"""
Teams bot runtime (Microsoft 365 Agents SDK), hosted inside the Flask/Waitress app.

The SDK is asyncio-based and Waitress is a sync WSGI server, so this owns one
long-lived event loop on a daemon thread. Flask routes hand coroutines to it
with submit(). The text-to-SQL pipeline itself is synchronous and slow (LLM +
DB), so handlers run it on a small thread pool rather than blocking the loop.
Pool threads have no running event loop, which the retrieval code relies on.
"""

import asyncio
import logging
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    ApplicationOptions,
    HttpAdapterBase,
    JwtTokenValidator,
    MemoryStorage,
    MessageFactory,
    TurnState,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

from .conversation_store import ConversationStore

logger = logging.getLogger(__name__)

_FOLLOWUP_TTL_SECONDS = 30 * 60


class TeamsAdapter(HttpAdapterBase):
    """Bot Framework channel adapter. Only the shared processing logic is
    used; the HTTP side is the Flask route in bridge.py."""


class TeamsBotRuntime:
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings

        self.auth_config = AgentAuthConfiguration(
            client_id=settings.app_id,
            tenant_id=settings.tenant_id,
            client_secret=settings.app_password,
            connection_name="SERVICE_CONNECTION",
        )
        self.connection_manager = MsalConnectionManager(
            connections_configurations={"SERVICE_CONNECTION": self.auth_config}
        )
        self.adapter = TeamsAdapter(connection_manager=self.connection_manager)
        self.adapter.on_turn_error = self._on_turn_error
        self.agent = AgentApplication[TurnState](
            ApplicationOptions(
                storage=MemoryStorage(),
                adapter=self.adapter,
                bot_app_id=settings.app_id,
                start_typing_timer=True,   # "typing…" while the pipeline runs
            ),
            connection_manager=self.connection_manager,
        )
        self.validator = JwtTokenValidator(self.auth_config)
        self.conversations = ConversationStore(settings.conversation_store_path)
        self.pool = ThreadPoolExecutor(max_workers=max(1, settings.max_workers), thread_name_prefix="teams-pipeline")

        self._states = {}                      # conversation id -> follow-up state
        self._states_lock = threading.Lock()
        self._seen_activity_ids = OrderedDict()
        self._seen_lock = threading.Lock()

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, name="teams-bot-loop", daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def submit(self, coro):
        """Schedule a coroutine on the bot loop; returns a concurrent Future."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _on_turn_error(self, context, error):
        logger.error(f"Teams turn failed: {error}", exc_info=error, extra={"admin": True})
        try:
            await context.send_activity(MessageFactory.text("Sorry — something went wrong answering that. Please try again."))
        except Exception:
            logger.exception("Teams: could not send the error reply")

    # ---- per-conversation state -----------------------------------------
    def conversation_state(self, conversation_id):
        """Mutable dict for one conversation: follow-up context (previous_sql,
        prior_question) that expires after 30 idle minutes, and an admin's
        chosen workspace (kept)."""
        now = time.time()
        with self._states_lock:
            state = self._states.setdefault(conversation_id, {})
            if now - state.get("_touched", now) > _FOLLOWUP_TTL_SECONDS:
                state.pop("previous_sql", None)
                state.pop("prior_question", None)
            state["_touched"] = now
            return state

    def is_duplicate(self, activity_id):
        """Teams retries a message it thinks timed out; answer each id once."""
        if not activity_id:
            return False
        with self._seen_lock:
            if activity_id in self._seen_activity_ids:
                return True
            self._seen_activity_ids[activity_id] = time.time()
            while len(self._seen_activity_ids) > 2000:
                self._seen_activity_ids.popitem(last=False)
        return False

    # ---- pipeline (runs on the worker pool) -------------------------------
    def run_in_pool(self, func, *args):
        return self._loop.run_in_executor(self.pool, func, *args)

    def with_workspace_instance(self, workspace_id, func, *args):
        """Run func(*args) with workspace_id's Vanna instance bound to this
        (pool) thread, so every `vn.` call inside the pipeline resolves to it."""
        instance, err = self.app.vanna_registry.get_or_build(workspace_id)
        if instance is None:
            raise RuntimeError(err or "Workspace is not configured")
        with self.app.vn_router.bound_to(instance):
            return func(*args)

    # ---- proactive delivery (called from scheduler threads) --------------
    def send_proactive(self, aad_object_id, activity_factory, timeout=30):
        """Message a user outside of a turn. Returns False if they've never
        messaged the bot (no stored conversation), True once sent."""
        reference = self.conversations.get(aad_object_id)
        if reference is None:
            return False

        async def _send():
            async def _callback(turn_context):
                await turn_context.send_activity(activity_factory())
            await self.adapter.continue_conversation(
                self.settings.app_id, reference.get_continuation_activity(), _callback
            )

        self.submit(_send()).result(timeout=timeout)
        return True

"""Teams bot turn handlers: identity, commands, audio attachments, card submits,
and the hand-off to the shared chat pipeline (app.run_chat_turn)."""

import logging

import requests
from microsoft_agents.activity import ActivityTypes

from ..voice import openai_audio
from . import cards
from .identity import IdentityError, build_chat_context, find_app_user

logger = logging.getLogger(__name__)

_FILE_DOWNLOAD_INFO = "application/vnd.microsoft.teams.file.download.info"
_BOTFRAMEWORK_SCOPE = "https://api.botframework.com/.default"


def register_handlers(runtime):
    agent = runtime.agent

    @agent.conversation_update("membersAdded")
    async def on_members_added(context, _state):
        activity = context.activity
        bot_id = activity.recipient.id if activity.recipient else None
        if any(m.id != bot_id for m in (activity.members_added or [])):
            runtime.conversations.save_from_activity(activity)
            await context.send_activity(cards.help_message(tab_available=runtime.settings.tab_enabled))

    @agent.activity(ActivityTypes.message)
    async def on_message(context, _state):
        await _handle_message(runtime, context)


async def _resolve_context(runtime, context, state):
    """ChatContext for the sender, or raises IdentityError with the reason."""
    activity = context.activity
    sender = activity.from_property
    aad_id = getattr(sender, "aad_object_id", None)

    # Teams activities carry the tenant in channel_data.tenant.id; conversation.tenant_id
    # is the general Bot Framework field and isn't always populated for personal chats.
    channel_data = activity.channel_data or {}
    teams_tenant_id = (channel_data.get("tenant") or {}).get("id") if isinstance(channel_data, dict) else None
    conversation_tenant_id = getattr(activity.conversation, "tenant_id", None)
    tenant = teams_tenant_id or conversation_tenant_id
    if runtime.settings.enforce_tenant and runtime.settings.tenant_id and tenant and tenant.lower() != runtime.settings.tenant_id.lower():
        logger.warning(
            f"Teams: rejected cross-tenant message. expected={runtime.settings.tenant_id} "
            f"channel_data.tenant.id={teams_tenant_id} conversation.tenant_id={conversation_tenant_id}",
            extra={"admin": True},
        )
        raise IdentityError("This bot only serves users of its own organization.")

    app = runtime.app
    user_id, meta = await runtime.run_in_pool(app.find_user_by_aad_id, aad_id)
    email = (meta or {}).get("email") or ""
    if not user_id:
        # Unknown Entra id: fetch the member's mailbox/UPN from Teams and match by email.
        member = None
        connector = context.turn_state.get("ConnectorClient")
        try:
            if connector is not None:
                member = await connector.get_conversation_member(activity.conversation.id, sender.id)
        except Exception as e:
            logger.warning(f"Teams: member lookup failed: {e}", extra={"admin": True})
        email = ((getattr(member, "email", None) or getattr(member, "user_principal_name", None) or "")).strip().lower()
        user_id, meta = await runtime.run_in_pool(find_app_user, app, aad_id, email)
        if not user_id:
            shown = email or "your Teams email"
            raise IdentityError(
                f"Hi {getattr(sender, 'name', None) or 'there'}! Your Teams account isn't registered in WAI yet. "
                f"Ask your WAI admin to add **{shown}** as the email on your WAI user."
            )

    return await runtime.run_in_pool(
        build_chat_context, app, user_id, meta, aad_id, email, state.get("workspace_id")
    )


def _find_audio_attachment(activity):
    for attachment in activity.attachments or []:
        content_type = (attachment.content_type or "").lower()
        if content_type == _FILE_DOWNLOAD_INFO and isinstance(attachment.content, dict):
            content = attachment.content
            ext = (content.get("fileType") or "").lower() or openai_audio.extension_for(filename=attachment.name)
            if ext in openai_audio.AUDIO_EXTENSIONS and content.get("downloadUrl"):
                return {"url": content["downloadUrl"], "filename": attachment.name or f"audio.{ext}", "mime": None, "needs_token": False}
        elif content_type.startswith("audio/") and attachment.content_url:
            return {"url": attachment.content_url, "filename": attachment.name, "mime": content_type, "needs_token": True}
    return None


def _download_audio(url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(chunk_size=256 * 1024):
            size += len(chunk)
            if size > openai_audio.MAX_AUDIO_BYTES:
                raise ValueError("The recording is larger than 25 MB.")
            chunks.append(chunk)
        return b"".join(chunks), response.headers.get("Content-Type")


async def _transcribe_attachment(runtime, audio):
    token = None
    if audio["needs_token"]:
        provider = runtime.connection_manager.get_default_connection()
        token = await provider.get_access_token("https://api.botframework.com", [_BOTFRAMEWORK_SCOPE])
    data, served_mime = await runtime.run_in_pool(_download_audio, audio["url"], token)
    return await runtime.run_in_pool(
        lambda: openai_audio.transcribe(data, mime_type=audio["mime"] or served_mime, filename=audio["filename"])
    )


async def _handle_card_action(runtime, context, ctx, value):
    action = value.get("wai_action")
    write_id = value.get("write_id")
    workspace_id = value.get("workspace_id") or ctx.workspace_id
    if action == "cancel_write":
        runtime.app.discard_pending_write(write_id)
        await context.send_activity(cards.text_message("Write cancelled — nothing was changed."))
        return
    if action == "confirm_write":
        if not ctx.is_admin:
            await context.send_activity(cards.text_message("Only an admin can confirm data changes."))
            return
        body, _status = await runtime.run_in_pool(
            runtime.with_workspace_instance, workspace_id,
            runtime.app._execute_pending_write, workspace_id, write_id, ctx.user_id,
        )
        if body.get("type") == "success":
            text = f"✅ Write executed — {body.get('rows_affected', 0)} row(s) affected."
        else:
            text = f"❌ Write failed: {body.get('error') or 'unknown error'}"
        await context.send_activity(cards.text_message(text))


async def _handle_message(runtime, context):
    activity = context.activity
    if runtime.is_duplicate(activity.id):
        return
    runtime.conversations.save_from_activity(activity)
    state = runtime.conversation_state(activity.conversation.id)

    try:
        ctx = await _resolve_context(runtime, context, state)
    except IdentityError as e:
        await context.send_activity(cards.text_message(str(e)))
        return

    if isinstance(activity.value, dict) and activity.value.get("wai_action"):
        await _handle_card_action(runtime, context, ctx, activity.value)
        return

    text = (activity.text or "").strip()
    audio = None if text else _find_audio_attachment(activity)
    if audio:
        try:
            text = await _transcribe_attachment(runtime, audio)
        except ValueError as e:
            await context.send_activity(cards.text_message(f"I couldn't use that recording: {e}"))
            return
        except Exception as e:
            logger.error(f"Teams: audio transcription failed: {e}", exc_info=True, extra={"admin": True})
            await context.send_activity(cards.text_message("Sorry — I couldn't transcribe that recording."))
            return
        if not text:
            await context.send_activity(cards.text_message("I couldn't hear any speech in that recording."))
            return
        await context.send_activity(cards.text_message(f"🎤 Heard: “{text}”"))

    if not text:
        await context.send_activity(cards.help_message(tab_available=runtime.settings.tab_enabled))
        return

    command = text.lower().strip()
    if command in ("help", "/help", "?"):
        await context.send_activity(cards.help_message(tab_available=runtime.settings.tab_enabled))
        return
    if command in ("reset", "/reset", "new", "new question"):
        state.pop("previous_sql", None)
        state.pop("prior_question", None)
        await context.send_activity(cards.text_message("Started fresh — your next question won't build on the previous one."))
        return
    if command.startswith("workspace") and ctx.is_admin:
        await _switch_workspace(runtime, context, state, text[len("workspace"):].strip())
        return

    try:
        result = await runtime.run_in_pool(
            runtime.with_workspace_instance, ctx.workspace_id, runtime.app.run_chat_turn, ctx, text, state
        )
    except Exception as e:
        logger.error(f"Teams: chat turn failed: {e}", exc_info=True, extra={"admin": True})
        await context.send_activity(cards.text_message(f"Sorry — I couldn't answer that: {e}"))
        return

    kind = result.get("kind")
    if kind == "answer":
        await context.send_activity(cards.answer_message(result))
    elif kind == "write_confirmation":
        await context.send_activity(cards.write_confirmation_message(result, ctx.workspace_id))
    else:
        await context.send_activity(cards.text_message(result.get("text") or "I don't have an answer for that."))


async def _switch_workspace(runtime, context, state, name):
    from .identity import teams_enabled_workspaces
    enabled = await runtime.run_in_pool(teams_enabled_workspaces, runtime.app)
    if not name:
        names = ", ".join((m.get("display_name") or m.get("name") or wid) for wid, m in enabled) or "(none)"
        await context.send_activity(cards.text_message(f"Teams-enabled workspaces: {names}. Say `workspace <name>` to switch."))
        return
    match = next(((wid, m) for wid, m in enabled
                  if name.lower() in (str(m.get("name", "")).lower(), str(m.get("display_name", "")).lower(), wid.lower())), None)
    if not match:
        await context.send_activity(cards.text_message(f"No Teams-enabled workspace called “{name}”."))
        return
    state["workspace_id"] = match[0]
    state.pop("previous_sql", None)
    state.pop("prior_question", None)
    await context.send_activity(cards.text_message(f"Switched to workspace **{match[1].get('display_name') or match[1].get('name')}**."))

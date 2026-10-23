import json
import logging
import os
import threading

from microsoft_agents.activity import Activity, ConversationReference

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Remembers each Teams user's 1:1 conversation with the bot, keyed by their
    Entra object id, so the bot can message them later without being asked
    first (a scheduled agent's results, a condition alert). Persisted to a JSON
    file so these survive a server restart. Teams only lets a bot message a user
    who has installed it, and this is what records that they have.
    """

    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()
        self._references = self._load()

    def _load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Teams conversation store unreadable ({self._path}): {e}", extra={"admin": True})
            return {}

    def _write(self):
        directory = os.path.dirname(self._path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = self._path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._references, f, indent=2)
        os.replace(tmp_path, self._path)

    def save_from_activity(self, activity: Activity):
        """Record/refresh the sender's conversation. Only 1:1 (personal) chats are
        kept: proactive results go to the user privately, never into a group."""
        sender = activity.from_property
        aad_id = getattr(sender, "aad_object_id", None) if sender else None
        conversation = activity.conversation
        if not aad_id or not conversation or getattr(conversation, "conversation_type", None) not in (None, "personal"):
            return
        reference = activity.get_conversation_reference()
        serialized = reference.model_dump(mode="json", by_alias=True, exclude_none=True)
        with self._lock:
            if self._references.get(aad_id) == serialized:
                return
            self._references[aad_id] = serialized
            try:
                self._write()
            except Exception as e:
                logger.error(f"Failed to persist Teams conversation reference: {e}", extra={"admin": True})

    def get(self, aad_id):
        with self._lock:
            data = self._references.get(aad_id)
        return ConversationReference.model_validate(data) if data else None

    def has(self, aad_id):
        with self._lock:
            return aad_id in self._references

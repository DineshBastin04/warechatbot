"""
Speech-to-text and text-to-speech through OpenAI, shared by the Teams bot
(audio file attachments) and the web/Teams-tab chat (mic + spoken replies).

Models are configurable via env:
  OPENAI_STT_MODEL  (default gpt-4o-mini-transcribe; whisper-1 also works)
  OPENAI_TTS_MODEL  (default gpt-4o-mini-tts; tts-1 also works)
  OPENAI_TTS_VOICE  (default alloy)
"""

import logging
import os
import threading
from collections import OrderedDict

from openai import OpenAI

logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 25 * 1024 * 1024       # OpenAI transcription upload limit
MAX_TTS_CHARS = 4096                      # OpenAI speech input limit

# Container/extension OpenAI infers the format from — the upload filename must
# carry the right extension for the bytes it contains.
_MIME_TO_EXT = {
    "audio/webm": "webm", "video/webm": "webm",
    "audio/ogg": "ogg", "audio/opus": "ogg",
    "audio/mp4": "mp4", "audio/m4a": "m4a", "audio/x-m4a": "m4a", "audio/aac": "m4a",
    "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/mpga": "mp3",
    "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav",
    "audio/flac": "flac", "video/mp4": "mp4",
}
AUDIO_EXTENSIONS = {"webm", "ogg", "mp4", "m4a", "mp3", "mpeg", "mpga", "wav", "flac", "aac"}

# Warehouse vocabulary nudges transcription toward domain terms ("LPN", "putaway"...).
_DOMAIN_PROMPT = (
    "Warehouse management questions about orders, order numbers, items, SKUs, item numbers, "
    "inventory, stock, locations, bins, license plates, LPN, handling units, picking, putaway, "
    "waves, replenishment, cycle counts, ASN, purchase orders, receipts, shipments, carriers, "
    "loads, docks, staging, work queue, employees, devices. Scheduling: every Monday, daily, "
    "email this report to my manager, notify me when."
)

_client_lock = threading.Lock()
_client = None


def _openai_client(api_key=None):
    global _client
    if api_key:
        return OpenAI(api_key=api_key)
    with _client_lock:
        if _client is None:
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set — speech features need an OpenAI key.")
            _client = OpenAI(api_key=key)
        return _client


def extension_for(mime_type=None, filename=None):
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in AUDIO_EXTENSIONS:
            return "m4a" if ext == "aac" else ext
    base_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    return _MIME_TO_EXT.get(base_mime)


def _language_code(language):
    """"en-US" -> "en"; OpenAI expects ISO-639-1."""
    if not language:
        return None
    code = language.split("-", 1)[0].strip().lower()
    return code if len(code) == 2 else None


def transcribe(audio_bytes, mime_type=None, filename=None, language=None, api_key=None):
    """Transcribe an audio clip. Returns the text ("" if nothing was said).
    Raises ValueError for unusable input."""
    if not audio_bytes:
        raise ValueError("The recording is empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError("The recording is larger than 25 MB.")
    ext = extension_for(mime_type, filename)
    if not ext:
        raise ValueError(f"Unsupported audio format ({mime_type or filename or 'unknown'}).")

    params = {
        "model": os.environ.get("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe"),
        "file": (f"speech.{ext}", audio_bytes),
        "prompt": _DOMAIN_PROMPT,
    }
    lang = _language_code(language)
    if lang:
        params["language"] = lang
    result = _openai_client(api_key).audio.transcriptions.create(**params)
    return (getattr(result, "text", "") or "").strip()


_tts_cache = OrderedDict()
_tts_cache_lock = threading.Lock()
_TTS_CACHE_SIZE = 64


def speak(text, voice=None, api_key=None):
    """Synthesize speech. Returns MP3 bytes. Identical requests are served from
    a small in-memory cache (repeated help text, re-played answers)."""
    text = (text or "").strip()[:MAX_TTS_CHARS]
    if not text:
        raise ValueError("Nothing to say.")
    model = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = voice or os.environ.get("OPENAI_TTS_VOICE", "alloy")
    key = (model, voice, text)
    with _tts_cache_lock:
        if key in _tts_cache:
            _tts_cache.move_to_end(key)
            return _tts_cache[key]

    params = {"model": model, "voice": voice, "input": text, "response_format": "mp3"}
    if model.startswith("gpt-4o"):
        # `instructions` isn't a named parameter in the pinned openai SDK yet.
        params["extra_body"] = {"instructions": "Speak clearly and naturally, like a helpful warehouse operations assistant."}
    audio = _openai_client(api_key).audio.speech.create(**params).read()

    with _tts_cache_lock:
        _tts_cache[key] = audio
        while len(_tts_cache) > _TTS_CACHE_SIZE:
            _tts_cache.popitem(last=False)
    return audio

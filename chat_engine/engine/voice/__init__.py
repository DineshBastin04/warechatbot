"""
Voice routes for the chat UI (web and Teams tab):

  POST /api/v0/transcribe  multipart "audio" (+ optional "language") -> {"text"}
  POST /api/v0/speak       JSON {"text"}                             -> audio/mpeg

Both require a logged-in session (enforced by the access guard). The browser's
built-in speech recognition doesn't work inside Teams (WebView2), so the chat
UI records audio and sends it here instead.
"""

import logging

from flask import Response, jsonify, request, session

from . import openai_audio

logger = logging.getLogger(__name__)


def register_voice_routes(app):
    flask_app = app.flask_app

    @flask_app.route("/api/v0/transcribe", methods=["POST"])
    def transcribe_audio():
        logger.info(
            f"/api/v0/transcribe: request received, content_length={request.content_length}, "
            f"session_user={session.get('username')}",
            extra={"admin": True},
        )
        if (request.content_length or 0) > openai_audio.MAX_AUDIO_BYTES + 1024 * 1024:
            return jsonify({"type": "error", "error": "The recording is larger than 25 MB."}), 413
        upload = request.files.get("audio")
        if upload is None:
            logger.warning("/api/v0/transcribe: no 'audio' file part in the request", extra={"admin": True})
            return jsonify({"type": "error", "error": "No audio uploaded"}), 400
        data = upload.read()
        logger.info(
            f"/api/v0/transcribe: audio bytes={len(data)}, mimetype={upload.mimetype}, filename={upload.filename}",
            extra={"admin": True},
        )
        try:
            text = openai_audio.transcribe(
                data,
                mime_type=upload.mimetype,
                filename=upload.filename,
                language=request.form.get("language"),
            )
        except ValueError as e:
            logger.warning(f"/api/v0/transcribe: rejected ({e})", extra={"admin": True})
            return jsonify({"type": "error", "error": str(e)}), 400
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True, extra={"admin": True})
            return jsonify({"type": "error", "error": "Transcription failed"}), 502
        logger.info(f"/api/v0/transcribe: transcript={text!r}", extra={"admin": True})
        return jsonify({"type": "transcript", "text": text})

    @flask_app.route("/api/v0/speak", methods=["POST"])
    def speak_text():
        text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
        if not text:
            return jsonify({"type": "error", "error": "No text provided"}), 400
        try:
            audio = openai_audio.speak(text)
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}", exc_info=True, extra={"admin": True})
            return jsonify({"type": "error", "error": "Speech synthesis failed"}), 502
        return Response(audio, mimetype="audio/mpeg", headers={"Cache-Control": "private, max-age=300"})

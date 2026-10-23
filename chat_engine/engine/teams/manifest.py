"""
Builds the Teams app package (manifest.json + two icons, zipped) from the
server's settings. An admin downloads it from the Teams Configuration page and
gives it to whoever uploads custom apps in the organization's Teams admin center.
"""

import io
import json
import os
import zipfile

MANIFEST_SCHEMA_VERSION = "1.25"
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest")


def build_manifest(settings, version="1.0.0"):
    host = settings.public_host
    return {
        "$schema": f"https://developer.microsoft.com/json-schemas/teams/v{MANIFEST_SCHEMA_VERSION}/MicrosoftTeams.schema.json",
        "manifestVersion": MANIFEST_SCHEMA_VERSION,
        "version": version,
        "id": settings.teams_app_id,
        "developer": {
            "name": "Tychons",
            "websiteUrl": "https://tychons.com",
            "privacyUrl": "https://tychons.com",
            "termsOfUseUrl": "https://tychons.com",
        },
        "name": {"short": "WAI", "full": "Warehouse Intelligence (WAI)"},
        "description": {
            "short": "Ask your warehouse data questions — by text or voice.",
            "full": (
                "WAI answers questions about your warehouse data in plain language, schedules "
                "reports and alerts by chat or email, and supports voice questions and spoken "
                "answers in its tab."
            ),
        },
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#4F46E5",
        "bots": [{
            "botId": settings.app_id,
            "scopes": ["personal"],
            "supportsFiles": True,          # lets users attach audio recordings
            "isNotificationOnly": False,
            "commandLists": [{
                "scopes": ["personal"],
                "commands": [
                    {"title": "help", "description": "What I can do"},
                    {"title": "/list", "description": "Your scheduled reports and alerts"},
                    {"title": "/email list", "description": "Registered email recipients"},
                    {"title": "reset", "description": "Start a new question (drop follow-up context)"},
                ],
            }],
        }],
        "staticTabs": [
            {
                "entityId": "wai-chat",
                "name": "Ask WAI",
                "contentUrl": f"https://{host}/teams/tab",
                "websiteUrl": f"https://{host}/",
                "scopes": ["personal"],
            },
            {"entityId": "conversations", "scopes": ["personal"]},
        ],
        "permissions": ["identity", "messageTeamMembers"],
        "devicePermissions": ["media"],     # microphone for voice questions in the tab
        "validDomains": [host],
        "webApplicationInfo": {"id": settings.app_id, "resource": settings.sso_resource},
    }


def build_package(settings):
    """Returns the app package as zip bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("manifest.json", json.dumps(build_manifest(settings), indent=2))
        for icon in ("color.png", "outline.png"):
            package.write(os.path.join(_ICON_DIR, icon), icon)
    return buffer.getvalue()

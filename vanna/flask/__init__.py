import json
import logging
import asyncio
import os
import re
import sqlparse
import sys
import uuid
import time
import base64
from threading import Thread
from typing import Dict, Any, Optional, List
from functools import wraps
from uuid import UUID,uuid4
from abc import ABC, abstractmethod
from functools import wraps
import importlib.metadata
from urllib.parse import urlparse
import subprocess
import copy
import io
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
from dateutil.relativedelta import relativedelta
from collections import deque as _deque
import openai
from openai import OpenAI
from openai import OpenAIError
# HTTP/Network
import aiohttp
import requests
from botframework.connector.aio import ConnectorClient

# Data Handling and Scientific Libraries
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
import pyodbc
import pyarrow as pa
import pyarrow.parquet as pq
import pdfplumber

# Database/Vector Store
import chromadb
import sqlparse


#translate
from deep_translator import GoogleTranslator
from langdetect import detect
import re

import os
from dotenv import load_dotenv



# Flask/Web Frameworks
import flask
from flask import (
    Flask, request, jsonify, redirect, url_for, session, make_response, 
    Response, send_from_directory, render_template, render_template_string,
    has_request_context
)
from flasgger import Swagger
from flask import Flask, Response, jsonify, request, send_from_directory, render_template
from flask import render_template_string
from flask_sock import Sock

# Azure/Bot Framework
from botbuilder.core import (
    BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext,
    BotFrameworkAdapter
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import (
    Activity, ConversationReference, ChannelAccount, ConversationAccount,
    ActivityTypes, Attachment, ErrorResponseException
)
from botframework.connector import ConnectorClient as SyncConnectorClient  # Renamed to avoid conflict
from botframework.connector.auth import (
    MicrosoftAppCredentials, JwtTokenValidation, AuthenticationConfiguration, 
    SimpleCredentialProvider, AuthenticationConstants
)
from azure.core.exceptions import DeserializationError

# Custom/Project-Specific (Based on your listed imports)
from ..base import VannaBase
from ..ollama import Ollama
from ..openai import OpenAI_Chat
from ..chromadb import ChromaDB_VectorStore
from .assets import css_content, html_content, js_content
from .auth import AuthInterface, NoAuth, BasicAuth
from .config import index_template
from .prediction_page import prediction_template
from .anomaly_page import anomaly_template

import io, uuid, logging
from typing import Dict, Any, Optional
import pyodbc
import pandas as pd
from io import BytesIO
import pickle

# from flask import session, has_request_context
from io import BytesIO
import gzip
try:
    import brotli  # optional; fallback to gzip if absent
    _HAS_BROTLI = True
except Exception:
    brotli = None
    _HAS_BROTLI = False
import pickle
import pandas as pd
import time
import threading 
# Bot Framework Imports
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity
#from .bot import TeamsBot
from azure.core.exceptions import DeserializationError
import asyncio


from threading import Thread
from flask import request, jsonify, make_response
from botbuilder.schema import Activity

from botbuilder.core import TurnContext, BotFrameworkAdapter
from botbuilder.schema import ConversationReference
from botframework.connector import ConnectorClient
from botframework.connector.auth import MicrosoftAppCredentials
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import ActivityTypes
from botbuilder.core import TurnContext
from urllib.parse import urlparse
from azure.core.exceptions import DeserializationError



import pyodbc
import csv
import io
import smtplib
from email.message import EmailMessage
from datetime import datetime
import schedule
from email.message import EmailMessage
from dotenv import load_dotenv, set_key
import os
from sqlalchemy import create_engine, text, event as sa_event


#smtp email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import csv
import io
import atexit, json, csv, io, smtplib, traceback
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime as _dt

from chromadb.utils import embedding_functions #sop bot
from asgiref.sync import async_to_sync


ALERT_COOLDOWN_SECONDS = 3600          # 1 h deduplication
stockout_cron_scheduler = None         # global scheduler object
alert_history = {}                     # {workspace: {scenario: last_sent_ts}}

# Automated device reset job — in-memory log buffer (last 500 entries)
_stuck_device_log = _deque(maxlen=500)
_stuck_device_log_lock = None          # initialised after Lock is imported below
_current_stuck_run_id = None

# Unpick Agent — in-memory log buffer (last 1000 entries)
_unpick_log = _deque(maxlen=1000)
_unpick_log_lock = None                # initialised after Lock is imported below
_current_unpick_run_id = None

# Scheduler objects — set to module-level globals so control routes can pause/resume/reschedule
_stuck_device_scheduler = None
_auto_unpick_scheduler = None

# Chat-driven writes — server-side cache of generated-but-not-yet-executed write SQL,
# keyed by a one-time write_id. execute_write_sql looks the SQL up here rather than
# trusting a SQL string echoed back by the client, since writes are higher stakes
# than the existing read flow's client-echoed-SQL pattern.
_pending_writes = {}
_pending_writes_lock = None            # initialised after Lock is imported below





# ENV_PATH = ".env"
# load_dotenv(ENV_PATH)
import os
import json
from threading import Lock

CONFIG_FILE = "feedback_config.json"
_config_lock = Lock()
_stuck_device_log_lock = Lock()
_unpick_log_lock = Lock()
_pending_writes_lock = Lock()


# DEPRECATED: This is replaced by the updated load_email_config below
# def load_email_config():
#     with _config_lock:
#         if not os.path.exists(CONFIG_FILE):
#             return {}
#
#         try:
#             with open(CONFIG_FILE, "r") as f:
#                 cfg = json.load(f)
#         except json.JSONDecodeError:
#             raise RuntimeError("feedback_config.json is corrupted")
#
#         provider = cfg.get("email_provider")
#
#         if provider not in ("gmail", "outlook", None):
#             raise RuntimeError("Invalid or missing email_provider")
#
#         if provider == "gmail" and "gmail" not in cfg:
#             raise RuntimeError("Gmail provider selected but gmail config missing")
#
#         if provider == "outlook" and "outlook" not in cfg:
#             raise RuntimeError("Outlook provider selected but outlook config missing")
#
#         # Set default SMTP settings if not present
#         if provider == "outlook":
#             if "smtp_server" not in cfg:
#                 cfg["smtp_server"] = "smtp.office365.com"
#             if "smtp_port" not in cfg:
#                 cfg["smtp_port"] = 587
#
#         return cfg


def save_email_config(data):
    with _config_lock:
        tmp_file = CONFIG_FILE + ".tmp"

        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=4)

        os.replace(tmp_file, CONFIG_FILE)








logger = logging.getLogger(__name__)


def _log_stuck(level: str, message: str, device_id: str = None):
    """Append a structured entry to the automated device reset log buffer and echo to the system logger."""
    entry = {
        "run_id":    _current_stuck_run_id or "Unknown",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "level":     level,
        "device_id": device_id or "",
        "message":   message,
    }
    with _stuck_device_log_lock:
        _stuck_device_log.append(entry)
    if level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    else:
        logger.info(message)


def _log_unpick(level: str, message: str, order_number: str = None, item_number: str = None, wh_id: str = None, run_id: str = None):
    """Append a structured entry to the unpick agent log buffer and echo to the system logger."""
    global _current_unpick_run_id
    entry = {
        "run_id":       run_id or _current_unpick_run_id or "Unknown",
        "timestamp":    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "level":        level,
        "wh_id":        wh_id or "",
        "order_number": order_number or "",
        "item_number":  item_number or "",
        "message":      message,
    }
    with _unpick_log_lock:
        _unpick_log.append(entry)
    if level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    else:
        logger.info(message)

 # Add this configuration at the top of the file after imports
USER_MANAGEMENT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('FEEDBACK_DB_SERVER', '192.168.1.74,7274')};"
    f"DATABASE={os.getenv('FEEDBACK_DB_NAME', 'tychons_wi')};"
    f"UID={os.getenv('FEEDBACK_DB_USER', 'user')};"
    f"PWD={os.getenv('FEEDBACK_DB_PASSWORD', '')};"
    "Trusted_Connection=yes;"
)




USER_FEEDBACK_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('FEEDBACK_DB_SERVER', '192.168.1.74,7274')};"
    f"DATABASE={os.getenv('FEEDBACK_DB_NAME', 'tychons_wi')};"
    f"UID={os.getenv('FEEDBACK_DB_USER', 'user')};"
    f"PWD={os.getenv('FEEDBACK_DB_PASSWORD', '')};"
)


# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587


TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")




#email smtp settings

# SMTP_USER = os.getenv("SMTP_USER")      # e.g. warehouse.alerts@gmail.com
# SMTP_PASS = os.getenv("SMTP_PASS")      # app password
# SMTP_FROM = os.getenv("SMTP_FROM")      # same as SMTP_USER






 
# MICROSOFT_APP_ID = "<redacted>"  # Replace with your Microsoft App ID
# MICROSOFT_APP_PASSWORD = "<redacted>"  # Replace with your Microsoft App Password

MICROSOFT_APP_ID = os.getenv("MICROSOFT_APP_ID", "")
MICROSOFT_APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")

MICROSOFT_APP_TENANT_ID = os.getenv("MICROSOFT_APP_TENANT_ID", "")  # from logs


# Initialize Bot Framework Adapter
adapter_settings = BotFrameworkAdapterSettings(
    app_id=MICROSOFT_APP_ID,
    app_password=MICROSOFT_APP_PASSWORD,
    channel_auth_tenant=MICROSOFT_APP_TENANT_ID
)


adapter = BotFrameworkAdapter(adapter_settings)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"[on_turn_error]: {error}", exc_info=True)
    await context.send_activity("Sorry, something went wrong. Please try again.")

adapter.on_turn_error = on_error

# Global conversation references
conversation_references = {}
 
# OpenAI.api_key = "<redacted>"  # use OPENAI_API_KEY from .env instead
# # Step 1: Define your app credentials
# APP_ID = ""  
# APP_PASSWORD = ""  

# # Step 2: Create BotFrameworkAdapterSettings
# settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)

# # Step 3: Initialize the BotFrameworkAdapter
# adapter = BotFrameworkAdapter(settings)

# # ---- Bot Framework Setup ----
# # adapter_settings = BotFrameworkAdapterSettings("<redacted>", "<redacted>")




# INCOMING_WEBHOOK_URL=""




# adapter_settings = BotFrameworkAdapterSettings(app_id="<redacted>", app_password="<redacted>")



#adapter_settings = BotFrameworkAdapterSettings(app_id="<redacted>", app_password="<redacted>")
# adapter = BotFrameworkAdapter(adapter_settings)




#adapter_settings = BotFrameworkAdapterSettings(app_id="", app_password="")
#adapter = BotFrameworkAdapter(adapter_settings)


# adapter_settings = BotFrameworkAdapterSettings(app_id="", app_password="")
# adapter = BotFrameworkAdapter(adapter_settings)


# Dictionary to store conversation references
#conversation_references = {}



# # # Dictionary to track the last question asked by each user
# user_last_questions = {}
#incoming for testing for demo
# INCOMING_WEBHOOK_URL="https://tychonsolution.webhook.office.com/webhookb2/7b239272-a2c9-487f-8bfb-b9e9dd38ac2c@df39b915-b72f-429a-8164-4983c27bb320/IncomingWebhook/668b3bdc1f854ae58e628323bb661328/2252290e-4347-4e52-8966-7c8fb757ae90/V2kc6V8bpI0uTeFztJDLvUkzVcM4jiq5gd32j7TDE8Wu41"


#incoming webhook for actual demo
INCOMING_WEBHOOK_URL="https://tychonsolution.webhook.office.com/webhookb2/7b239272-a2c9-487f-8bfb-b9e9dd38ac2c@df39b915-b72f-429a-8164-4983c27bb320/IncomingWebhook/3359896e687a4439bb16318969ba78c1/2252290e-4347-4e52-8966-7c8fb757ae90/V2k6PJOa5-c4Ja9-faqcuNfqh6n9Xn_0ZamAKjDyR525w1"
vn = None


#translation #########################################

# def translate(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
#     """
#     Universal translation helper.
#     Uses Google Translate and supports any language it supports.
    
#     Args:
#         text: Input text
#         source_lang: Source language code or 'auto'
#         target_lang: Target language code
        
#     Returns:
#         Translated text, or original text on error.
#     """
#     if not text or target_lang is None:
#         return text

#     # If translation target is same as source (and not auto), return original.
#     if source_lang != "auto" and source_lang == target_lang:
#         return text

#     try:
#         return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
#     except Exception as e:
#         logger.error(f"Translation Error ({source_lang} -> {target_lang}): {str(e)}")
#         return text


# def translate_question_if_needed(question: str) -> dict:
#     """
#     Detects language and translates to English if the text is not English.
#     Works for ANY language supported by Google Translate.
    
#     Returns:
#         {
#             "original": original_question,
#             "translated": english_question,
#             "language": detected_language_code,
#             "was_translated": bool
#         }
#     """
#     if not question:
#         return {
#             "original": question,
#             "translated": question,
#             "language": "unknown",
#             "was_translated": False
#         }

#     try:
#         # Detect language of the incoming question
#         try:
#             detected_lang = detect(question)
#         except LangDetectException:
#             detected_lang = "unknown"

#         # If already English, no translation needed
#         if detected_lang == "en":
#             return {
#                 "original": question,
#                 "translated": question,
#                 "language": detected_lang,
#                 "was_translated": False
#             }

#         # Use Google Translate's auto-detect to be as generic as possible
#         translated_text = translate(text=question, source_lang="auto", target_lang="en")

#         # If translation didn't change anything, treat as "not translated"
#         was_translated = translated_text != question

#         return {
#             "original": question,
#             "translated": translated_text,
#             "language": detected_lang,
#             "was_translated": was_translated
#         }

#     except Exception as e:
#         logger.error(f"Translation error in translate_question_if_needed: {str(e)}")
#         return {
#             "original": question,
#             "translated": question,
#             "language": "unknown",
#             "was_translated": False
#         }


def translate_text(response: str, user_language: str) -> str:
    """
    Translates an English bot response back to the user's language.
    If user language is English or unknown, returns the original response.
    
    Args:
        response: English text (or base language text)
        user_language: Target language code like 'es', 'fr', 'de', 'hi', etc.
    """
    if not response:
        return response

    if user_language in (None, "", "unknown", "en"):
        return response

    return translate(text=response, source_lang="en", target_lang=user_language)


def translate_v2_api_key(text: str, target_lang: str = "en", source_lang: str = None) -> dict:
    """
    Google Translate Basic v2 using API key (REST).

    If source_lang is None => auto detect.

    Returns:
    {
      "translated_text": "...",
      "detected_language": "...",
      "was_translated": bool
    }
    """
    if not text or not target_lang:
        return {
            "translated_text": text,
            "detected_language": "unknown",
            "was_translated": False
        }

    if not TRANSLATE_API_KEY:
        raise ValueError("Missing GOOGLE_TRANSLATE_API_KEY in environment/.env")

    url = "https://translation.googleapis.com/language/translate/v2"
    params = {"key": TRANSLATE_API_KEY}
    data = {
        "q": text,
        "target": target_lang,
        "format": "text"
    }

    # If you pass source_lang, it uses it. If not, auto-detects.
    if source_lang and source_lang != "auto":
        data["source"] = source_lang

    try:
        r = requests.post(url, params=params, json=data, timeout=10)
        r.raise_for_status()
        result = r.json()

        translated = result["data"]["translations"][0]["translatedText"]
        detected = result["data"]["translations"][0].get("detectedSourceLanguage", "unknown")

        return {
            "translated_text": translated,
            "detected_language": detected,
            "was_translated": translated != text
        }

    except Exception as e:
        logger.error(f"Translate v2 API error: {str(e)}")
        return {
            "translated_text": text,
            "detected_language": "unknown",
            "was_translated": False
        }
    
def translate(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    res = translate_v2_api_key(
        text=text,
        source_lang=None if source_lang == "auto" else source_lang,
        target_lang=target_lang
    )
    return res["translated_text"]

def translate_question_if_needed(question: str) -> dict:
    if not question:
        return {
            "original": question,
            "translated": question,
            "language": "unknown",
            "was_translated": False
        }

    try:
        # Auto detect + translate to English
        res = translate_v2_api_key(text=question, target_lang="en", source_lang=None)

        detected_lang = res["detected_language"]
        translated_text = res["translated_text"]
        was_translated = (detected_lang != "en") and (translated_text != question)

        return {
            "original": question,
            "translated": translated_text,
            "language": detected_lang,
            "was_translated": was_translated
        }

    except Exception as e:
        logger.error(f"translate_question_if_needed error: {str(e)}")
        return {
            "original": question,
            "translated": question,
            "language": "unknown",
            "was_translated": False
        }




def clean_question(q: str) -> str:
        # remove tabs, multiple spaces, weird unicode spaces
        q = q.replace("\t", " ")
        q = q.replace("\n", " ")
        q = re.sub(r"\s+", " ", q)  # replace multiple spaces with single
        return q.strip()
###########################################################################################

class Cache(ABC):
    """
    Define the interface for a cache that can be used to store data in a Flask app.
    """

    @abstractmethod
    def generate_id(self, *args, **kwargs):
        """
        Generate a unique ID for the cache.
        """
        pass

    @abstractmethod
    def get(self, id, field):
        """
        Get a value from the cache.
        """
        pass

    @abstractmethod
    def get_all(self, field_list) -> list:
        """
        Get all values from the cache.
        """
        pass

    @abstractmethod
    def set(self, id, field, value):
        """
        Set a value in the cache.
        """
        pass

    @abstractmethod
    def delete(self, id):
        """
        Delete a value from the cache.
        """
        pass

#cron enabled Caching
class MemoryCache(Cache):
    def __init__(self):
        # now: { user_id: { workspace_id: { question_id: {...} } } }
        # legacy support: self.user_caches[user_id] might still be { question_id: {...} }
        self.user_caches: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # last_ids: { user_id: { workspace_id: last_id } }
        self.last_ids: Dict[str, Dict[str, Optional[str]]] = {}
        self.user_mgmt_config = {
            'server': os.environ.get('USER_MGMT_SERVER', '192.168.1.74'),
            'port': os.environ.get('USER_MGMT_PORT', '7274'),
            'database': os.environ.get('USER_MGMT_DATABASE', 'tychons_wi'),
            'username': os.environ.get('USER_MGMT_USERNAME', 'user'),
            'password': os.environ.get('USER_MGMT_PASSWORD', os.environ.get('FEEDBACK_DB_PASSWORD', ''))
        }
        
        import threading
        from collections import defaultdict

        # Lower-level helpers for concurrency
        self._inflight_ops = set()
        self._inflight_lock = threading.Lock()
        self._id_locks = defaultdict(threading.Lock)
        
        # Global lock for workspace operations
        if not hasattr(self, "_global_lock"):
            self._global_lock = threading.Lock()

        # NEW: Time-based eviction settings
        # TTL (time-to-live) in seconds for heavy objects (df, fig_json, summary)
        # Default: 10 minutes = 600 seconds
        self.heavy_cache_ttl_seconds = int(os.environ.get('CACHE_TTL_SECONDS', 600))
        
        # Track last access times for each question_id
        # Structure: { user_id: { workspace_id: { question_id: timestamp } } }
        self.last_access_times: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.last_access_lock = threading.Lock()
        
        # Background thread for cache eviction
        self._eviction_thread = None
        self._eviction_stop_event = threading.Event()
        self._start_eviction_thread()


    def _start_eviction_thread(self):
        """Start background thread for time-based cache eviction."""
        if self._eviction_thread is None or not self._eviction_thread.is_alive():
            self._eviction_stop_event.clear()
            self._eviction_thread = threading.Thread(
                target=self._eviction_worker,
                daemon=True,
                name="CacheEvictionWorker"
            )
            self._eviction_thread.start()
            logger.info("Cache eviction thread started with TTL=%d seconds", self.heavy_cache_ttl_seconds, extra={"cache": True})


    def _eviction_worker(self):
        """Background worker that periodically evicts stale heavy objects from cache."""
        # Run every minute to check for expired entries
        check_interval = 60  # seconds
        
        while not self._eviction_stop_event.is_set():
            try:
                self._evict_stale_entries()
            except Exception as e:
                logger.exception("Error in eviction worker: %s", e, extra={"cache": True})
            
            # Sleep with ability to be interrupted
            self._eviction_stop_event.wait(check_interval)


    def _evict_stale_entries(self):
        """Evict heavy objects (df, fig_json, summary) that haven't been accessed within TTL."""
        import time
        current_time = time.time()
        ttl = self.heavy_cache_ttl_seconds
        
        evicted_count = 0
        
        with self.last_access_lock:
            # Iterate through all users and workspaces
            for uid in list(self.user_caches.keys()):
                for wid in list(self.user_caches.get(uid, {}).keys()):
                    workspace_map = self.user_caches.get(uid, {}).get(wid, {})
                    access_times = self.last_access_times.get(uid, {}).get(wid, {})
                    
                    for qid, entry in list(workspace_map.items()):
                        if not isinstance(entry, dict):
                            continue
                        
                        last_access = access_times.get(qid, 0)
                        time_since_access = current_time - last_access
                        
                        # If not accessed within TTL, evict heavy objects
                        if time_since_access > ttl:
                            cleared_fields = []
                            
                            if "df" in entry:
                                try:
                                    del entry["df"]
                                    cleared_fields.append("df")
                                except Exception:
                                    pass
                            
                            if "fig_json" in entry:
                                try:
                                    del entry["fig_json"]
                                    cleared_fields.append("fig_json")
                                except Exception:
                                    pass
                            
                            if "summary" in entry:
                                try:
                                    del entry["summary"]
                                    cleared_fields.append("summary")
                                except Exception:
                                    pass
                            # additional eviction of "plotly_code"
                            if "plotly_code" in entry:
                                try:
                                    del entry["plotly_code"]
                                    cleared_fields.append("plotly_code")
                                except Exception:
                                    pass
                            
                            if cleared_fields:
                                entry["_evicted_at"] = current_time
                                entry["_evicted_fields"] = cleared_fields
                                evicted_count += 1
                                logger.debug(f"Evicted {cleared_fields} for user={uid} ws={wid} qid={qid} (idle for {int(time_since_access)}s)", extra={"cache": True})
        
        if evicted_count > 0:
            logger.info(f"Cache eviction completed: cleared heavy objects from {evicted_count} entries", extra={"cache": True})


    def update_cache_ttl(self, ttl_seconds: int):
        """
        Dynamically update the TTL for heavy cache objects.
        
        Args:
            ttl_seconds: New TTL in seconds (e.g., 600 for 10 minutes)
        """
        old_ttl = self.heavy_cache_ttl_seconds
        self.heavy_cache_ttl_seconds = ttl_seconds
        logger.info(f"Cache TTL updated from {old_ttl}s to {ttl_seconds}s", extra={"cache": True})


    def stop_eviction_thread(self):
        """Stop the background eviction thread (useful for cleanup/testing)."""
        if self._eviction_thread and self._eviction_thread.is_alive():
            self._eviction_stop_event.set()
            self._eviction_thread.join(timeout=5)
            logger.info("Cache eviction thread stopped", extra={"cache": True})


    def _update_access_time(self, uid: str, wid: str, qid: str):
        """Update the last access time for a question."""
        import time
        with self.last_access_lock:
            if uid not in self.last_access_times:
                self.last_access_times[uid] = {}
            if wid not in self.last_access_times[uid]:
                self.last_access_times[uid][wid] = {}
            self.last_access_times[uid][wid][qid] = time.time()


    def _get_db_connection(self):
        logger.info(f"_get_db_connection", extra={"flow":True})
        cfg = self.user_mgmt_config
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={cfg['server']},{cfg['port']};"
            f"DATABASE={cfg['database']};"
            f"UID={cfg['username']};"
            f"PWD={cfg['password']};"
            f"Trusted_Connection=no;"
            f"Connection Timeout=30;"
        )
        return pyodbc.connect(conn_str, autocommit=False)


    # helper: resolve active user_id and workspace_id
    def _resolve_user_workspace(self, user_id: Optional[str] = None, workspace_id: Optional[str] = None):
        logger.info(f"_resolve_user_workspace", extra={"flow":True})
        uid = str(user_id) if user_id is not None else None
        wid = str(workspace_id) if workspace_id is not None else None
        try:
            if has_request_context():
                if not uid:
                    uid = session.get("user_id")
                if not wid:
                    wid = session.get("workspace_id")
        except Exception:
            pass
        return (str(uid) if uid is not None else None, str(wid) if wid is not None else None)


    # helper: return the workspace map for a given user/workspace, creating nesting if needed
    def _get_workspace_map(self, uid: str, wid: str) -> Dict[str, Dict[str, Any]]:
        logger.info(f"_get_workspace_map", extra={"flow":True})
        if uid not in self.user_caches:
            self.user_caches[uid] = {}

        # detect legacy shape
        maybe_user_map = self.user_caches.get(uid, {})
        is_legacy = False
        if maybe_user_map:
            for val in maybe_user_map.values():
                if isinstance(val, dict) and ("question" in val or "sql" in val or "fig_json" in val):
                    is_legacy = True
                    break

        if is_legacy:
            legacy_key = "__legacy__"
            existing_flat = self.user_caches[uid]
            if not isinstance(existing_flat, dict) or legacy_key not in existing_flat:
                self.user_caches[uid] = {legacy_key: existing_flat}
            if wid not in self.user_caches[uid]:
                self.user_caches[uid][wid] = {}
        else:
            if wid not in self.user_caches[uid]:
                self.user_caches[uid][wid] = {}

        return self.user_caches[uid].get(wid, {})


    # ---------- core DB fetch ----------
    # def fetch_user_documents_for_user(self, user_id, workspace_id) -> Dict[str, Dict[str, Any]]:
    #     logger.info(f"fetch_user_documents_for_user", extra={"flow":True})
    #     if user_id is None or workspace_id is None:
    #         return {}
    #     # sql = """
    #     # SELECT question_id, question, sql_query, summary, plot_data, workspace_name, df
    #     # FROM dbo.[users]
    #     # WHERE user_id = ? and workspace_id = ?
    #     # ORDER BY timestamp DESC
    #     # """

    #     # sql = """
    #     # SELECT question_id, question, sql_query, workspace_name
    #     # FROM dbo.[users]
    #     # WHERE user_id = ? and workspace_id = ?
    #     # ORDER BY timestamp DESC
    #     # """

    #     sql = """
    #     SELECT question_id, question, sql_query, workspace_name, detected_language
    #     FROM users
    #     WHERE user_id = ? and workspace_id = ?
    #     ORDER BY timestamp DESC
    #     """
    #     results: Dict[str, Dict[str, Any]] = {}
    #     conn = None
    #     try:
    #         conn = self._get_db_connection()
    #         cur = conn.cursor()
    #         cur.execute(sql, (user_id, workspace_id))
    #         rows = cur.fetchall()
    #         for row in rows:
    #             question_id = row[0]
    #             if question_id is None:
    #                 continue
    #             qid = str(question_id)
    #             # Only store lightweight fields - df, fig_json, summary will be generated on-demand
    #             # results[qid] = {
    #             #     "question": row[1],
    #             #     "sql": row[2],
    #             #     "workspace": row[5]
    #             # }
    #             results[qid] = {
    #                 "question": row[1],
    #                 "sql": row[2],
    #                 "workspace": row[3]
    #             }
    #         cur.close()
    #         conn.commit()
    #         return results
    #     except Exception:
    #         if conn:
    #             try:
    #                 conn.rollback()
    #             except Exception:
    #                 pass
    #         return {}
    #     finally:
    #         if conn:
    #             conn.close()

    def fetch_user_documents_for_user(self, user_id, workspace_id) -> Dict[str, Dict[str, Any]]:
            logger.info(f"fetch_user_documents_for_user", extra={"flow":True})
            if user_id is None or workspace_id is None:
                return {}


            sql = """
            SELECT question_id, question, sql_query, workspace_name, detected_language
            FROM users
            WHERE user_id = ? and workspace_id = ?
            ORDER BY timestamp DESC
            """
            results: Dict[str, Dict[str, Any]] = {}
            conn = None
            try:
                conn = self._get_db_connection()
                cur = conn.cursor()
                cur.execute(sql, (user_id, workspace_id))
                rows = cur.fetchall()
                for row in rows:
                    question_id = row[0]
                    if question_id is None:
                        continue
                    qid = str(question_id)
            
                    results[qid] = {
                        "question": row[1],
                        "sql": row[2],
                        "workspace": row[3],
                        "detected_language": row[4]
                    }
                cur.close()
                conn.commit()
                return results
            except Exception:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                return {}
            finally:
                if conn:
                    conn.close()

    def refresh_cache_for_user(self, user_id, workspace_id) -> None:
        """Refresh the in-memory workspace cache for a user."""
        logger.info("refresh_cache_for_user", extra={"flow": True})

        uid, wid = self._resolve_user_workspace(user_id, workspace_id)
        if not uid or not wid:
            logger.info("refresh_cache_for_user called without user_id or workspace_id", extra={"cache": True})
            return

        try:
            data = self.fetch_user_documents_for_user(uid, wid) or {}
            if uid not in self.user_caches:
                self.user_caches[uid] = {}

            processed_workspace = {}

            for qid, raw_entry in (data.items() if isinstance(data, dict) else []):
                try:
                    if not isinstance(raw_entry, dict):
                        processed_workspace[qid] = raw_entry
                        continue

                    # Only copy lightweight fields
                    entry = {k: v for k, v in raw_entry.items() if k not in ["df", "fig_json", "summary"]}
                    processed_workspace[qid] = entry

                except Exception:
                    logger.exception("Failed processing entry %s while refreshing cache", qid, extra={"cache": True})
                    processed_workspace[qid] = raw_entry

            self.user_caches[uid][wid] = processed_workspace

            if uid not in self.last_ids:
                self.last_ids[uid] = {}
            first_id = next(iter(processed_workspace), None)
            self.last_ids[uid][wid] = first_id

            logger.info("Cache refreshed for user=%s workspace=%s entries=%d", uid, wid, len(processed_workspace), extra={"cache": True})

        except Exception as e:
            logger.exception("Failed to refresh cache for user=%s workspace=%s: %s", uid, wid, e, extra={"cache": True})
            if uid not in self.user_caches:
                self.user_caches[uid] = {}
            self.user_caches[uid][wid] = {}
            if uid not in self.last_ids:
                self.last_ids[uid] = {}
            self.last_ids[uid][wid] = None


    def ensure_id_loaded(self, id: str, user_id: Optional[str] = None) -> None:
        logger.info(f"ensure_id_loaded", extra={"flow":True})
        uid, wid = self._resolve_user_workspace(user_id, None)
        if uid is None or wid is None:
            return
        workspace_map = self._get_workspace_map(uid, wid)
        if id in workspace_map:
            return
        self.refresh_cache_for_user(uid, wid)


    def generate_id(self, *args, **kwargs):
        logger.info(f"generate_id", extra={"flow":True})
        return str(uuid.uuid4())

    # Add these methods to your MemoryCache class:

    @property
    def last_id(self):
        """
        Backward-compatible property for tracking the last used question ID.
        Returns the last ID for the current user's active workspace.
        """
        try:
            if has_request_context():
                uid = session.get("user_id")
                wid = session.get("workspace_id")
                if uid and wid:
                    return self.last_ids.get(str(uid), {}).get(str(wid))
        except Exception:
            pass
        
        # Fallback: return any last_id we can find
        for user_ids in self.last_ids.values():
            for workspace_id in user_ids.values():
                if workspace_id:
                    return workspace_id
        return None


    @last_id.setter
    def last_id(self, value):
        """
        Backward-compatible setter for last_id.
        Sets the last ID for the current user's active workspace.
        """
        try:
            if has_request_context():
                uid = session.get("user_id")
                wid = session.get("workspace_id")
                if uid and wid:
                    if uid not in self.last_ids:
                        self.last_ids[uid] = {}
                    self.last_ids[uid][wid] = value
                    return
        except Exception:
            pass
        
        # Fallback: create anonymous tracking
        uid = "__anonymous__"
        wid = "__anonymous_ws__"
        if uid not in self.last_ids:
            self.last_ids[uid] = {}
        self.last_ids[uid][wid] = value

    # def set(self, id, field, value, user_id: Optional[str] = None):
    #     logger.info(f"set - {field}", extra={"flow": True})
    #     uid, wid = self._resolve_user_workspace(user_id, None)
    #     if uid is None or wid is None:
    #         uid = uid or "__anonymous__"
    #         wid = wid or "__anonymous_ws__"
    #     wid = str(wid)

    #     # ensure maps exist
    #     if uid not in self.user_caches:
    #         self.user_caches[uid] = {}
    #     if wid not in self.user_caches[uid]:
    #         self.user_caches[uid][wid] = {}
    #     if id not in self.user_caches[uid][wid]:
    #         self.user_caches[uid][wid][id] = {}
    #     entry = self.user_caches[uid][wid][id]

    #     # Update access time for this question
    #     self._update_access_time(uid, wid, id)

    #     # --- Heavy objects: Store temporarily but will be auto-evicted ---
    #     if field in ["df", "fig_json", "summary"]:
    #         entry[field] = value
    #         entry[f"_{field}_stored_at"] = time.time()
    #         if uid not in self.last_ids:
    #             self.last_ids[uid] = {}
    #         self.last_ids[uid][wid] = id
    #         logger.info(f"set: stored {field} for id={id} (will auto-evict after {self.heavy_cache_ttl_seconds}s idle)", extra={"cache": True})
    #         return None

    #     # --- default: normal fields (lightweight, permanent) ---
    #     entry[field] = value
    #     if uid not in self.last_ids:
    #         self.last_ids[uid] = {}
    #     self.last_ids[uid][wid] = id
    #     try:
    #         preview = value if not isinstance(value, (bytes, bytearray)) else f"<{len(value)} bytes>"
    #         logger.info(f"Inside set(): user={uid} ws={wid} field={field} preview={str(preview)[:200]}", extra={"cache": True})
    #     except Exception:
    #         logger.info(f"Inside set(): updated cache for user {uid} ws {wid}", extra={"cache": True})

    #     return None

    # UPDATED set() for consistent anonymous handling:
    def set(self, id, field, value, user_id: Optional[str] = None):
        logger.info(f"set - {field}", extra={"flow": True})
        uid, wid = self._resolve_user_workspace(user_id, None)
        
        # Consistent anonymous handling
        if uid is None or wid is None:
            uid = uid or "__anonymous__"
            wid = wid or "__anonymous_ws__"
        
        uid = str(uid)
        wid = str(wid)

        # ensure maps exist
        if uid not in self.user_caches:
            self.user_caches[uid] = {}
        if wid not in self.user_caches[uid]:
            self.user_caches[uid][wid] = {}
        if id not in self.user_caches[uid][wid]:
            self.user_caches[uid][wid][id] = {}
        entry = self.user_caches[uid][wid][id]

        # Update access time for this question
        self._update_access_time(uid, wid, id)

        # --- Heavy objects: Store temporarily but will be auto-evicted ---
        if field in ["df", "fig_json", "summary", "plotly_code"]:
            entry[field] = value
            entry[f"_{field}_stored_at"] = time.time()
            if uid not in self.last_ids:
                self.last_ids[uid] = {}
            self.last_ids[uid][wid] = id
            logger.info(f"set: stored {field} for id={id} (will auto-evict after {self.heavy_cache_ttl_seconds}s idle)", extra={"cache": True})
            return None

        # --- default: normal fields (lightweight, permanent) ---
        entry[field] = value
        if uid not in self.last_ids:
            self.last_ids[uid] = {}
        self.last_ids[uid][wid] = id
        
        try:
            preview = value if not isinstance(value, (bytes, bytearray)) else f"<{len(value)} bytes>"
            logger.info(f"Inside set(): user={uid} ws={wid} field={field} preview={str(preview)[:200]}", extra={"cache": True})
        except Exception:
            logger.info(f"Inside set(): updated cache for user {uid} ws {wid}", extra={"cache": True})

        return None


    # def get(self, id, field, user_id: Optional[str] = None):
    #     global vn

    #     logger.info(f"get for field: {field}", extra={"flow": True})
    #     uid, wid = self._resolve_user_workspace(user_id, None)
    #     if uid is None or wid is None:
    #         return None

    #     # ensure workspace present
    #     if uid not in self.user_caches or str(wid) not in self.user_caches.get(uid, {}):
    #         self.refresh_cache_for_user(uid, wid)

    #     workspace_map = self.user_caches.get(uid, {}).get(str(wid), {})

    #     if id not in workspace_map:
    #         self.ensure_id_loaded(id, uid)
    #         workspace_map = self.user_caches.get(uid, {}).get(str(wid), {})
    #         if id not in workspace_map:
    #             return None

    #     entry = workspace_map.get(id, {})

    #     # Update access time whenever a field is accessed
    #     self._update_access_time(uid, wid, id)

    #     # --- DataFrame retrieval: Check cache or regenerate ---
    #     if field == "df":
    #         # Check if df exists in cache (not evicted)
    #         if "df" in entry and entry.get("df") is not None:
    #             logger.info(f"get: returning cached df for id={id}", extra={"cache": True})
    #             return entry.get("df")

    #         # Regenerate via vn.run_sql
    #         sql = entry.get("sql")
    #         if sql and vn is not None and getattr(vn, "run_sql_is_set", False):
    #             try:
    #                 logger.info(f"get: regenerating df by running SQL for id={id}", extra={"cache": True})
    #                 df = vn.run_sql(sql=sql)
    #                 # Store in cache (will be auto-evicted after TTL)
    #                 entry["df"] = df
    #                 entry["_df_stored_at"] = time.time()
    #                 entry["_df_regenerated"] = True
    #                 logger.info(f"get: regenerated and cached df for id={id}", extra={"cache": True})
    #                 return df
    #             except Exception as e:
    #                 logger.exception("get: run_sql failed: %s", e, extra={"cache": True})
    #                 return None
            
    #         logger.warning(f"get: cannot generate df for id={id} - no sql or vn not available", extra={"cache": True})
    #         return None

    #     # --- fig_json retrieval: Check cache or regenerate ---
    #     if field == "fig_json":
    #         if "fig_json" in entry and entry.get("fig_json") is not None:
    #             logger.info(f"get: returning cached fig_json for id={id}", extra={"cache": True})
    #             return entry.get("fig_json")

    #         # Regenerate fig_json
    #         df = self.get(id, "df", user_id=uid)
    #         if df is None:
    #             logger.info(f"get: cannot build fig_json for id={id} because df unavailable", extra={"cache": True})
    #             return None

    #         question = entry.get("question")
    #         sql = entry.get("sql")
    #         code = entry.get("plotly_code")
            
    #         try:
    #             # Generate plotly code if needed
    #             if code is None and hasattr(vn, "generate_plotly_code") and question and sql:
    #                 logger.info(f"get: generating plotly_code for id={id}", extra={"cache": True})
    #                 code = vn.generate_plotly_code(
    #                     question=question, 
    #                     sql=sql, 
    #                     df_metadata=f"Running df.dtypes gives:\n {df.dtypes}"
    #                 )
    #                 entry["plotly_code"] = code

    #             # Generate figure
    #             if code is not None and hasattr(vn, "get_plotly_figure"):
    #                 logger.info(f"get: regenerating plotly figure for id={id}", extra={"cache": True})
    #                 fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
    #                 fig_json = fig.to_json()
    #                 entry["fig_json"] = fig_json
    #                 entry["_fig_json_stored_at"] = time.time()
    #                 entry["_fig_json_regenerated"] = True
    #                 logger.info(f"get: regenerated and cached fig_json for id={id}", extra={"cache": True})
    #                 return fig_json
    #         except Exception as e:
    #             logger.exception("get: failed to generate fig_json: %s", e, extra={"cache": True})
    #             return None

    #         return None

    #     # --- summary retrieval: Check cache or regenerate ---
    #     if field == "summary":
    #         existing = entry.get("summary")
    #         if existing:
    #             logger.info(f"get: returning cached summary for id={id}", extra={"cache": True})
    #             return existing

    #         if vn is None or not hasattr(vn, "generate_summary"):
    #             logger.info(f"get: vn.generate_summary not available for id={id}", extra={"cache": True})
    #             return None

    #         summary_result = None
    #         try:
    #             # Try id-based generation
    #             try:
    #                 summary_result = vn.generate_summary(id=id, workspace=str(wid))
    #             except TypeError:
    #                 try:
    #                     summary_result = vn.generate_summary(id=id)
    #                 except Exception:
    #                     summary_result = None
    #             except Exception:
    #                 summary_result = None

    #             # Try question/sql based call
    #             if not summary_result:
    #                 question = entry.get("question")
    #                 sql = entry.get("sql")
    #                 try:
    #                     summary_result = vn.generate_summary(question=question, sql=sql)
    #                 except Exception:
    #                     summary_result = None

    #             # Last resort: pass df
    #             if not summary_result:
    #                 df_for_summary = self.get(id, "df", user_id=uid)
    #                 if df_for_summary is not None:
    #                     try:
    #                         summary_result = vn.generate_summary(
    #                             df=df_for_summary, 
    #                             question=entry.get("question"), 
    #                             sql=entry.get("sql")
    #                         )
    #                     except Exception:
    #                         summary_result = None

    #         except Exception as e:
    #             logger.exception("get: exception while generating summary for id=%s: %s", id, e, extra={"cache": True})
    #             summary_result = None

    #         # Normalize summary result
    #         normalized_summary = None
    #         if isinstance(summary_result, str):
    #             normalized_summary = summary_result
    #         elif isinstance(summary_result, dict):
    #             if "summary" in summary_result and isinstance(summary_result["summary"], str):
    #                 normalized_summary = summary_result["summary"]
    #             elif "text" in summary_result and isinstance(summary_result["text"], str):
    #                 normalized_summary = summary_result["text"]
    #             else:
    #                 try:
    #                     normalized_summary = str(summary_result)[:2000]
    #                 except Exception:
    #                     normalized_summary = None
    #         elif summary_result is not None:
    #             try:
    #                 normalized_summary = str(summary_result)
    #             except Exception:
    #                 normalized_summary = None

    #         if normalized_summary:
    #             entry["summary"] = normalized_summary
    #             entry["_summary_stored_at"] = time.time()
    #             entry["_summary_regenerated"] = True
    #             logger.info(f"get: regenerated and cached summary for id={id}", extra={"cache": True})
    #             return normalized_summary

    #         logger.info(f"get: unable to generate summary for id={id}", extra={"cache": True})
    #         return None

    #     # --- Default: return field from entry ---
    #     return entry.get(field, None)

    # UPDATED get() method with better error handling:
    def get(self, id, field, user_id: Optional[str] = None):
        global vn

        logger.info(f"get for field: {field}", extra={"flow": True})
        uid, wid = self._resolve_user_workspace(user_id, None)
        
        # Handle anonymous users consistently
        if uid is None or wid is None:
            uid = uid or "__anonymous__"
            wid = wid or "__anonymous_ws__"

        uid = str(uid)
        wid = str(wid)

        # Ensure workspace present
        if uid not in self.user_caches or wid not in self.user_caches.get(uid, {}):
            self.refresh_cache_for_user(uid, wid)

        workspace_map = self.user_caches.get(uid, {}).get(wid, {})

        if id not in workspace_map:
            self.ensure_id_loaded(id, uid)
            workspace_map = self.user_caches.get(uid, {}).get(wid, {})
            if id not in workspace_map:
                return None

        entry = workspace_map.get(id, {})

        # Update access time whenever a field is accessed
        self._update_access_time(uid, wid, id)

        # [Rest of your get() logic remains the same...]
        
        # --- DataFrame retrieval: Check cache or regenerate ---
        if field == "df":
            if "df" in entry and entry.get("df") is not None:
                logger.info(f"get: returning cached df for id={id}", extra={"cache": True})
                return entry.get("df")

            sql = entry.get("sql")
            if sql and vn is not None and getattr(vn, "run_sql_is_set", False):
                try:
                    logger.info(f"get: regenerating df by running SQL for id={id}", extra={"cache": True})
                    df = vn.run_sql(sql=sql)
                    entry["df"] = df
                    entry["_df_stored_at"] = time.time()
                    entry["_df_regenerated"] = True
                    logger.info(f"get: regenerated and cached df for id={id}", extra={"cache": True})
                    return df
                except Exception as e:
                    logger.exception("get: run_sql failed: %s", e, extra={"cache": True})
                    return None
            
            logger.warning(f"get: cannot generate df for id={id} - no sql or vn not available", extra={"cache": True})
            return None

        # [Continue with fig_json, summary, and default cases as in your original code...]
        
        return entry.get(field, None)

    # def get_all(self, field_list, user_id: Optional[str] = None) -> list:
    #     uid, wid = self._resolve_user_workspace(user_id, None)
    #     if uid is None or wid is None:
    #         return []
    #     wid = str(wid)
    #     if uid not in self.user_caches or wid not in self.user_caches.get(uid, {}):
    #         self.refresh_cache_for_user(uid, wid)
    #     workspace_map = self.user_caches.get(uid, {}).get(wid, {})
    #     ALL = [
    #         {"id": qid, **{field: workspace_map.get(qid, {}).get(field) for field in field_list}}
    #         for qid in workspace_map
    #     ]
    #     logger.info("get_all() user=%s ws=%s Data count=%d", uid, wid, len(ALL), extra={"cache":True})
    #     return ALL

    # UPDATED get_all() to update access times:
    def get_all(self, field_list, user_id: Optional[str] = None) -> list:
        uid, wid = self._resolve_user_workspace(user_id, None)
        
        # Handle anonymous users
        if uid is None or wid is None:
            uid = uid or "__anonymous__"
            wid = wid or "__anonymous_ws__"
        
        uid = str(uid)
        wid = str(wid)
        
        if uid not in self.user_caches or wid not in self.user_caches.get(uid, {}):
            self.refresh_cache_for_user(uid, wid)
        
        workspace_map = self.user_caches.get(uid, {}).get(wid, {})
        
        # Update access times for all questions being retrieved
        for qid in workspace_map:
            self._update_access_time(uid, wid, qid)
        
        ALL = [
            {"id": qid, **{field: workspace_map.get(qid, {}).get(field) for field in field_list}}
            for qid in workspace_map
        ]
        logger.info("get_all() user=%s ws=%s Data count=%d", uid, wid, len(ALL), extra={"cache":True})
        return ALL

    # def delete(self, id, user_id: Optional[str] = None):
    #     uid, wid = self._resolve_user_workspace(user_id, None)
    #     if uid is None or wid is None:
    #         return
        
    #     # Delete from main cache
    #     if uid in self.user_caches and wid in self.user_caches[uid] and id in self.user_caches[uid][wid]:
    #         del self.user_caches[uid][wid][id]
    #         if self.last_ids.get(uid, {}).get(wid) == id:
    #             self.last_ids[uid][wid] = next(iter(self.user_caches[uid][wid]), None)
    #         logger.info(f"delete: removed cache entry for id={id}", extra={"cache": True})
        
    #     # Delete from access times
    #     with self.last_access_lock:
    #         if uid in self.last_access_times and wid in self.last_access_times[uid] and id in self.last_access_times[uid][wid]:
    #             del self.last_access_times[uid][wid][id]

    # UPDATED delete() for consistent handling:
    def delete(self, id, user_id: Optional[str] = None):
        uid, wid = self._resolve_user_workspace(user_id, None)
        
        # Handle anonymous users
        if uid is None or wid is None:
            uid = uid or "__anonymous__"
            wid = wid or "__anonymous_ws__"
        
        uid = str(uid)
        wid = str(wid)
        
        # Delete from main cache
        if uid in self.user_caches and wid in self.user_caches[uid] and id in self.user_caches[uid][wid]:
            del self.user_caches[uid][wid][id]
            if self.last_ids.get(uid, {}).get(wid) == id:
                self.last_ids[uid][wid] = next(iter(self.user_caches[uid][wid]), None)
            logger.info(f"delete: removed cache entry for id={id}", extra={"cache": True})
        
        # Delete from access times
        with self.last_access_lock:
            if uid in self.last_access_times and wid in self.last_access_times[uid] and id in self.last_access_times[uid][wid]:
                del self.last_access_times[uid][wid][id]

    def clear_workspace_cache(self, user_id: str, workspace_id: str):
        uid = str(user_id)
        wid = str(workspace_id)
        if uid in self.user_caches:
            self.user_caches[uid].pop(wid, None)
        if uid in self.last_ids:
            self.last_ids[uid].pop(wid, None)
        with self.last_access_lock:
            if uid in self.last_access_times:
                self.last_access_times[uid].pop(wid, None)


    def clear_user_cache(self, user_id: str):
        uid = str(user_id)
        self.user_caches.pop(uid, None)
        self.last_ids.pop(uid, None)
        with self.last_access_lock:
            self.last_access_times.pop(uid, None)


    @property
    def cache(self):
        try:
            if has_request_context():
                uid = session.get("user_id")
                wid = session.get("workspace_id")
                if uid and wid:
                    return self.user_caches.get(str(uid), {}).get(str(wid), {})
        except Exception:
            pass
        return {}
    

    def clear_workspace_for_user(self, user_id: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
        """Clear the cache for a specific workspace for a user."""
        if workspace_id is None:
            logger.warning("clear_workspace_for_user called without workspace_id", extra={"cache": True})
            return False

        if not hasattr(self, "_global_lock"):
            import threading
            self._global_lock = threading.Lock()

        uid, _ = self._resolve_user_workspace(user_id, None)
        if uid is None:
            uid = user_id

        if uid is None:
            logger.warning("clear_workspace_for_user: no user id resolved or provided", extra={"cache": True})
            return False

        uid = str(uid)
        wid = str(workspace_id)

        with self._global_lock:
            # Clear main cache
            try:
                if hasattr(self, "user_caches") and uid in self.user_caches and wid in self.user_caches[uid]:
                    try:
                        cnt_questions = len(self.user_caches[uid][wid] or {})
                        logger.info(f"clear_workspace_for_user: removing user={uid} workspace={wid} with {cnt_questions} questions", extra={"cache": True})
                    except Exception:
                        logger.info(f"clear_workspace_for_user: removing user={uid} workspace={wid}", extra={"cache": True})

                    del self.user_caches[uid][wid]

                    if not self.user_caches[uid]:
                        try:
                            del self.user_caches[uid]
                        except Exception:
                            pass
            except Exception:
                logger.exception("clear_workspace_for_user: failed to delete workspace map", extra={"cache": True})
                return False

            # Clear last_ids
            try:
                if hasattr(self, "last_ids") and uid in self.last_ids and wid in self.last_ids[uid]:
                    del self.last_ids[uid][wid]
                    if not self.last_ids[uid]:
                        try:
                            del self.last_ids[uid]
                        except Exception:
                            pass
            except Exception:
                logger.exception("clear_workspace_for_user: failed to update last_ids", extra={"cache": True})

            # Clear access times
            with self.last_access_lock:
                try:
                    if hasattr(self, "last_access_times") and uid in self.last_access_times and wid in self.last_access_times[uid]:
                        del self.last_access_times[uid][wid]
                        if not self.last_access_times[uid]:
                            del self.last_access_times[uid]
                except Exception:
                    logger.exception("clear_workspace_for_user: failed to clear access times", extra={"cache": True})

            # Clean up per-id locks
            try:
                if hasattr(self, "_id_locks") and isinstance(self._id_locks, dict):
                    locks = self._id_locks
                    if uid in locks and isinstance(locks[uid], dict) and wid in locks[uid]:
                        try:
                            del locks[uid][wid]
                            if not locks[uid]:
                                del locks[uid]
                        except Exception:
                            pass
            except Exception:
                logger.exception("clear_workspace_for_user: error cleaning _id_locks", extra={"cache": True})

        logger.info(f"clear_workspace_for_user: completed for user={uid} workspace={wid}", extra={"cache": True})
        return True
    

#for agent mails 
def _rows_to_csv(rows):
    if not rows: return None
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
    return out.getvalue()

# def _send_email(recipients, subject, body, rows, filename):
#     if not recipients: return
#     msg = MIMEMultipart()
#     msg["From"] = SMTP_FROM
#     msg["To"]   = ", ".join(recipients)
#     msg["Subject"] = subject
#     msg.attach(MIMEText(body, "plain", "utf-8"))
#     csv_data = _rows_to_csv(rows)
#     if csv_data:
#         part = MIMEBase("application", "octet-stream")
#         part.set_payload(csv_data.encode("utf-8"))
#         encoders.encode_base64(part)
#         part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
#         msg.attach(part)
#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=90) as s:
#         s.starttls(); s.login(SMTP_USER, SMTP_PASS)
#         s.sendmail(SMTP_FROM, recipients, msg.as_string())


# Send email using SMTP (e.g., Gmail)
def _send_email_smtp(recipients, subject, body, rows, filename, cfg):
    if not recipients:
        return False

    SMTP_SERVER = cfg["smtp_server"]
    SMTP_PORT = int(cfg["smtp_port"])
    SMTP_USER = cfg["sender_email"]
    SMTP_PASS = cfg["sender_password"]
    SMTP_FROM = cfg["sender_email"]

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    csv_data = _rows_to_csv(rows)
    if csv_data:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(csv_data.encode("utf-8"))
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"'
        )
        msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_FROM, recipients, msg.as_string())

    return True


# Send email using Microsoft Graph API (Outlook)
def _send_email_outlook_graph(recipients, subject, body, rows, filename, cfg):
    outlook = cfg["outlook"]

    # 1) Get access token
    token_res = requests.post(
        f"https://login.microsoftonline.com/{outlook['tenant_id']}/oauth2/v2.0/token",
        data={
            "client_id": outlook["client_id"],
            "client_secret": outlook["client_secret"],
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default"
        },
        timeout=30
    )

    token_res.raise_for_status()
    access_token = token_res.json()["access_token"]

    # 2) Prepare attachment
    attachments = []
    csv_data = _rows_to_csv(rows)
    if csv_data:
        attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": filename,
            "contentType": "text/csv",
            "contentBytes": base64.b64encode(
                csv_data.encode("utf-8")
            ).decode("utf-8")
        })

    # 3) Build mail payload
    mail = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": r}} for r in recipients
            ],
            "attachments": attachments
        }
    }

    # 4) Send mail
    res = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{outlook['sender_email']}/sendMail",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=mail,
        timeout=30
    )

    res.raise_for_status()
    return True


# Main function to send email based on configured provider
def _send_email(recipients, subject, body, rows, filename):
    if not recipients:
        return False

    cfg = load_email_config()

    if not cfg.get("send_email_enabled", True):
        print("Email sending disabled (kill switch)")
        return False

    provider = cfg.get("email_provider", "gmail")

    if provider == "gmail":
        return _send_email_smtp(
            recipients, subject, body, rows, filename, cfg["gmail"]
        )

    if provider == "outlook":
        return _send_email_outlook_graph(
            recipients, subject, body, rows, filename, cfg
        )

    raise ValueError(f"Unsupported email provider: {provider}")

def initialize_vanna_instance(workspace_id, llm_details, db_details, db_details_b=None):
            global vn
            try:
                # Initialize Vanna based on LLM type
                if llm_details['model_type'] == 'openai':
                    if not llm_details['api_key']:
                        logger.warning("API key missing for OpenAI model", extra={"admin": True})
                        logger.warning("API key missing for OpenAI model", extra={"user": True})
                        return {"success": False, "error": "API key is required for OpenAI models"}

                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)

                    vn = MyVanna(config={
                        'api_key': llm_details['api_key'],
                        'model': llm_details['model_name'],
                        'allow_llm_to_see_data': True
                    })
                elif llm_details['model_type'] == 'ollama':
                    class MyVanna(ChromaDB_VectorStore, Ollama):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            Ollama.__init__(self, config=config)

                    vn = MyVanna(config={
                        'model': llm_details['model_name'],
                        'allow_llm_to_see_data': True
                    })
                else:
                    return {"success": False, "error": "Unsupported LLM model type."}

                # Use the same ODBC connection string as /connect-vanna
                odbc_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={db_details['serverName']},{db_details['port']};"
                    f"DATABASE={db_details['databaseName']};"
                    f"UID={db_details['username']};"
                    f"PWD={db_details['password']};"
                )
                logger.info(f"Connecting to MSSQL with: {odbc_conn_str.replace(db_details['password'], '****')}", extra={"admin": True})
                vn.connect_to_mssql(odbc_conn_str=odbc_conn_str)

                # Record primary/secondary DB aliases for cross-DB SQL qualification
                # (see get_sql_prompt). No live connection to the secondary DB — it's
                # reached either via same-instance three-part naming (if both databases
                # share the same server+port) or a linked server (if genuinely separate
                # servers) — get_sql_prompt picks the right form using vn.same_instance.
                vn.primary_db_alias = db_details.get("db_alias") or "PRIMARY"
                vn.primary_db_name = db_details.get("databaseName")
                if db_details_b and db_details_b.get("databaseName"):
                    vn.secondary_db_alias = db_details_b.get("db_alias") or "SECONDARY"
                    vn.secondary_db_name = db_details_b.get("databaseName")
                    vn.same_instance = (
                        str(db_details_b.get("serverName") or "").strip().lower()
                            == str(db_details.get("serverName") or "").strip().lower()
                        and str(db_details_b.get("port") or "").strip()
                            == str(db_details.get("port") or "").strip()
                    )
                else:
                    vn.secondary_db_alias = None
                    vn.secondary_db_name = None
                    vn.same_instance = False

                # Optionally store vn in vanna_api if needed
                # vanna_api.vn = vn  # Uncomment if vanna_api is a valid object
                logger.info(f"Vanna initialized for workspace {workspace_id}", extra={"admin": True})
                return {"success": True, "message": "Vanna initialized successfully."}
            except Exception as e:
                logger.error(f"Failed to initialize Vanna: {str(e)}", exc_info=True, extra={"admin": True})
                return {"success": False, "error": f"Failed to initialize Vanna: {str(e)}"}



class VannaFlaskAPI:
    flask_app = None

    #for agent initlaization
    def ensure_vanna_initialized(self, workspace_id):
            global vn
            logger.info("ensure vanna function")
            
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return False, "Workspace not found"
            logger.info(f"Workspace inside ensure {workspace}")
            llm_config = json.loads(workspace.get("llm_config", "{}"))
            db_config = json.loads(workspace.get("db_config", "{}"))
            db_config_b = json.loads(workspace.get("db_config_b", "{}"))
            logger.info(f"ensure vanna function {llm_config} {db_config}")

            data_to_send = {
                "workspace_id": workspace_id,
                "llm_details": {
                    "model_name": llm_config.get("model_name"),
                    "model_type": llm_config.get("model_type"),
                    "api_key": llm_config.get("api_key"),
                    "base_url": llm_config.get("base_url")
                },
                "db_details": {
                    "serverName": db_config.get("serverName"),
                    "port": db_config.get("port"),
                    "databaseName": db_config.get("databaseName"),
                    "username": db_config.get("username"),
                    "password": db_config.get("password"),
                    "db_alias": db_config.get("db_alias")
                },
                "db_details_b": {
                    "databaseName": db_config_b.get("databaseName"),
                    "db_alias": db_config_b.get("db_alias"),
                    "serverName": db_config_b.get("serverName"),
                    "port": db_config_b.get("port")
                } if db_config_b.get("databaseName") else None
            }
            result = initialize_vanna_instance(
                workspace_id, data_to_send["llm_details"], data_to_send["db_details"],
                data_to_send["db_details_b"]
            )
            if not result["success"]:
                return False, result["error"]

            # CRITICAL: Update self.vn to point to the globally initialized instance
            self.vn = vn
            logger.info("ensure_vanna_initialized: self.vn updated directly from global vn")

            return True, None
    
   


    def requires_cache(self, required_fields, optional_fields=[]):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                id = request.args.get("id")
                if id is None:
                    try:
                        id = request.json.get("id")
                    except Exception:
                        id = None

                # Use last_id if still None
                if id is None:
                    id = self.cache.last_id
                    if id is None:
                        return jsonify({"type": "error", "error": "No id provided and no cached entry available"})

                # Ensure required fields exist
                for field in required_fields:
                    if self.cache.get(id=id, field=field) is None:
                    #   if field == "df":
                    #       return jsonify({
                    #           "type": "text",
                    #           "id": id,
                    #           "text": "No data available to generate a summary.",
                    #       })
                    #   return jsonify({"type": "error", "error": f"No {field} found for id {id}"})
                        if field == "df":
                            # Base English message
                            base_msg = "No data available to generate a summary."

                            # Get detected language from cache (stored during generate_sql)
                            user_language = self.cache.get(id=id, field="detected_language")

                            # Translate message back to user's language if needed
                            localized_msg = translate_text(base_msg, user_language)

                            return jsonify({
                                "type": "text",
                                "id": id,
                                "text": localized_msg,
                                "language": user_language
                            })


                # Collect fields
                field_values = {
                    field: self.cache.get(id=id, field=field) for field in required_fields
                }

                for field in optional_fields:
                    field_values[field] = self.cache.get(id=id, field=field)

                field_values["id"] = id
                return f(*args, **field_values, **kwargs)

            return decorated
        return decorator

    # def requires_auth(self, f):
    #     @wraps(f)
    #     def decorated(*args, **kwargs):
    #         user = self.auth.get_user(request)
    #         if not self.auth.is_logged_in(user):
    #             return redirect(url_for("login"))
    #         return f(*args, user=user, **kwargs)  # pass as kwarg
    #     return decorated
    
    def requires_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not has_request_context():
                return jsonify({"type":"error","error":"No request context"}), 401

            # If some outer decorator already supplied user, honor it.
            user = kwargs.get("user")
            if user is None:
                user = self.auth.get_user(request)

            if not user:
                return redirect(url_for("login"))

            # Put user into kwargs only if not present
            if "user" not in kwargs:
                kwargs["user"] = user

            return f(*args, **kwargs)
        return decorated


    # def requires_role(self, allowed_roles):
    #     def decorator(f):
    #         @wraps(f)
    #         def wrapped(*args, **kwargs):
    #             if not has_request_context():
    #                 return jsonify({"type":"error","error":"No request context"}), 401
    #             user = self.auth.get_user(request)
    #             if not user:
    #                 return redirect(url_for("login"))
    #             role = session.get("role")
    #             if isinstance(allowed_roles, (list, tuple, set)):
    #                 ok = role in allowed_roles
    #             else:
    #                 ok = role == allowed_roles
    #             if not ok:
    #                 return jsonify({"type":"error","error":"Permission denied"}), 403
    #             return f(*args, user=user, **kwargs)
    #         return wrapped
    #     return decorator
    

    # def requires_role(self, allowed_roles):
    #     def decorator(f):
    #         @wraps(f)
    #         def wrapped(*args, **kwargs):
    #             # ensure request context
    #             if not has_request_context():
    #                 return jsonify({"type":"error","error":"No request context"}), 401

    #             # if requires_auth already provided a user object, prefer that
    #             user = kwargs.get("user")
    #             if user is None:
    #                 # fallback to getting user from auth
    #                 user = self.auth.get_user(request)

    #             # not authenticated
    #             if not user:
    #                 # for HTML pages you may want redirect; for API endpoints return JSON
    #                 # choose one strategy — here's redirect (keeps original behavior)
    #                 return redirect(url_for("login"))

    #             # role can come from session or from user object if available
    #             role = session.get("role") or getattr(user, "role", None) or user.get("role", None)

    #             # debug log
    #             logger.debug("requires_role: user=%s role=%s required=%s", getattr(user, "id", None) or user.get("id", None), role, allowed_roles)

    #             if isinstance(allowed_roles, (list, tuple, set)):
    #                 ok = role in allowed_roles
    #             else:
    #                 ok = role == allowed_roles

    #             if not ok:
    #                 return jsonify({"type":"error","error":"Permission denied"}), 403

    #             # pass user in kwargs so any inner code can receive it
    #             kwargs.setdefault("user", user)
    #             return f(*args, **kwargs)
    #         return wrapped
    #     return decorator
    
    def requires_role(self, allowed_roles):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not has_request_context():
                    return jsonify({"type":"error","error":"No request context"}), 401

                # Prefer user already injected into kwargs by requires_auth
                user = kwargs.get("user")
                if user is None:
                    user = self.auth.get_user(request)

                if not user:
                    return redirect(url_for("login"))

                # Prefer role from kwargs/session/user
                role = kwargs.get("role") or session.get("role") or getattr(user, "role", None) or user.get("role", None)

                logger.debug("requires_role check: required=%s role=%s user=%s", allowed_roles, role, getattr(user, "id", None) or user.get("id", None))

                if isinstance(allowed_roles, (list, tuple, set)):
                    ok = role in allowed_roles
                else:
                    ok = role == allowed_roles

                if not ok:
                    return jsonify({"type":"error","error":"Permission denied"}), 403

                # ensure we pass user forward but do not re-inject if already present
                if "user" not in kwargs:
                    kwargs["user"] = user

                return f(*args, **kwargs)
            return wrapped
        return decorator







    def __init__(
        self,
        #vn: VannaBase,
        cache: Cache = MemoryCache(),
        auth: AuthInterface = NoAuth(),
        debug=False,
        allow_llm_to_see_data=False,
        chart=True,
    ):
        global vn
        """
        Expose a Flask API that can be used to interact with a Vanna instance.

        Args:
            vn: The Vanna instance to interact with.
            cache: The cache to use. Defaults to MemoryCache, which uses an in-memory cache. You can also pass in a custom cache that implements the Cache interface.
            auth: The authentication method to use. Defaults to NoAuth, which doesn't require authentication. You can also pass in a custom authentication method that implements the AuthInterface interface.
            debug: Show the debug console. Defaults to True.
            allow_llm_to_see_data: Whether to allow the LLM to see data. Defaults to False.
            chart: Whether to show the chart output in the UI. Defaults to True.

        Returns:
            None
        """

        # Was hardcoded to the project's old location (d:/Admin-Module/WAI/templates),
        # which no longer exists after the project moved to D:\WAI — resolving against
        # the working directory (main.py is always launched from the project root)
        # survives future moves instead of hardcoding another absolute path.
        self.flask_app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "templates"))

        self.swagger = Swagger(
          self.flask_app, template={"info": {"title": "Tychons API"}}
        )
        self.sock = Sock(self.flask_app)
        self.ws_clients = []
        self.vn = vn
        self.auth = auth
        self.cache = cache
        self.debug = debug
        self.allow_llm_to_see_data = allow_llm_to_see_data
        self.chart = chart
        self.scenario_cache = {} # Cache for agent scenario dataframes
        self.config = {
          "debug": debug,
          "allow_llm_to_see_data": allow_llm_to_see_data,
          "chart": chart,
        }


        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        if "google.colab" in sys.modules:
            self.debug = False
            print("Google Colab doesn't support running websocket servers. Disabling debug mode.")

        if self.debug:
            def log(message, title="Info"):
                [ws.send(json.dumps({'message': message, 'title': title})) for ws in self.ws_clients]

            self.vn.log = log


        @self.flask_app.route("/api/v0/get_config", methods=["GET"])
        @self.requires_auth
        def get_config(user: any):
            """
            Get the configuration for a user
            ---
            parameters:
              - name: user
                in: query
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: config
                    config:
                      type: object
            """
            config = self.auth.override_config_for_user(user, self.config)
            return jsonify(
                {
                    "type": "config",
                    "config": config
                }
            )

        @self.flask_app.route("/api/v0/generate_questions", methods=["GET"])
        @self.requires_auth
        def generate_questions(user: any):
            """
            Generate questions
            ---
            parameters:
              - name: user
                in: query
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: question_list
                    questions:
                      type: array
                      items:
                        type: string
                    header:
                      type: string
                      default: Here are some questions you can ask
            """
            workspace = flask.request.args.get("workspace_name")
            logger.info(f"while loading generate_question {workspace}")
            # If self has an _model attribute and model=='chinook'
            if hasattr(self.vn, "_model") and self.vn._model == "chinook":
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": [
                            "What are the top 10 artists by sales?",
                            "What are the total sales per year by country?",
                            "Who is the top selling artist in each genre? Show the sales numbers.",
                            "How do the employees rank in terms of sales performance?",
                            "Which 5 cities have the most customers?",
                        ],
                        "header": "Here are some questions you can ask:",
                    }
                )

            training_data = vn.get_training_data(workspace=workspace)

            # If training data is None or empty
            if training_data is None or len(training_data) == 0:
                return jsonify(
                    {
                        "type": "error",
                        "error": "No training data found. Please add some training data first.",
                    }
                )

            # Get the questions from the training data
            try:
                # Filter training data to only include questions where the question is not null
                
                questions = (
                    training_data[training_data["question"].notnull()]
                    .sample(5)["question"]
                    .tolist()
                )
                # questions = [
                #     "What container types are available for warehouse 1?",
                #     "Check items that have quantities below 10.",
                #     "Show the items that are finished goods",
                #     "How many orders are ready for shipping?",
                #     "What are the works completed in the warehouse"
                # ]

                # Temporarily this will just return an empty list
                # return jsonify(
                #     {
                #         "type": "question_list",
                #         "questions": questions,
                #         "header": "Here are some questions you can ask",
                #     }
                # )
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": questions,
                        "header": "Here are some questions you can ask",
                    }
                )
            except Exception as e:
                return jsonify(
                    {
                        "type": "question_list",
                        "questions": [],
                        "header": "Go ahead and ask a question",
                    }
                )
        
#############generate sql without tanslate ###################
        # @self.flask_app.route("/api/v0/generate_sql", methods=["GET"])
        # @self.requires_auth
        # def generate_sql(user: any):
        #     """
        #     Generate SQL from a question with optional previous SQL context
        #     ---
        #     parameters:
        #     - name: user
        #         in: query
        #     - name: question
        #         in: query
        #         type: string
        #         required: true
        #     - name: sql
        #         in: query
        #         type: string
        #         description: Previous SQL query for context
        #     - name: workspace
        #         in: query
        #         type: string
        #         required: true
        #     responses:
        #     200:
        #         schema:
        #         type: object
        #         properties:
        #             type:
        #             type: string
        #             default: sql
        #             id:
        #             type: string
        #             text:
        #             type: string
        #     """
        #     question = flask.request.args.get("question")
        #     previous_sql = flask.request.args.get("sql")
        #     workspace = flask.request.args.get("workspace")
        #     logger.info(f"Inside generate_sql endpoint - Question: '{question}', Previous SQL: '{previous_sql}', Workspace: '{workspace}'", extra={"admin": True})
        #     logger.info(f"Inside generate_sql endpoint - Question: '{question}', Previous SQL: '{previous_sql}', Workspace: '{workspace}'", extra={"followup": True})
        #     logger.info(f"Request Args: {flask.request.args}", extra={"followup": True})
            
        #     logger.info(f"Question: '{question}', Previous SQL: '{previous_sql}', Workspace: '{workspace}'", extra={"user": True})

        #     # Validate required parameters
        #     if question is None:
        #         return jsonify({"type": "error", "error": "No question provided"}), 400
            
        #     if workspace is None:
        #         return jsonify({"type": "error", "error": "No workspace provided"}), 400

        #     # Generate SQL based on whether we have previous SQL context
        #     if previous_sql and previous_sql.lower() != 'null':
        #         logger.info(f"inside generate sql if condition", extra={"followup": True})

        #         id = self.cache.generate_id(question=previous_sql)
        #         sql = vn.generate_sql(
        #             question=previous_sql,
        #             followup_sql=question,
        #             allow_llm_to_see_data=self.allow_llm_to_see_data,
        #             workspace=workspace
        #         )
        #         logger.info(f"IF - SQL Query: {sql}", extra={"followup": True})
        #     else:
        #         logger.info(f"inside generate sql else condition", extra={"followup": True})
        #         id = self.cache.generate_id(question=question)
        #         sql = vn.generate_sql(
        #             question=question,
        #             allow_llm_to_see_data=self.allow_llm_to_see_data,
        #             workspace=workspace
        #         )
        #         logger.info(f"ELSE - SQL Query: {sql}", extra={"followup": True})
        #     logger.info(f"SQL Query: {sql}", extra={"admin": True})
        #     logger.info(f"SQL Query: {sql}", extra={"user": True})
        #     # Cache the results
        #     self.cache.set(id=id, field="question", value=question)
        #     self.cache.set(id=id, field="sql", value=sql)
        #     self.cache.set(id=id, field="workspace", value=workspace)

        #     # db push
        #     workspace = flask.request.args.get("workspace")
        #     user_role = session.get('username', None)
        #     user_id = session.get('user_id', None)
        #     # self._log_complete_user_activity(
        #     #     question=question,
        #     #     sql_query=sql,
        #     #     summary=None,
        #     #     workspace_name=workspace,
        #     #     user_role=user_role,
        #     #     user_id = user_id,
        #     #     cache_id=id
        #     # )
        #     #RBA
        #     self.log_user_activity(
        #         question_id=id,
        #         question=question,
        #         sql_query=sql,
        #         workspace_name=workspace,
        #         user_role=user_role,
        #         user_id=user_id
        #     )
        #     # Validate and return the SQL
        #     if vn.is_sql_valid(sql=sql):
        #         return jsonify({
        #             "type": "sql",
        #             "id": id,
        #             "text": sql,
        #         })
        #     else:
        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": sql,
        #         })

        @self.flask_app.route("/api/v0/generate_sql", methods=["GET"])
        @self.requires_auth
        def generate_sql(user: any):
            """
            Generate SQL from a natural language question (supports multilingual input).
            Handles follow-up questions, token logging, billing, caching, and activity tracking.
            """
            question_raw = flask.request.args.get("question")
            previous_sql = flask.request.args.get("sql")
            workspace = flask.request.args.get("workspace")

            # ────────────────────────────────────────────────
            #  Validation
            # ────────────────────────────────────────────────
            if not question_raw:
                return jsonify({"type": "error", "error": "No question provided"}), 400

            if not workspace:
                return jsonify({"type": "error", "error": "No workspace provided"}), 400

            # Clean + prepare
            question_clean = clean_question(question_raw)

            # ────────────────────────────────────────────────
            # 🌍 Language detection + translation
            # ────────────────────────────────────────────────
            translation_result = translate_question_if_needed(question_clean)

            original_question   = translation_result["original"]
            question_en         = translation_result["translated"]      # ALWAYS English for LLM
            detected_language   = translation_result["language"]
            was_translated      = translation_result["was_translated"]

            # ────────────────────────────────────────────────
            # Logging – early visibility
            # ────────────────────────────────────────────────
            logger.info(
                f"Question (EN): '{question_en}', Prev SQL: '{previous_sql or None}', Workspace: '{workspace}'",
                extra={"admin": True}
            )
            logger.info(
                f"Question (orig): '{original_question}', Prev SQL: '{previous_sql or None}', Workspace: '{workspace}'",
                extra={"user": True}
            )
            if was_translated:
                logger.info(
                    f"Translated {detected_language} → EN: '{original_question}' → '{question_en}'",
                    extra={"user": True}
                )

            # ────────────────────────────────────────────────
            # Read vs write routing (see vn.classify_intent) — a write-classified
            # question never reaches generate_sql's read-only prompt. It's routed
            # to the write-preview flow instead: the SQL is generated and validated
            # against the workspace's write whitelist, cached server-side by write_id,
            # and returned for confirmation — never auto-executed, unlike reads.
            # ────────────────────────────────────────────────
            if vn.classify_intent(question_en) == "write":
                workspace_id_for_write = flask.session.get("workspace_id")
                if not workspace_id_for_write:
                    return jsonify({
                        "type": "error",
                        "error": "Workspace is not fully connected (no workspace_id in session) — cannot stage a write.",
                    }), 400
                body, status = _stage_pending_write(vn, workspace, workspace_id_for_write, question_en, original_question)
                if status == 200 and body.get("type") == "write_confirmation":
                    body["detected_language"] = detected_language
                    body["was_translated"] = was_translated
                    body["translated_question"] = question_en if was_translated else None
                return jsonify(body), status

            # ────────────────────────────────────────────────
            # Decide ID + call generate_sql
            # ────────────────────────────────────────────────
            if previous_sql and str(previous_sql).lower() != "null":
                logger.info("Follow-up mode (IF branch)", extra={"followup": True})
                cache_id = self.cache.generate_id(question=previous_sql)   # key on context
                sql_result = vn.generate_sql(
                    question=previous_sql,           # previous context
                    followup_sql=question_en,        # new (translated) question
                    allow_llm_to_see_data=self.allow_llm_to_see_data,
                    workspace=workspace
                )
            else:
                logger.info("First question mode (ELSE branch)", extra={"followup": True})
                cache_id = self.cache.generate_id(question=question_en)
                sql_result = vn.generate_sql(
                    question=question_en,
                    allow_llm_to_see_data=self.allow_llm_to_see_data,
                    workspace=workspace
                )

            # ────────────────────────────────────────────────
            # Unpack result – support both old & new return styles
            # ────────────────────────────────────────────────
            if isinstance(sql_result, tuple) and len(sql_result) == 5:
                sql, total_tokens, input_tokens, output_tokens, model_name = sql_result
            elif isinstance(sql_result, tuple) and len(sql_result) == 2:
                sql, total_tokens = sql_result
                input_tokens = output_tokens = 0
                model_name = "unknown"
            else:
                sql = str(sql_result)
                total_tokens = input_tokens = output_tokens = 0
                model_name = "unknown"

            logger.info(f"Generated SQL:\n{sql}", extra={"admin": True})
            logger.info(f"Generated SQL (user-visible)", extra={"user": True})

            # ────────────────────────────────────────────────
            # Cache – store both original and translated question
            # ────────────────────────────────────────────────
            self.cache.set(id=cache_id, field="question",           value=original_question)
            self.cache.set(id=cache_id, field="translated_question", value=question_en)
            self.cache.set(id=cache_id, field="sql",                value=sql)
            self.cache.set(id=cache_id, field="workspace",          value=workspace)
            self.cache.set(id=cache_id, field="detected_language",  value=detected_language)
            self.cache.set(id=cache_id, field="was_translated",     value=was_translated)

            # Token-related fields (for UI/debugging/billing)
            self.cache.set(id=cache_id, field="token_total",   value=total_tokens)
            self.cache.set(id=cache_id, field="token_input",   value=input_tokens)
            self.cache.set(id=cache_id, field="token_output",  value=output_tokens)
            self.cache.set(id=cache_id, field="model_name",    value=model_name)

            logger.info(
                f"Tokens | id:{cache_id} | total={total_tokens} in={input_tokens} out={output_tokens} model={model_name}",
                extra={"token_count": True}
            )

            # ────────────────────────────────────────────────
            # Billing + usage logging
            # ────────────────────────────────────────────────
            cost_usd = None
            try:
                cost_usd = self.log_token_count(
                    question_id=cache_id,
                    total_tokens=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    cached_input_tokens=0,          # can be improved later
                    user_id=session.get('user_id')
                )
            except Exception as e:
                logger.error(f"Billing calculation failed: {e}")

            try:
                self.log_user_activity(
                    question_id=cache_id,
                    question=original_question,
                    sql_query=sql,
                    workspace_name=workspace,
                    user_role=session.get('username', None),
                    user_id=session.get('user_id', None),
                    token_count=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    cached_input_tokens=0,
                    cost_usd=cost_usd,
                    detected_language=detected_language
                )
            except Exception as e:
                logger.error(f"User activity logging failed: {e}")

            # ────────────────────────────────────────────────
            # Response
            # ────────────────────────────────────────────────
            # Extract SQL text if tuple
            sql_text = sql[0] if isinstance(sql, tuple) else sql

            response_type = "sql" if vn.is_sql_valid(sql=sql_text) else "text"

            return jsonify({
                "type":               response_type,
                "id":                 cache_id,
                "text":               sql_text,   # send only SQL string
                "original_question":  original_question,
                "detected_language":  detected_language,
                "was_translated":     was_translated,
                "translated_question": question_en if was_translated else None,
            })

        @self.flask_app.route("/api/get_user/<username>", methods=["GET"])
        @self.requires_auth
        def get_user_config(user: any, username: str):
            """
            Get the user configuration including enabled agent scenarios.
            """
            # Security check: ensure requesting user matches username or is admin
            current_user = user # from requires_auth
            if current_user.get("username") != username and current_user.get("role") != "admin":
                 return jsonify({"type": "error", "error": "Unauthorized access to user config"}), 403

            agent_config = []
            
            # Attempt to fetch from Auth's ChromaDB collection if available
            if hasattr(self.auth, 'users_collection'):
                try:
                    results = self.auth.users_collection.get(where={"username": username}, limit=1)
                    if results.get("metadatas"):
                        user_record = results["metadatas"][0]
                        # agent_config is stored as a stringified list or list in metadata
                        config_raw = user_record.get("agent_config", "[]")
                        logger.info(f"get_user_config raw data for {username}: {config_raw}")
                        
                        if isinstance(config_raw, str):
                            try:
                                agent_config = json.loads(config_raw)
                            except:
                                logger.error(f"Failed to parse agent_config for {username}: {config_raw}")
                                agent_config = []
                        elif isinstance(config_raw, list):
                            agent_config = config_raw
                    else:
                        logger.warning(f"get_user_config: User {username} not found in ChromaDB")

                except Exception as e:
                    logger.error(f"Error fetching user config from ChromaDB: {e}")

            logger.info(f"Returning config for {username}: {agent_config}")
            return jsonify({
                "username": username,
                "agent_config": agent_config,
                "role": current_user.get("role"),
                "workspace": current_user.get("workspace")
            })

        @self.flask_app.route("/api/v0/run_agent_query", methods=["GET"])
        @self.requires_auth
        def run_agent_query(user: any):
            """
            Run a specific agent scenario query.
            """
            scenario_id = flask.request.args.get("scenario_id")
            workspace = flask.request.args.get("workspace") # Optional, might use user's workspace
            
            logger.info(f"run_agent_query called for scenario_id: {scenario_id}")

            if not scenario_id:
                return jsonify({"type": "error", "error": "No scenario_id provided"}), 400

            # Resolve target_workspace_id reliably (Session -> Request Arg -> User default)
            target_workspace_id = flask.session.get('workspace_id')
            if not target_workspace_id:
                 workspace_name = workspace or (user.get('workspace') if isinstance(user, dict) else None)
                 
                 if workspace_name:
                     logger.info(f"run_agent_query: Resolving workspace ID for '{workspace_name}'")
                     try: 
                        results = self.workspace_collection.get()
                        if results and results.get("metadatas"):
                            ids = results.get("ids", [])
                            metadatas = results.get("metadatas", [])
                            for i, meta in enumerate(metadatas):
                                if meta.get("name") == workspace_name:
                                    target_workspace_id = ids[i]
                                    logger.info(f"run_agent_query: Resolved target_workspace_id to {target_workspace_id}")
                                    break
                     except Exception as e:
                        logger.error(f"run_agent_query: Error resolving workspace name: {e}")

            # Auto-connect logic
            if not hasattr(self, 'vn') or self.vn is None:
                logger.info("run_agent_query: self.vn is None. Attempting auto-initialization...")
                
                # internal helper to get workspace_id from session/args
                user_id = flask.session.get('user_id')
                
                if target_workspace_id:
                    logger.info(f"run_agent_query: initializing with workspace_id {target_workspace_id}")
                    success, err = self.ensure_vanna_initialized(target_workspace_id)
                    if not success:
                        logger.error(f"run_agent_query: Auto-init failed: {err}")
                        return jsonify({"type": "error", "error": f"Auto-init failed: {err}"}), 500
                else:
                    logger.error("run_agent_query: Could not determine workspace_id for auto-init")
                    return jsonify({"type": "error", "error": "Vanna not initialized and no workspace_id found"}), 500

            # Map frontend keys to backend keys
            MAPPING = {
                "sku_missing": "S1_MISSING_ITEM_MASTER",
                "qty_shortage": "S2_ORDER_QTY_EXCEEDS_STOCK",
                "zero_before_pick": "S3_INVENTORY_DEPLETED_DURING_PICK",
                "pick_task_fail": "S4_PICK_TASK_NOT_CREATED",
                "lost_during_pick": "S5_INVENTORY_CONSUMED_BY_OTHER_ORDER",
                "status_unusable": "S6_INVENTORY_NOT_AVAILABLE_STATUS",
                "cycle_zero": "S7_CYCLE_COUNT_ADJUSTED_TO_ZERO",
                "system_physical_mismatch": "S8_SYSTEM_PHYSICAL_MISMATCH",
                "expired_inventory": "S9_EXPIRED_INVENTORY",
                "inbound_missing": "S10_ITEM_NOT_RECEIVED",
                "manual_adjustment": "S11_MANUAL_INVENTORY_ADJUSTMENT"
            }

            backend_key = MAPPING.get(scenario_id)
            if not backend_key:
                 return jsonify({"type": "error", "error": f"Invalid scenario_id: {scenario_id}"}), 400

            # --- DYNAMIC SQL OVERRIDE ---
            # Try to get custom SQL from ChromaDB if available for this workspace
            custom_sql = None
            if target_workspace_id:
                try:
                    import json
                    # get_workspace_metadata is a local helper defined in this scope
                    workspace_meta = get_workspace_metadata(self, target_workspace_id)
                    if workspace_meta:
                        agent_config_raw = workspace_meta.get("agent_config_stockout", "{}")
                        agent_config = json.loads(agent_config_raw)
                        logger.info(f"run_agent_query: Found agent_config_stockout for ws {target_workspace_id}")
                        
                        # Root 'enabled' check for the stockout agent
                        if agent_config.get("enabled"):
                            scenarios = agent_config.get("scenarios", [])
                            logger.info(f"run_agent_query: Iterating through {len(scenarios)} scenarios for {scenario_id}")
                            for s in scenarios:
                                # DEBUG: Log scenario IDs found
                                # logger.info(f"run_agent_query: checking scenario s_id={s.get('id')} vs req={scenario_id}")
                                
                                # Match by frontend scenario_id and ensure it's enabled with a custom query
                                if s.get("id") == scenario_id and s.get("enabled") and s.get("sql"):
                                    custom_sql = s.get("sql")
                                    logger.info(f"run_agent_query: OVERRIDING with custom SQL for {scenario_id}")
                                    break
                        else:
                            logger.info(f"run_agent_query: agent_config_stockout is DISABLED for ws {target_workspace_id}")
                except Exception as e:
                    logger.error(f"run_agent_query: Error fetching custom SQL for {scenario_id}: {e}")

            # Fetch SQL from custom override or fall back to SCENARIO_SQL_MAP
            sql = custom_sql if custom_sql else SCENARIO_SQL_MAP.get(backend_key)
            
            if not custom_sql:
                logger.info(f"run_agent_query: Using FALLBACK SQL for {scenario_id}")
            
            if not sql:
                return jsonify({"type": "error", "error": f"No SQL definition for scenario: {backend_key}"}), 500

            try:
                # Execute SQL
                # Use self.vn instance
                if not hasattr(self, 'vn') or self.vn is None:
                     logger.error(f"run_agent_query: self.vn is None. Vanna not initialized/connected.")
                     return jsonify({"type": "error", "error": "Vanna not initialized (self.vn is None)"}), 500
                     
                df = self.vn.run_sql(sql=sql)
                
                # Cache the dataframe for generate_insight
                self.scenario_cache[scenario_id] = df
                
                if df is None or df.empty:
                     return jsonify({
                         "df": [], 
                         "columns": [], 
                         "chart_data": {"labels": [], "values": []},
                         "kpis": {"alert_count": 0, "resource_count": 0, "risk_score": 0},
                         "message": "No data returned"
                     })

                # --- 1. Calculate Universal KPIs ---
                total_alerts = int(len(df))
                
                # Identify columns for identification (Try to rotate between Item/SKU/Order for variety)
                keys = df.columns.tolist()
                keys_lower = [k.lower() for k in keys]
                
                if 'item_number' in keys_lower:
                    resource_col = keys[keys_lower.index('item_number')]
                elif 'sku' in keys_lower:
                    resource_col = keys[keys_lower.index('sku')]
                elif 'order_number' in keys_lower:
                    resource_col = keys[keys_lower.index('order_number')]
                else:
                    resource_col = next((k for k in keys if any(x in k.lower() for x in ['item', 'sku', 'order', 'number'])), keys[0] if keys else "Resource")
                
                impacted_resources = int(df[resource_col].nunique()) if (keys and resource_col in df.columns) else total_alerts
                
                # Dynamic Execution Risk: Heuristic based on record density or volume
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                shortage_col = next((k for k in numeric_cols if any(x in k.lower() for x in ['short', 'required', 'ordered'])), None)
                
                try:
                    if shortage_col:
                        val = df[shortage_col].sum()
                        execution_risk = int(val) if pd.notnull(val) else int(total_alerts * 0.85)
                    else:
                        execution_risk = int(total_alerts * 0.85)
                except:
                    execution_risk = int(total_alerts * 0.85)

                # --- 2. Chart Aggregation & Type Suggestion ---
                top_10 = df[resource_col].value_counts().head(10) if (keys and resource_col in df.columns) else pd.Series()
                chart_labels = [str(x) for x in top_10.index.tolist()]
                chart_values = [float(x) if pd.notnull(x) else 0 for x in top_10.values.tolist()]
                
                # Enhanced Chart Rotation for Visual Diversity
                cardinality = len(chart_labels)
                # Use a string-based rotation to ensure distinct types for adjacent scenarios
                rotation = ['bar', 'pie', 'doughnut', 'polarArea', 'line']
                type_index = sum(ord(c) for c in (scenario_id or "")) % len(rotation)
                
                if cardinality > 0 and cardinality < 4:
                    preferred_type = 'pie'
                elif cardinality >= 4 and cardinality < 7:
                    preferred_type = 'doughnut'
                else:
                    # High variety for the most common ranges
                    preferred_type = rotation[type_index]
                    # Ensure we don't pick pie/doughnut for high cardinality if the hash hits them
                    if cardinality > 10 and preferred_type in ['pie', 'doughnut']:
                         preferred_type = 'bar'

                logger.info(f"run_agent_query: {scenario_id} -> Label: {resource_col}, Type: {preferred_type}")

                # --- 3. Limit Data Preview for Table ---
                data_preview = df.head(200).to_dict(orient='records')
                columns = df.columns.tolist()

                # Robust serialization for JSON
                for row in data_preview:
                    for k, v in row.items():
                        if pd.isnull(v):
                            row[k] = None
                        elif isinstance(v, (pd.Timestamp, datetime)):
                             row[k] = str(v)
                        elif isinstance(v, (np.integer, np.floating)):
                             row[k] = v.item()

                # Suggest scenario-specific labels for KPIs
                kpi_labels = {
                    "alert_count": "Total Alerts",
                    "resource_count": "Impacted Resources", 
                    "risk_score": "Execution Risk"
                }
                
                if "shortage" in (scenario_id or "").lower():
                    kpi_labels["resource_count"] = "Units Short"
                elif "expired" in (scenario_id or "").lower():
                    kpi_labels["resource_count"] = "Expired Batches"

                return jsonify({
                    "df": data_preview,
                    "columns": columns,
                    "chart_data": {
                        "labels": chart_labels,
                        "values": chart_values,
                        "label_key": resource_col,
                        "preferred_type": preferred_type
                    },
                    "kpis": {
                        "alert_count": total_alerts,
                        "resource_count": impacted_resources,
                        "risk_score": execution_risk,
                        "labels": kpi_labels
                    },
                    "scenario_id": scenario_id,
                    "backend_key": backend_key
                })

            except Exception as e:
                logger.error(f"Error running agent query {backend_key}: {e}", exc_info=True)
                return jsonify({"type": "error", "error": str(e)}), 500

        @self.flask_app.route("/api/v0/download_agent_data", methods=["GET"])
        @self.requires_auth
        def download_agent_data(user: any):
            """
            Export full dataset for a scenario as CSV.
            """
            scenario_id = flask.request.args.get("scenario_id")
            if not scenario_id:
                return jsonify({"type": "error", "error": "No scenario_id provided"}), 400

            try:
                # 1. Get Data (Check cache first to avoid re-running expensive SQL)
                if scenario_id in self.scenario_cache:
                    df = self.scenario_cache[scenario_id]
                else:
                    # Map frontend keys to backend keys
                    MAPPING = {
                        "sku_missing": "S1_MISSING_ITEM_MASTER",
                        "qty_shortage": "S2_ORDER_QTY_EXCEEDS_STOCK",
                        "zero_before_pick": "S3_INVENTORY_DEPLETED_DURING_PICK",
                        "pick_task_fail": "S4_PICK_TASK_NOT_CREATED",
                        "lost_during_pick": "S5_INVENTORY_CONSUMED_BY_OTHER_ORDER",
                        "status_unusable": "S6_INVENTORY_NOT_AVAILABLE_STATUS",
                        "cycle_zero": "S7_CYCLE_COUNT_ADJUSTED_TO_ZERO",
                        "system_physical_mismatch": "S8_SYSTEM_PHYSICAL_MISMATCH",
                        "expired_inventory": "S9_EXPIRED_INVENTORY",
                        "inbound_missing": "S10_ITEM_NOT_RECEIVED",
                        "manual_adjustment": "S11_MANUAL_INVENTORY_ADJUSTMENT"
                    }
                    backend_key = MAPPING.get(scenario_id)
                    if not backend_key:
                        return jsonify({"type": "error", "error": f"Invalid scenario_id: {scenario_id}"}), 400
                    
                    # Resolve target_workspace_id reliably (Session -> User default)
                    target_workspace_id = flask.session.get('workspace_id')
                    if not target_workspace_id:
                         workspace_name = (user.get('workspace') if isinstance(user, dict) else None)
                         if workspace_name:
                             try: 
                                results = self.workspace_collection.get()
                                if results and results.get("metadatas"):
                                    ids = results.get("ids", [])
                                    metadatas = results.get("metadatas", [])
                                    for i, meta in enumerate(metadatas):
                                        if meta.get("name") == workspace_name:
                                            target_workspace_id = ids[i]
                                            break
                             except Exception: pass

                    # --- DYNAMIC SQL OVERRIDE (Download) ---
                    custom_sql = None
                    if target_workspace_id:
                        try:
                            import json
                            workspace_meta = get_workspace_metadata(self, target_workspace_id)
                            if workspace_meta:
                                agent_config_raw = workspace_meta.get("agent_config_stockout", "{}")
                                agent_config = json.loads(agent_config_raw)
                                if agent_config.get("enabled"):
                                    scenarios = agent_config.get("scenarios", [])
                                    for s in scenarios:
                                        if s.get("id") == scenario_id and s.get("enabled") and s.get("sql"):
                                            custom_sql = s.get("sql")
                                            logger.info(f"download_agent_data: Using custom SQL for {scenario_id}")
                                            break
                        except Exception: pass

                    sql = custom_sql if custom_sql else SCENARIO_SQL_MAP.get(backend_key)
                    df = self.vn.run_sql(sql=sql)

                if df is None or df.empty:
                    return jsonify({"type": "error", "error": "No data available for export"}), 404

                # 2. Convert to CSV using StringIO for memory efficiency
                output = io.StringIO()
                df.to_csv(output, index=False, encoding='utf-8-sig') # Use utf-8-sig for Excel compatibility
                
                response = make_response(output.getvalue())
                filename = f"WAI_Agent_{scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                response.headers["Content-Disposition"] = f"attachment; filename={filename}"
                response.headers["Content-type"] = "text/csv"
                
                return response

            except Exception as e:
                logger.error(f"Error exporting agent data: {e}", exc_info=True)
                return jsonify({"type": "error", "error": str(e)}), 500


        @self.flask_app.route("/api/v0/generate_insight", methods=["GET"])
        @self.requires_auth
        def generate_insight(user: any):
            """
            Generate a natural language insight for a specific agent scenario.
            Handles large datasets by summarizing before sending to LLM.
            """
            scenario_id = flask.request.args.get("scenario_id")
            workspace = flask.request.args.get("workspace")
            
            if not scenario_id:
                return jsonify({"type": "error", "error": "No scenario_id provided"}), 400

            # Resolve target_workspace_id reliably (Session -> Request Arg -> User default)
            target_workspace_id = flask.session.get('workspace_id')
            if not target_workspace_id:
                 workspace_name = workspace or (user.get('workspace') if isinstance(user, dict) else None)
                 if workspace_name:
                     try: 
                        results = self.workspace_collection.get()
                        if results and results.get("metadatas"):
                            ids = results.get("ids", [])
                            metadatas = results.get("metadatas", [])
                            for i, meta in enumerate(metadatas):
                                if meta.get("name") == workspace_name:
                                    target_workspace_id = ids[i]
                                    break
                     except Exception: pass

            # --- Auto-connect Logic (Reused) ---
            if not hasattr(self, 'vn') or self.vn is None:
                user_id = flask.session.get('user_id')
                if target_workspace_id:
                    self.ensure_vanna_initialized(target_workspace_id)
            
            if not hasattr(self, 'vn') or self.vn is None:
                 return jsonify({"type": "error", "error": "Vanna not initialized"}), 500
            # -----------------------------------

            # Map frontend keys to backend keys (Copy of logic from run_agent_query)
            MAPPING = {
                "sku_missing": "S1_MISSING_ITEM_MASTER",
                "qty_shortage": "S2_ORDER_QTY_EXCEEDS_STOCK",
                "zero_before_pick": "S3_INVENTORY_DEPLETED_DURING_PICK",
                "pick_task_fail": "S4_PICK_TASK_NOT_CREATED",
                "lost_during_pick": "S5_INVENTORY_CONSUMED_BY_OTHER_ORDER",
                "status_unusable": "S6_INVENTORY_NOT_AVAILABLE_STATUS",
                "cycle_zero": "S7_CYCLE_COUNT_ADJUSTED_TO_ZERO",
                "system_physical_mismatch": "S8_SYSTEM_PHYSICAL_MISMATCH",
                "expired_inventory": "S9_EXPIRED_INVENTORY",
                "inbound_missing": "S10_ITEM_NOT_RECEIVED",
                "manual_adjustment": "S11_MANUAL_INVENTORY_ADJUSTMENT"
            }

            backend_key = MAPPING.get(scenario_id)
            if not backend_key:
                 return jsonify({"type": "error", "error": f"Invalid scenario_id: {scenario_id}"}), 400

            # --- DYNAMIC SQL OVERRIDE (Insight) ---
            custom_sql = None
            if target_workspace_id:
                try:
                    import json
                    workspace_meta = get_workspace_metadata(self, target_workspace_id)
                    if workspace_meta:
                        agent_config_raw = workspace_meta.get("agent_config_stockout", "{}")
                        agent_config = json.loads(agent_config_raw)
                        if agent_config.get("enabled"):
                            scenarios = agent_config.get("scenarios", [])
                            for s in scenarios:
                                if s.get("id") == scenario_id and s.get("enabled") and s.get("sql"):
                                    custom_sql = s.get("sql")
                                    break
                except Exception: pass

            sql = custom_sql if custom_sql else SCENARIO_SQL_MAP.get(backend_key)
            
            if not sql:
                return jsonify({"type": "error", "error": f"No SQL definition for scenario: {backend_key}"}), 500

            try:
                # 1. Get Data (Check cache first)
                if scenario_id in self.scenario_cache:
                    logger.info(f"generate_insight: Using cached df for {scenario_id}")
                    df = self.scenario_cache[scenario_id]
                else:
                    logger.info(f"generate_insight: Cache miss for {scenario_id}, running SQL")
                    df = self.vn.run_sql(sql=sql)
                
                if df is None or df.empty:
                    return jsonify({"insight": "No data available to analyze."})

                # 2. Smart Summarization for Large Datasets
                total_records = len(df)
                summary_text = ""
                
                # Identify keys (Label vs Value)
                keys = df.columns.tolist()
                label_key = next((k for k in keys if df[k].dtype == 'object'), keys[0])
                value_key = next((k for k in keys if pd.api.types.is_numeric_dtype(df[k]) and k != label_key), None)
                if not value_key:
                     value_key = next((k for k in keys if k != label_key), keys[0])

                if total_records > 50:
                    # Advanced Statistical Profiling
                    unique_labels = df[label_key].nunique()
                    summary_text = f"**Data Profile (High Accuracy Analysis):**\n"
                    summary_text += f"- Scope: {total_records} total records involving {unique_labels} unique '{label_key}' items.\n"

                    if value_key and pd.api.types.is_numeric_dtype(df[value_key]):
                        # Numeric Distribution & Pareto Analysis
                        total_val = df[value_key].sum()
                        avg_val = df[value_key].mean()
                        median_val = df[value_key].median()
                        max_val = df[value_key].max()
                        
                        summary_text += f"- Total Impact ({value_key}): {total_val:,.2f}\n"
                        summary_text += f"- Distribution: Average={avg_val:.2f}, Median={median_val:.2f}, Max={max_val:.2f}\n"
                        
                        # Concentration Analysis (Pareto Principle)
                        top_n = min(10, len(df))
                        top_n_df = df.nlargest(top_n, value_key)
                        top_n_sum = top_n_df[value_key].sum()
                        concentration_pct = (top_n_sum / total_val) * 100 if total_val > 0 else 0
                        
                        summary_text += f"- Concentration: The top {top_n} items account for {concentration_pct:.1f}% of the total '{value_key}'.\n"
                        summary_text += f"- Top {top_n} Critical Items:\n{top_n_df[[label_key, value_key]].to_markdown(index=False)}\n"
                    else:
                        # Categorical Frequency Analysis
                        top_counts = df[label_key].value_counts()
                        top_item = top_counts.index[0] if len(top_counts) > 0 else "N/A"
                        top_count = top_counts.iloc[0] if len(top_counts) > 0 else 0
                        share_pct = (top_count / total_records) * 100 if total_records > 0 else 0
                        
                        summary_text += f"- Most Frequent: '{top_item}' appears {top_count} times ({share_pct:.1f}% of all records).\n"
                        summary_text += f"- Top 10 Most Frequent:\n{top_counts.head(10).to_markdown()}\n"
                else:
                    # Small dataset: Send full data
                    summary_text = f"Full Data Table:\n{df.to_markdown(index=False)}"

                # 3. Prompt Construction
                system_msg = "You are an expert Data Analyst for Supply Chain. You analyze statistical profiles of warehouse data. Your goal is to provide a SINGLE, PRECISE, 100% FACTUAL insight. Use the provided concentration metrics (e.g., 'Top 10 items account for 80%') to determine if the issue is systemic or localized."
                user_msg = f"Analyze this data profile for scenario '{scenario_id}'.\n{summary_text}\n\nProvide ONE concise sentence starting with 'Insight:'. Be specific with numbers."
                
                messages = [
                    self.vn.system_message(system_msg),
                    self.vn.user_message(user_msg)
                ]

                # 4. LLM Generation
                insight = self.vn.submit_prompt(messages)
                
                # Handle tuple return (content, usage, ...) from OpenAI_Chat
                if isinstance(insight, tuple):
                    insight = insight[0]

                # Cleanup response (remove 'Insight:' prefix if present)
                if insight:
                    cleaned_insight = insight.replace("Insight:", "").strip()
                else:
                    cleaned_insight = "Analysis complete, but no insight generated."
                
                return jsonify({"insight": cleaned_insight})

            except Exception as e:
                logger.error(f"Error generating insight: {e}")
                return jsonify({"type": "error", "error": str(e)}), 500


        # @self.flask_app.route("/api/v0/generate_sql", methods=["GET"])
        # @self.requires_auth
        # def generate_sql(user: any):
        #     """
        #     Generate SQL from a question with optional previous SQL context.
        #     Auto-detects language and translates to English for LLM.
        #     """

        #     question = flask.request.args.get("question")
        #     previous_sql = flask.request.args.get("sql")
        #     workspace = flask.request.args.get("workspace")

        #     # -------------------------------
        #     # Validation
        #     # -------------------------------
        #     if not question:
        #         return jsonify({"type": "error", "error": "No question provided"}), 400

        #     if not workspace:
        #         return jsonify({"type": "error", "error": "No workspace provided"}), 400

        #     question = clean_question(question)

        #     # -------------------------------
        #     # Language Detection + Translation
        #     # -------------------------------
        #     translation_result = translate_question_if_needed(question)

        #     original_question = translation_result["original"]
        #     question_en = translation_result["translated"]
        #     detected_language = translation_result["language"]
        #     was_translated = translation_result["was_translated"]

        #     # -------------------------------
        #     # Logging (same structure as Program 1)
        #     # -------------------------------
        #     logger.info(
        #         f"Question (EN): '{question_en}', Previous SQL: '{previous_sql}', Workspace: '{workspace}'",
        #         extra={"admin": True}
        #     )
        #     logger.info(
        #         f"Question (original): '{original_question}', Previous SQL: '{previous_sql}', Workspace: '{workspace}'",
        #         extra={"user": True}
        #     )

        #     if was_translated:
        #         logger.info(
        #             f"Translated from {detected_language}: '{original_question}' → '{question_en}'",
        #             extra={"user": True}
        #         )

        #     # -------------------------------
        #     # SQL Generation
        #     # -------------------------------
        #     if previous_sql and str(previous_sql).lower() != "null":
        #         logger.info("inside generate sql IF condition", extra={"followup": True})

        #         id = self.cache.generate_id(question=previous_sql)
        #         sql = vn.generate_sql(
        #             question=previous_sql,
        #             followup_sql=question_en,
        #             allow_llm_to_see_data=self.allow_llm_to_see_data,
        #             workspace=workspace
        #         )
        #     else:
        #         logger.info("inside generate sql ELSE condition", extra={"followup": True})

        #         id = self.cache.generate_id(question=question_en)
        #         sql = vn.generate_sql(
        #             question=question_en,
        #             allow_llm_to_see_data=self.allow_llm_to_see_data,
        #             workspace=workspace
        #         )

        #     logger.info(f"SQL Query: {sql}", extra={"admin": True})
        #     logger.info(f"SQL Query: {sql}", extra={"user": True})

        #     # -------------------------------
        #     # Cache (DB-safe multilingual metadata)
        #     # -------------------------------
        #     self.cache.set(id=id, field="question", value=original_question)
        #     self.cache.set(id=id, field="translated_question", value=question_en)
        #     self.cache.set(id=id, field="sql", value=sql)
        #     self.cache.set(id=id, field="workspace", value=workspace)
        #     self.cache.set(id=id, field="language", value=detected_language)
        #     self.cache.set(id=id, field="was_translated", value=was_translated)

        #     # -------------------------------
        #     # RBA + DB PUSH (FROM PROGRAM 1)
        #     # -------------------------------
        #     user_role = session.get("username", None)
        #     user_id = session.get("user_id", None)

        #     self.log_user_activity(
        #         question_id=id,
        #         question=original_question,
        #         sql_query=sql,
        #         workspace_name=workspace,
        #         user_role=user_role,
        #         user_id=user_id,
        #         detected_language=detected_language
        #     )

        #     # -------------------------------
        #     # Response
        #     # -------------------------------
        #     response_payload = {
        #         "type": "sql" if vn.is_sql_valid(sql) else "text",
        #         "id": id,
        #         "text": sql,
        #         "original_question": original_question,
        #         "detected_language": detected_language,
        #         "was_translated": was_translated
        #     }

        #     return jsonify(response_payload)

            
            #################################################################################

        @self.flask_app.route("/api/v0/generate_rewritten_question", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(required_fields=[], optional_fields=["sql", "question"])  
        def generate_rewritten_question(user: any, sql: str = None, question: str = None, id: str = None):

            """
            Generate a rewritten question
            ---
            parameters:
              - name: last_question
                in: query
                type: string
                required: true
              - name: new_question
                in: query
                type: string
                required: true
            """

            last_question = flask.request.args.get("last_question")
            new_question = flask.request.args.get("new_question")
            workspace = flask.request.args.get("workspace")
            logger.info(f"workspace fetched from generate_rewritten {workspace}", extra={"admin": True})

            logger.info(f"inside rewritten in init file SQL: {sql}, Question: {question}", extra={"followup": True})
            logger.info(f"Request Args: {flask.request.args}", extra={"followup": True})
            parsed = sqlparse.parse(sql)[0]
            table_names = []
            for token in parsed.tokens:
                if isinstance(token, sqlparse.sql.Identifier) and 'FROM' not in str(token).upper() and 'JOIN' not in str(token).upper():
                    table_name = str(token).split(' ')[0].strip()
                    table_names.append(table_name)
                elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ['FROM', 'JOIN']:
                    next_token = parsed.token_next(parsed.token_index(token))
                    if next_token and isinstance(next_token, sqlparse.sql.Identifier):
                        table_name = str(next_token).split(' ')[0].strip()
                        table_names.append(table_name)
            table_names = list(dict.fromkeys(table_names))  # Remove duplicates
            if not table_names:
                table_names = ["Unknown table"]

            # Step 2: Fetch schema
            schema = {}
            if "Unknown table" not in table_names:
                # Fetch schema for all tables in table_names using vn.run_sql
                for table in table_names:
                    # Example schema query (adjust based on your DB system, e.g., INFORMATION_SCHEMA for SQL Server/MySQL)
                    schema_query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
                    schema_df = vn.run_sql(schema_query)  # Assuming this returns a DataFrame
                    if not schema_df.empty:
                        schema[table] = dict(zip(schema_df['COLUMN_NAME'], schema_df['DATA_TYPE']))
                    else:
                        schema[table] = "Schema unavailable probably this is not a table"
            logger.info(f"last question {last_question}, new quesiton {new_question}, sql {sql}", extra={"followup": True})
            logger.info(f"Last question: {last_question}, New quesiton: {new_question}, Sql: {sql}", extra={"admin": True})
            rewritten_question = vn.generate_rewritten_question(last_question, new_question,sql,schema, workspace=workspace)
            # Look for content within ```sql_schema``` first
            sql_schema_match = re.search(r'```sql_schema\s*(.*?)\s*```', rewritten_question, re.DOTALL)
            if sql_schema_match:
                rewritten_question = f"'''rewritten'''\n{sql_schema_match.group(1).strip()}\n'''rewritten'''"
            
            # If no ```sql_schema```, look for ```sql```
            sql_match = re.search(r'```sql\s*(.*?)\s*```', rewritten_question, re.DOTALL)
            if sql_match:
                rewritten_question = f"'''rewritten'''\n{sql_match.group(1).strip()}\n'''rewritten'''"
            logger.info(f"rewritten_question returned {rewritten_question}", extra={"admin": True})

            logger.info(f"'type': 'rewritten_question', 'question':{rewritten_question}, 'new': {new_question}", extra={"followup": True})
            return jsonify({"type": "rewritten_question", "question":rewritten_question, "new": new_question})

        @self.flask_app.route("/api/v0/get_function", methods=["GET"])
        @self.requires_auth
        def get_function(user: any):
            """
            Get a function from a question
            ---
            parameters:
              - name: user
                in: query
              - name: question
                in: query
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: function
                    id:
                      type: object
                    function:
                      type: string
            """
            question = flask.request.args.get("question")

            if question is None:
                return jsonify({"type": "error", "error": "No question provided"})

            if not hasattr(vn, "get_function"):
                return jsonify({"type": "error", "error": "This setup does not support function generation."})

            id = self.cache.generate_id(question=question)
            function = vn.get_function(question=question)

            if function is None:
                return jsonify({"type": "error", "error": "No function found"})

            if 'instantiated_sql' not in function:
                self.vn.log(f"No instantiated SQL found for {question} in {function}")
                return jsonify({"type": "error", "error": "No instantiated SQL found"})

            self.cache.set(id=id, field="question", value=question)
            self.cache.set(id=id, field="sql", value=function['instantiated_sql'])

            if 'instantiated_post_processing_code' in function and function['instantiated_post_processing_code'] is not None and len(function['instantiated_post_processing_code']) > 0:
                self.cache.set(id=id, field="plotly_code", value=function['instantiated_post_processing_code'])

            return jsonify(
                {
                    "type": "function",
                    "id": id,
                    "function": function,
                }
            )

        @self.flask_app.route("/api/v0/get_all_functions", methods=["GET"])
        @self.requires_auth
        def get_all_functions(user: any):
            """
            Get all the functions
            ---
            parameters:
              - name: user
                in: query
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: functions
                    functions:
                      type: array
            """
            if not hasattr(vn, "get_all_functions"):
                return jsonify({"type": "error", "error": "This setup does not support function generation."})

            functions = vn.get_all_functions()

            return jsonify(
                {
                    "type": "functions",
                    "functions": functions,
                }
            )
        @self.flask_app.route("/api/v0/deliverytimeprediction", methods=["GET"])
        #@self.requires_auth
        #@self.requires_cache(["sql"])
        def run_sql_2():
            try:
                if not vn.run_sql_is_set:
                    return jsonify(
                        {
                            "type": "error",
                            "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                        }
                    )
                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="SELECT * FROM t_tychons_load_master")
                logger.info(f"df Response for run_sql_2:\n{df}")

                # Step 2: Data Preprocessing for Delivery Time Prediction
                df['delivery_time'] = (pd.to_datetime(df['must_arive_by_date']) - pd.to_datetime(df['routing_date'])).dt.days
                df['pickup_weekday'] = pd.to_datetime(df['pickup_date']).dt.weekday
                df['expected_weekday'] = pd.to_datetime(df['expected_ship_date']).dt.weekday
                
                # Select features for delivery time prediction
                delivery_features = ['total_weight', 'num_pallets', 'pickup_weekday', 'expected_weekday']
                delivery_data = df[delivery_features]

                # Step 3: Use Predefined Model for Delivery Time Prediction
                delivery_model_coef = np.array([0.5, -0.2, 1.0, -0.5])  # Example coefficients
                delivery_model_intercept = 2.5  # Example intercept

                # Make delivery time predictions
                df['predicted_delivery_time'] = np.dot(delivery_data, delivery_model_coef) + delivery_model_intercept

                # Step 4: Data Preprocessing for Shipment Delay Prediction
                delay_features = ['total_weight', 'num_pallets', 'pickup_weekday', 'expected_weekday', 'delivery_time']
                delay_data = df[delay_features]

                # Use Predefined Model for Shipment Delay Prediction
                delay_model_coef = np.array([0.3, 0.1, -0.2, 0.4, 0.8])  # Example coefficients
                delay_model_intercept = -1.2  # Example intercept

                # Logistic function for probability
                def sigmoid(x):
                    return 1 / (1 + np.exp(-x))
                
                delay_logits = np.dot(delay_data, delay_model_coef) + delay_model_intercept
                df['predicted_shipment_delay_prob'] = sigmoid(delay_logits)
                df['predicted_shipment_delay'] = (df['predicted_shipment_delay_prob'] > 0.5).astype(int)

                # Optional: Prepare a subset for better readability in response
                response_df = df[[
                    "bol_number", "created_date", 
                    "expected_ship_date", "expected_weekday", "load_id", "load_master_id", 
                    "must_arive_by_date", "num_pallets", "pallet_type", "payment_terms", "pickup_date", 
                    "pickup_weekday", "predicted_delivery_time", "pro_number", "routing_date", 
                    "ship_to_city", "ship_to_name", "spl_instructions", 
                     "total_weight" 
                ]]
                filtered_df = response_df[response_df["predicted_delivery_time"] <= 100.00]  # Filter rows
                next_10_df = filtered_df.iloc[:10]  # Select first 10 rows

                logger.info(f"prediction Response run_sql_2: {response_df}")
                # Step 5: Cache and Return the Response
                #self.cache.set(field="df", value=df)
                return jsonify(
                    {
                       "df": next_10_df.head(10).replace({np.nan: "NULL"}).to_dict(orient='records')
                    }
                )
            except Exception as e:
                return jsonify({"type": "sql_error", "error": str(e)})

        @self.flask_app.route("/api/v0/shipmentdelayprediction", methods=["GET"])
        #@self.requires_auth
        #@self.requires_cache(["sql"])
        def shipmentdelayprediction():
            try:
                if not vn.run_sql_is_set:
                    return jsonify(
                        {
                            "type": "error",
                            "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                        }
                    )
                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="SELECT * FROM t_tychons_load_master")
                logger.info(f"df Response for run_sql_2:\n{df}")

                # Step 2: Data Preprocessing for Delivery Time Prediction
                df['delivery_time'] = (pd.to_datetime(df['must_arive_by_date']) - pd.to_datetime(df['routing_date'])).dt.days
                df['pickup_weekday'] = pd.to_datetime(df['pickup_date']).dt.weekday
                df['expected_weekday'] = pd.to_datetime(df['expected_ship_date']).dt.weekday
                
                # Select features for delivery time prediction
                delivery_features = ['total_weight', 'num_pallets', 'pickup_weekday', 'expected_weekday']
                delivery_data = df[delivery_features]

                # Step 3: Use Predefined Model for Delivery Time Prediction
                delivery_model_coef = np.array([0.5, -0.2, 1.0, -0.5])  # Example coefficients
                delivery_model_intercept = 2.5  # Example intercept

                # Make delivery time predictions
                df['predicted_delivery_time'] = np.dot(delivery_data, delivery_model_coef) + delivery_model_intercept

                # Step 4: Data Preprocessing for Shipment Delay Prediction
                delay_features = ['total_weight', 'num_pallets', 'pickup_weekday', 'expected_weekday', 'delivery_time']
                delay_data = df[delay_features]

                # Use Predefined Model for Shipment Delay Prediction
                delay_model_coef = np.array([0.3, 0.1, -0.2, 0.4, 0.8])  # Example coefficients
                delay_model_intercept = -1.2  # Example intercept

                # Logistic function for probability
                def sigmoid(x):
                    return 1 / (1 + np.exp(-x))
                
                delay_logits = np.dot(delay_data, delay_model_coef) + delay_model_intercept
                df['predicted_shipment_delay_prob'] = sigmoid(delay_logits).round(4)
                df['predicted_shipment_delay'] = (df['predicted_shipment_delay_prob'] > 0.5).astype(int)

                # Optional: Prepare a subset for better readability in response
                response_df = df[[
                    "total_weight", "num_pallets", "pickup_weekday", 
                    "load_id", "carrier_code", "client_code", "pickup_date", "expected_ship_date", "must_arive_by_date", 
                      "predicted_shipment_delay", "predicted_shipment_delay_prob"
                ]].head(10)
                logger.info(f"prediction Response run_sql_2: {response_df}")
                
                # Step 5: Cache and Return the Response
                #self.cache.set(field="df", value=df)
                return jsonify(
                    {
                       "df": response_df.head(10).replace({np.nan: "NULL"}).to_dict(orient='records')
                    }
                )
            except Exception as e:
                return jsonify({"type": "sql_error", "error": str(e)})


        @self.flask_app.route("/api/v0/jobforecasting", methods=["GET"])
        #@self.requires_auth
        #@self.requires_cache(["sql"])
        def run_sql_3():
          try:
              if not vn.run_sql_is_set:
                  return jsonify(
                      {
                          "type": "error",
                          "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                      }
                  )

              # Step 1: Fetch data from the database
              df = vn.run_sql(sql="SELECT [id], [sp_name], [archival_date], [job_start], [job_end], [comments] FROM [tychons_DB].[dbo].[t_tychons_archive_log]")
              logger.info(f"df Response for run_sql_3:\n{df}")

              # Step 2: Data Preprocessing for Job Duration Prediction
              # Parse the 'job_start' and 'job_end' columns as datetime
              df['job_start'] = pd.to_datetime(df['job_start'])
              df['job_end'] = pd.to_datetime(df['job_end'])

              # Calculate job duration in days
              df['job_duration'] = (df['job_end'] - df['job_start']).dt.days

              # Step 3: Predict Job Duration (Example Model)
              # For simplicity, using average duration as prediction for now
              avg_duration = df['job_duration'].mean()
              df['predicted_job_duration'] = avg_duration

              # Step 4: Predict Job Status (Based on Comments, Example: Whether the Job is Ended or Started)
              df['predicted_job_status'] = df['comments'].apply(lambda x: 'Ended' if 'Ended' in str(x) else 'In Progress')

              # Optional: Prepare a subset for better readability in response
              response_df = df[['id', 'sp_name', 'job_start', 'job_end', 'comments', 'job_duration', 'predicted_job_duration', 'predicted_job_status']].head(10)
              logger.info(f"prediction Response run_sql_3: {response_df}")

              # Step 5: Return the Response
              return jsonify(
                  {
                      "df": df.tail(10).replace({np.nan: "NULL"}).to_dict(orient='records')
                  }
              )
          except Exception as e:
              return jsonify({"type": "sql_error", "error": str(e)})
          
        @self.flask_app.route("/api/v0/inventorydemandforecasting", methods=["GET"])
        def run_sql_4():
            try:
                if not vn.run_sql_is_set:
                    return jsonify(
                        {
                            "type": "error",
                            "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                        }
                    )

                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="""
                    SELECT 
                        [description], 
                        [item_number], 
                        [std_hand_qty], 
                        [reorder_point], 
                        [reorder_qty], 
                        [cycle_count_class], 
                        [product_category] 
                    FROM [tychons_DB].[dbo].[t_item_master] WHERE [reorder_qty] != 0 and [product_category] IS NOT NULL
                """)

                # Step 2: Handle missing or null values
                df = df.fillna({'reorder_qty': 0})  # Replace null reorder quantities with 0
                df['reorder_qty'] = pd.to_numeric(df['reorder_qty'], errors='coerce')  # Ensure numeric type for calculations

                # Step 3: Group by item_number and calculate the average reorder_qty
                demand_forecast = df.groupby('product_category')['reorder_qty'].mean().reset_index()
                demand_forecast.rename(columns={'reorder_qty': 'predicted_demand'}, inplace=True)

                # Step 4: Merge the predicted demand back into the original dataframe
                df = df.merge(demand_forecast, on='product_category', how='left')

                # Step 5: Prepare response data (returning the last 10 rows for now)
                df["predicted_demand"] = df["predicted_demand"].round()

                response_df = df[['description', 'product_category', 'std_hand_qty', 'reorder_qty', 'predicted_demand']]
                unique_categories_df = response_df.drop_duplicates(subset=["product_category"]).iloc[:10]



                # Replace NaN values with "NULL" for the JSON response
                return jsonify({"df": unique_categories_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

            except Exception as e:
                logger.error(f"Error in inventory demand prediction: {str(e)}")
                return jsonify({"type": "sql_error", "error": str(e)})


        # @self.flask_app.route("/api/v0/stockoutprediction", methods=["GET"])
        # def run_sql_5():
        #     try:
        #         if not vn.run_sql_is_set:
        #             return jsonify({"type": "error", "error": "Database connection required."})

        #         # Step 1: Fetch data from the database
        #         df = vn.run_sql(sql="SELECT TOP 1000 [item_master_id], [item_number], [std_hand_qty], [reorder_point], [reorder_qty], [last_count_date], [inventory_type] FROM [tychons_DB].[dbo].[t_item_master]")
                
        #         # Step 2: Stockout Prediction Logic (e.g., predict if stock will be less than reorder point)
        #         df['predicted_stockout'] = df['std_hand_qty'] < df['reorder_point']
                
        #         # Step 3: Return the top 10 prediction results
        #         response_df = df[['item_master_id', 'item_number', 'std_hand_qty', 'reorder_point', 'predicted_stockout']].head(10)
                
        #         return jsonify({"df": response_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

        #     except Exception as e:
        #         return jsonify({"type": "sql_error", "error": str(e)})


        @self.flask_app.route("/api/v0/stockoutprediction", methods=["GET"])
        def run_stockout_prediction():
            try:
                if not self.vn.run_sql_is_set:
                    return jsonify({"type": "error", "error": "Database connection required."})

                # Fetch inventory data from the database
                df = self.vn.run_sql(sql="""
                    SELECT  
                        [item_number], 
                        [actual_qty], 
                        [fifo_date] 
                    FROM [tychons_DB].[dbo].[t_stored_item] 
                    WHERE [actual_qty] > 0;
                """)
                
                # Convert fifo_date to datetime
                df['fifo_date'] = pd.to_datetime(df['fifo_date'])
                
                # Estimate depletion rates (assuming FIFO, older stock is used first)
                df['days_in_stock'] = (pd.Timestamp.today() - df['fifo_date']).dt.days
                df = df[df['days_in_stock'] > 0]
                df['depletion_rate'] = df['actual_qty'] / df['days_in_stock']
                
                # Calculate stockout prediction in days
                avg_depletion_df = df.groupby('item_number', as_index=False)['depletion_rate'].mean()
                inventory_df = df.groupby('item_number', as_index=False)['actual_qty'].sum()
                
                stockout_df = inventory_df.merge(avg_depletion_df, on='item_number')
                stockout_df['stockout_days'] = (stockout_df['actual_qty'] / stockout_df['depletion_rate']).round(2)
                
                # Merge with descriptions
                desc_df = self.vn.run_sql(sql="""
                    SELECT DISTINCT item_number, description FROM [tychons_DB].[dbo].[t_stored_item]
                """)
                stockout_df = stockout_df.merge(desc_df, on='item_number')[['item_number', 'description', 'actual_qty', 'stockout_days']]
                
                # Return top 10 items with the highest stockout risk (earliest depletion)
                stockout_df = stockout_df.nsmallest(10, 'stockout_days')
                #stockout_df = df[['item_number', 'description', 'actual_qty', 'stockout_days']].head(10)
                
                return jsonify({"df": stockout_df.replace({np.nan: "NULL"}).to_dict(orient='records')})
            
            except Exception as e:
                logger.error(f"Error in run_sql_3: {str(e)}")
                return jsonify({"type": "sql_error", "error": str(e)})

        @self.flask_app.route("/api/v0/pricetrendprediciton", methods=["GET"])
        def run_sql_7():
            try:
                if not vn.run_sql_is_set:
                    return jsonify({"type": "error", "error": "Database connection required."})

                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="""
                    SELECT  
                        [item_number], 
                        [description], 
                        [price] 
                    FROM [tychons_DB].[dbo].[t_stored_item] 
                    WHERE [price] != 0;
                """)

                inflation_rate = 0.03

                # Step 2: Calculate average price per item_number
                avg_price_df = df.groupby('item_number', as_index=False)['price'].mean()
                avg_price_df['predicted_price'] = (avg_price_df['price'] * (1 + inflation_rate)).round(2)

                # Step 3: Merge with original dataframe to include descriptions
                merged_df = df[['item_number', 'description']].drop_duplicates()
                response_df = avg_price_df.merge(merged_df, on='item_number')[['description', 'price', 'predicted_price']]

                # Step 4: Return the top 10 predicted results
                response_df = response_df.head(10)

                return jsonify({"df": response_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

            except Exception as e:
                return jsonify({"type": "sql_error", "error": str(e)})



        # @self.flask_app.route("/api/v0/pricetrendprediciton", methods=["GET"])
        # def run_sql_7():
        #     try:
        #         if not vn.run_sql_is_set:
        #             return jsonify({"type": "error", "error": "Database connection required."})

        #         # Step 1: Fetch data from the database
        #         df = vn.run_sql(sql="""
        #             SELECT TOP 1000 
        #                 [item_number], 
        #                 [price] 
        #             FROM [tychons_DB].[dbo].[t_stored_item] 
        #             WHERE [price] != 0;
        #         """)

        #         inflation_rate = 0.03

        #         # Step 2: Price Prediction Logic (Use mean price adjusted for inflation)
        #         df['predicted_price'] = df['price'].mean() * (1 + inflation_rate)

        #         # Step 3: Return the top 10 predicted results
        #         response_df = df[['item_number', 'price', 'predicted_price']].head(10)

        #         return jsonify({"df": response_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

        #     except Exception as e:
        #         return jsonify({"type": "sql_error", "error": str(e)})



        @self.flask_app.route("/api/v0/orderfulfillmenttimeprediction", methods=["GET"])
        # @self.requires_auth
        # @self.requires_cache(["sql"])
        def orderfulfillmenttimeprediction():
          try:
              if not vn.run_sql_is_set:
                  return jsonify(
                      {
                          "type": "error",
                          "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                      }
                  )
              
              # Step 1: Fetch only relevant columns from the database
              query = """
              SELECT TOP 1000 order_detail_id, qty, bo_qty, item_weight, picking_flow, date_expected 
              FROM t_order_detail
              """
              df = vn.run_sql(sql=query)

              # Step 2: Handle missing or null values in the fetched data
              if df.isnull().any().any():
                  logger.warning("Some columns have missing values. Handling missing data...")
                  df = df.fillna({
                      'qty': 0,
                      'bo_qty': 0,
                      'item_weight': 0,
                      'picking_flow': 'Unknown',  # Assuming 'picking_flow' is categorical
                      'date_expected': pd.to_datetime('today')  # Filling with current date
                  })
              
              logger.info(f"df Response for run_sql_3:\n{df}")

              # Step 3: Data Preprocessing for Order Fulfillment Time Prediction
              # Convert 'date_expected' to datetime if it's not already
              df['date_expected'] = pd.to_datetime(df['date_expected'], errors='coerce')
              if df['date_expected'].isnull().any():
                  logger.error("Some 'date_expected' values are invalid or missing. Aborting.")
                  return jsonify({"type": "error", "error": "'date_expected' contains invalid or missing values."})

              # Add a 'pickup_weekday' feature for prediction (based on 'date_expected')
              df['pickup_weekday'] = df['date_expected'].dt.weekday
              
              # Step 4: Convert the columns to numeric values
              # Convert 'qty', 'bo_qty', 'item_weight' to numeric if they are not already
              df['qty'] = pd.to_numeric(df['qty'], errors='coerce')
              df['bo_qty'] = pd.to_numeric(df['bo_qty'], errors='coerce')
              df['item_weight'] = pd.to_numeric(df['item_weight'], errors='coerce')

              # Encode 'picking_flow' as numeric (e.g., using label encoding)
              df['picking_flow'] = df['picking_flow'].astype('category').cat.codes
              
              # Calculate the fulfillment time (dummy calculation for example)
              df['fulfillment_time'] = (df['date_expected'] - pd.to_datetime(df['date_expected'])).dt.days
              
              # Step 5: Select only relevant features for the prediction model
              fulfillment_features = ['qty', 'bo_qty', 'item_weight', 'pickup_weekday', 'picking_flow']
              fulfillment_data = df[fulfillment_features]

              # Step 6: Check for any non-numeric columns
              if not np.issubdtype(fulfillment_data.dtypes.iloc[0], np.number):
                  logger.error("Non-numeric data found in prediction features.")
                  return jsonify({"type": "error", "error": "Prediction features contain non-numeric data."})

              # Check if features match expected shape before prediction
              if fulfillment_data.shape[1] != 5:
                  logger.error("Feature selection mismatch. Expected 5 features.")
                  return jsonify({"type": "error", "error": "Feature mismatch in the prediction model."})

              # Step 7: Use Predefined Model for Order Fulfillment Time Prediction (using example coefficients)
              fulfillment_model_coef = np.array([0.4, -0.1, 0.8, -0.3, 0.2])  # Example coefficients
              fulfillment_model_intercept = 1.0  # Example intercept
              #fulfillment_model_coef = np.array([0.02, -0.02, 0.08, -0.05, 0.012])  # Halved impact
              #fulfillment_model_intercept = 0.06  # Halved intercept





              # Predict order fulfillment time (in days)
              df['predicted_fulfillment_time'] = (np.dot(fulfillment_data, fulfillment_model_coef) + fulfillment_model_intercept).round()


              # Step 8: Optional - Predict order delays (using a logistic model for binary outcome)
              delay_features = ['qty', 'bo_qty', 'item_weight', 'pickup_weekday', 'picking_flow', 'predicted_fulfillment_time']
              delay_data = df[delay_features]

              # Logistic Regression Coefficients for Delay Prediction (Example)
              #delay_model_coef = np.array([0.3, 0.2, -0.4, 0.5, 0.1, 0.7])  # Example coefficients
              delay_model_coef = np.array([0.2, 0., -0.4, 0.5, 0.1, 0.7])  # Example coefficients
              delay_model_intercept = -1.0  # Example intercept

              # Logistic function for probability
              def sigmoid(x):
                  return 1 / (1 + np.exp(-x))
              
              delay_logits = np.dot(delay_data, delay_model_coef) + delay_model_intercept
              df['predicted_order_delay_prob'] = sigmoid(delay_logits)
              df['predicted_order_delay'] = (df['predicted_order_delay_prob'] > 0.5).astype(int)

              # Optional: Prepare a subset for better readability in the response
              response_df = df[['bo_qty', 'item_weight', 'order_detail_id', 
                                'picking_flow', 'pickup_weekday',  'predicted_fulfillment_time', 'qty'
                              ]]
                      # Step 5: Filter alternating predictions of 0 and 1
              '''delay_0_df = df[df['predicted_order_delay'] == 0].head(5)
              delay_1_df = df[df['predicted_order_delay'] == 1].head(5)
              response_df = pd.concat([delay_0_df, delay_1_df]).sort_index()'''
              filtered_df = response_df[response_df["predicted_fulfillment_time"] >= 100.00]  # Filter rows
              next_10_df = filtered_df.iloc[:10]  # Select first 10 rows
              logger.info(f"prediction Response run_sql_3: {response_df}")

              # Step 9: Return the Response
              return jsonify(
                  {
                      "df": next_10_df.head(10).replace({np.nan: "NULL"}).to_dict(orient='records')
                  }
              )
          except Exception as e:
              logger.error(f"Error in run_sql_3: {str(e)}")
              return jsonify({"type": "sql_error", "error": str(e)})
        @self.flask_app.route("/api/v0/orderdelayprediction", methods=["GET"])
        def orderdelayprediction():
          try:
              if not vn.run_sql_is_set:
                  return jsonify(
                      {
                          "type": "error",
                          "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                      }
                  )
              
              # Step 1: Fetch only relevant columns from the database
              query = """
              SELECT TOP 1000 order_detail_id, qty, bo_qty, item_weight, picking_flow, date_expected 
              FROM t_order_detail
              """
              df = vn.run_sql(sql=query)
              
              # Step 2: Handle missing or null values in the fetched data
              if df.isnull().any().any():
                  logger.warning("Some columns have missing values. Handling missing data...")
                  df = df.fillna({
                      'qty': 0,
                      'bo_qty': 0,
                      'item_weight': 0,
                      'picking_flow': 'Unknown',  # Assuming 'picking_flow' is categorical
                      'date_expected': pd.to_datetime('today')  # Filling with current date
                  })
              
              logger.info(f"df Response for run_sql_3:\n{df}")

              # Step 3: Data Preprocessing for Order Fulfillment Time Prediction
              # Convert 'date_expected' to datetime if it's not already
              df['date_expected'] = pd.to_datetime(df['date_expected'], errors='coerce')
              if df['date_expected'].isnull().any():
                  logger.error("Some 'date_expected' values are invalid or missing. Aborting.")
                  return jsonify({"type": "error", "error": "'date_expected' contains invalid or missing values."})

              # Add a 'pickup_weekday' feature for prediction (based on 'date_expected')
              df['pickup_weekday'] = df['date_expected'].dt.weekday
              
              # Step 4: Convert the columns to numeric values
              # Convert 'qty', 'bo_qty', 'item_weight' to numeric if they are not already
              df['qty'] = pd.to_numeric(df['qty'], errors='coerce')
              df['bo_qty'] = pd.to_numeric(df['bo_qty'], errors='coerce')
              df['item_weight'] = pd.to_numeric(df['item_weight'], errors='coerce')

              # Encode 'picking_flow' as numeric (e.g., using label encoding)
              df['picking_flow'] = df['picking_flow'].astype('category').cat.codes
              
              # Calculate the fulfillment time (dummy calculation for example)
              df['fulfillment_time'] = (df['date_expected'] - pd.to_datetime(df['date_expected'])).dt.days
              
              # Step 5: Select only relevant features for the prediction model
              fulfillment_features = ['qty', 'bo_qty', 'item_weight', 'pickup_weekday', 'picking_flow']
              fulfillment_data = df[fulfillment_features]

              # Step 6: Check for any non-numeric columns
              if not np.issubdtype(fulfillment_data.dtypes[0], np.number):
                  logger.error("Non-numeric data found in prediction features.")
                  return jsonify({"type": "error", "error": "Prediction features contain non-numeric data."})

              # Check if features match expected shape before prediction
              if fulfillment_data.shape[1] != 5:
                  logger.error("Feature selection mismatch. Expected 5 features.")
                  return jsonify({"type": "error", "error": "Feature mismatch in the prediction model."})

              # Step 7: Use Predefined Model for Order Fulfillment Time Prediction (using example coefficients)
              fulfillment_model_coef = np.array([0.4, -0.1, 0.8, -0.3, 0.2])  # Example coefficients
              fulfillment_model_intercept = 1.5  # Example intercept

              # Predict order fulfillment time (in days)
              df['predicted_fulfillment_time'] = np.dot(fulfillment_data, fulfillment_model_coef) + fulfillment_model_intercept
              
              # Step 8: Optional - Predict order delays (using a logistic model for binary outcome)
              delay_features = ['qty', 'bo_qty', 'item_weight', 'pickup_weekday', 'picking_flow', 'predicted_fulfillment_time']
              delay_data = df[delay_features]

              # Logistic Regression Coefficients for Delay Prediction (Example)
              delay_model_coef = np.array([0.3, 0.2, -0.4, 0.5, 0.1, 0.7])  # Example coefficients
              delay_model_intercept = -1.0  # Example intercept

              # Logistic function for probability
              def sigmoid(x):
                  return 1 / (1 + np.exp(-x))
              
              delay_logits = np.dot(delay_data, delay_model_coef) + delay_model_intercept
              df['predicted_order_delay_prob'] = sigmoid(delay_logits)
              df['predicted_order_delay'] = (df['predicted_order_delay_prob'] > 0.5).astype(int)

              # Optional: Prepare a subset for better readability in the response
              response_df = df[['bo_qty', 'date_expected', 'item_weight', 'order_detail_id', 'picking_flow', 'pickup_weekday', 
                                'predicted_order_delay', 'predicted_order_delay_prob','qty']].head(10)
              logger.info(f"prediction Response run_sql_3: {response_df}")

              # Step 9: Return the Response
              return jsonify(
                  {
                      "df": response_df.head(10).replace({np.nan: "NULL"}).to_dict(orient='records')
                  }
              )
          except Exception as e:
              logger.error(f"Error in run_sql_3: {str(e)}")
              return jsonify({"type": "sql_error", "error": str(e)})
        @self.flask_app.route("/api/v0/employeeperformanceprediction", methods=["GET"])
        def run_sql_employee_performance():
            try:
                if not vn.run_sql_is_set:
                    return jsonify({"type": "error", "error": "Database connection required."})

                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="""
                    SELECT [employee_id], [emp_number], [function_code], [dept], [status], 
                                    [region_number], [work_shift], [goal_time_flag]
                    FROM [tychons_DB].[dbo].[t_employee]
                    WHERE [status] = 'A'
                """)

                # Step 2: Performance Prediction Logic (Use goal time flag as a proxy)
                df['predicted_performance_score'] = df['goal_time_flag'].apply(lambda x: 1 if x == 'Y' else 0)

                # Step 3: Return the top 10 results
                response_df = df[['employee_id', 'emp_number', 'dept', 'predicted_performance_score']].head(10)
                
                return jsonify({"df": response_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

            except Exception as e:
                logger.error(f"Error in run_sql_3: {str(e)}")
                return jsonify({"type": "sql_error", "error": str(e)})


        # API 2: Task Completion Time Prediction
        @self.flask_app.route("/api/v0/taskcompletionprediction", methods=["GET"])
        def run_sql_task_completion():
            try:
                if not vn.run_sql_is_set:
                    return jsonify({"type": "error", "error": "Database connection required."})

                # Step 1: Fetch data from the database
                df = vn.run_sql(sql="""
                    SELECT TOP 1000 [employee_id], [work_shift], [hours_into_future], 
                                    [last_tran_start_datetime], [last_tran_end_datetime]
                    FROM [tychons_DB].[dbo].[t_employee]
                    WHERE [last_tran_start_datetime] IS NOT NULL AND [last_tran_end_datetime] IS NOT NULL
                """)

                # Step 2: Convert datetime columns to proper format and handle errors
                df['last_tran_start_datetime'] = pd.to_datetime(df['last_tran_start_datetime'], errors='coerce')
                df['last_tran_end_datetime'] = pd.to_datetime(df['last_tran_end_datetime'], errors='coerce')

                # Drop rows where datetime conversion failed
                df = df.dropna(subset=['last_tran_start_datetime', 'last_tran_end_datetime'])

                # Calculate task duration, ensuring no negative values
                df['task_duration'] = (df['last_tran_end_datetime'] - df['last_tran_start_datetime']).dt.total_seconds() / 3600
                df['task_duration'] = df['task_duration'].apply(lambda x: max(0, x))  # Ensure no negative values

                # Step 3: Predict using mean task duration
                df['predicted_task_completion_time'] = df['task_duration'].mean()

                # Step 4: Return the top 10 results
                response_df = df[['employee_id', 'task_duration', 'predicted_task_completion_time']].head(10)
                
                return jsonify({"df": response_df.replace({np.nan: "NULL"}).to_dict(orient='records')})

            except Exception as e:
                return jsonify({"type": "sql_error", "error": str(e)})

        @self.flask_app.route("/api/v0/anomalydetection", methods=["GET"])
        def anomaly_detection():
            try:
                # Step 1: Fetch data from the database
                query = """
                    SELECT TOP 1000 std_hand_qty, price, unit_weight, tare_weight, wh_id, client_code
                    FROM t_item_master
                    WHERE std_hand_qty IS NOT NULL AND std_hand_qty <> 0;
                """
                df = vn.run_sql(sql=query)

                if df.empty:
                    logger.warning("No data fetched from the database.")
                    return jsonify({"type": "warning", "message": "No data available for anomaly detection."})

                # Step 2: Handle missing data (fill missing values with the median)
                numerical_columns = ['std_hand_qty', 'price', 'unit_weight', 'tare_weight']
                for col in numerical_columns:
                    if col in df.columns:
                        df[col] = df[col].fillna(df[col].median())
                        logger.info(f"Filled missing values in {col} with its median.")

                # Step 3: Detect anomalies using Z-score method
                anomalies = []
                threshold = 3  # Z-score threshold for anomaly detection

                for col in numerical_columns:
                    if col in df.columns:
                        mean = df[col].mean()
                        std_dev = df[col].std()
                        df[f'{col}_is_anomalous'] = np.abs((df[col] - mean) / std_dev) > threshold

                # Step 4: Create a response with anomaly details
                for index, row in df.iterrows():
                    unusual_columns = [col for col in numerical_columns if row.get(f'{col}_is_anomalous')]
                    if unusual_columns:
                        anomalies.append({
                            "wh_id": row.get("wh_id"),
                            "client_code": row.get("client_code"),
                            "unusual_columns": unusual_columns,
                            "values": {col: row[col] for col in unusual_columns},
                            "recommendation": f"Check the following fields: {', '.join(unusual_columns)}"
                        })

                logger.info(f"Anomalies detected: {len(anomalies)} records.")
                anomaly_df = pd.DataFrame(anomalies)

                # Step 5: Format response
                response_data = anomaly_df.replace({np.nan: "NULL"}).to_dict(orient='records')
                return jsonify({"status": "success", "anomalies": response_data})

            except Exception as e:
                logger.error(f"Error in anomaly detection: {str(e)}")
                return jsonify({"status": "error", "message": str(e)})

        @self.flask_app.route("/api/v0/run_sql", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["sql"])
        def run_sql(user: any, id: str, sql: str):
            """
            Run SQL
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: df
                    id:
                      type: string
                    df:
                      type: object
                    should_generate_chart:
                      type: boolean
            """
            try:
                if not vn.run_sql_is_set:
                    return jsonify(
                        {
                            "type": "error",
                            "error": "Please connect to a database using vn.connect_to_... in order to run SQL queries.",
                        }
                    )

                df = vn.run_sql(sql=sql)
                # logger.info(f"df Response:\n{df}")
                self.cache.set(id=id, field="df", value=df)
                
                # Prepare predictions dictionary
                predictions = {}
                
                # Prediction block intentionally disabled; this endpoint now only executes SQL and returns data.
                # Keeping this placeholder so legacy prediction logic can be restored later if needed.
                # try:
                #     <legacy prediction logic here>
                # except Exception as pred_error:
                #     logger.exception(f"Prediction stage failed: {pred_error}")
                #     predictions = {"message": "Prediction skipped for this result shape."}
                    
                if df.empty:
                    # Create an empty DataFrame with the same JSON structure
                    df = pd.DataFrame([{"message": "No data available for your request.!"}])
                    df_json = df.head(10).to_json(orient='records', date_format='iso')
                    return jsonify({ "type": "df", "df": df_json })

                # Convert DataFrame to JSON in the correct format before passing to jsonify
                df_json = df.head(10).to_json(orient='records', date_format='iso')

                # Return predictions
                return jsonify(
                    {
                        "type": "df",
                        "id": id,
                        "df": df_json,
                        "should_generate_chart": self.chart and vn.should_generate_chart(df),
                        "predictions": predictions,
                    }
                )
            except TimeoutError as e:
                # Handle query timeout specifically
                user_friendly_message = "Query has been executed for more than 15 sec and the connection has been closed."
                df = pd.DataFrame([{"message": user_friendly_message}])
                df_json = df.head(10).to_json(orient='records', date_format='iso')
                return jsonify({"type": "df", "df": df_json})

            except Exception as e:
                error_message = str(e)
                logger.error(f"SQL Execution Error: {error_message}", exc_info=True, extra={"admin": True})

                # Check for missing column errors (42S22 - Invalid column name)
                column_match = re.findall(r"Invalid column name '([^']+)'", error_message)
                table_match = re.findall(r"Invalid object name '([^']+)'", error_message)
                if column_match:
                    user_friendly_message = f"The query could not be executed because the column '{column_match[0]}' does not exist. Please check your database schema."
                # Check for missing table errors (42S02 - Invalid object name)
                elif table_match:
                    user_friendly_message= f"The query could not be executed because the table '{table_match[0]}' does not exist. Please verify the table name."
                # Fallback: surface the actual database error instead of a generic,
                # unhelpful message that hides what really went wrong. Extract the
                # SQL Server-reported text if present (pyodbc wraps it as
                # "[SQL Server]<message> (<code>) (SQLExecDirectW)"), else show the
                # raw exception text truncated to a safe display length.
                else:
                    sql_server_match = re.search(r"\[SQL Server\](.+?)(?:\s*\(\d+\)\s*\(SQL\w*\)|$)", error_message)
                    detail = sql_server_match.group(1).strip() if sql_server_match else error_message[:300]
                    user_friendly_message = f"The query could not be executed: {detail}"
                df = pd.DataFrame([{"message": user_friendly_message}])
                df_json = df.head(10).to_json(orient='records', date_format='iso')
                return jsonify({ "type": "df", "df": df_json })


        @self.flask_app.route("/api/v0/fix_sql", methods=["POST"])
        @self.requires_auth
        @self.requires_cache(["question", "sql"])
        def fix_sql(user: any, id: str, question: str, sql: str):
            """
            Fix SQL
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
              - name: error
                in: body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: sql
                    id:
                      type: string
                    text:
                      type: string
            """
            error = flask.request.json.get("error")

            if error is None:
                return jsonify({"type": "error", "error": "No error provided"})

            question = f"I have an error: {error}\n\nHere is the SQL I tried to run: {sql}\n\nThis is the question I was trying to answer: {question}\n\nCan you rewrite the SQL to fix the error?"

            fixed_sql = vn.generate_sql(question=question)

            self.cache.set(id=id, field="sql", value=fixed_sql)

            return jsonify(
                {
                    "type": "sql",
                    "id": id,
                    "text": fixed_sql,
                }
            )


        @self.flask_app.route('/api/v0/update_sql', methods=['POST'])
        @self.requires_auth
        @self.requires_cache([])
        def update_sql(user: any, id: str):
            """
            Update SQL
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
              - name: sql
                in: body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: sql
                    id:
                      type: string
                    text:
                      type: string
            """
            sql = flask.request.json.get('sql')

            if sql is None:
                return jsonify({"type": "error", "error": "No sql provided"})

            self.cache.set(id=id, field='sql', value=sql)

            return jsonify(
                {
                    "type": "sql",
                    "id": id,
                    "text": sql,
                })

        @self.flask_app.route("/api/v0/download_csv", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["df"])
        def download_csv(user: any, id: str, df):

            # Reset index to start from 1
            df = df.reset_index(drop=True)
            df.index = df.index + 1

            csv = df.to_csv(index=True)

            return Response(
                csv,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={id}.csv"},
            )
        @self.flask_app.route("/api/v0/generate_plotly_figure", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["df", "question", "sql"])
        def generate_plotly_figure(user: any, id: str, df, question, sql):
            """
            Generate plotly figure
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
              - name: chart_instructions
                in: body
                type: string
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: plotly_figure
                    id:
                      type: string
                    fig:
                      type: object
            """
            chart_instructions = flask.request.args.get('chart_instructions')

            try:
                # If chart_instructions is not set then attempt to retrieve the code from the cache
                if chart_instructions is None or len(chart_instructions) == 0:
                    code = self.cache.get(id=id, field="plotly_code")
                else:
                    question = f"{question}. When generating the chart, use these special instructions: {chart_instructions}"
                    code = vn.generate_plotly_code(
                        question=question,
                        sql=sql,
                        df_metadata=f"Running df.dtypes gives:\n {df.dtypes}",
                    )
                    self.cache.set(id=id, field="plotly_code", value=code)

                fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
                fig_json = fig.to_json()

                self.cache.set(id=id, field="fig_json", value=fig_json)

                return jsonify(
                    {
                        "type": "plotly_figure",
                        "id": id,
                        "fig": fig_json,
                    }
                )
            except Exception as e:
                # Print the stack trace
                import traceback

                traceback.print_exc()

                return jsonify({"type": "error", "error": str(e)})

        @self.flask_app.route("/api/v0/get_training_data", methods=["GET"])
        @self.requires_auth
        def get_training_data(user: any):
            """
            Get all training data
            ---
            parameters:
              - name: user
                in: query
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: df
                    id:
                      type: string
                      default: training_data
                    df:
                      type: object
            """
            df = vn.get_training_data()

            if df is None or len(df) == 0:
                return jsonify(
                    {
                        "type": "error",
                        "error": "No training data found. Please add some training data first.",
                    }
                )

            return jsonify(
                {
                    "type": "df",
                    "id": "training_data",
                    "df": df.to_json(orient="records"),
                }
            )

        @self.flask_app.route("/api/v0/remove_training_data_module", methods=["POST"])
        @self.requires_auth
        def remove_training_data_module(user: any):
            """
            Remove training data from ChromaDB
            """
            data = flask.request.json
            id = data.get("id")
            workspace_name = data.get("workspace_name")

            if not id or not workspace_name:
                return jsonify({"type": "error", "error": "Missing id or workspace name"})

            deleted = vn.remove_training_data_module(id=id, workspace_name=workspace_name)

            if deleted:
                return jsonify({"success": True})
            else:
                return jsonify({"type": "error", "error": "Couldn't remove training data or data not found in DB."})
            
            

        @self.flask_app.route("/api/v0/remove_training_data", methods=["POST"])
        @self.requires_auth
        def remove_training_data(user: any):
            """
            Remove training data
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    success:
                      type: boolean
            """
            # Get id from the JSON body
            id = flask.request.json.get("id")

            if id is None:
                return jsonify({"type": "error", "error": "No id provided"})

            if vn.remove_training_data(id=id):
                return jsonify({"success": True})
            else:
                return jsonify(
                    {"type": "error", "error": "Couldn't remove training data"}
                )

        # @self.flask_app.route("/api/v0/train", methods=["POST"])
        # @self.requires_auth
        # def add_training_data(user: any):
        #     """
        #     Add training data
        #     ---
        #     parameters:
        #       - name: user
        #         in: query
        #       - name: question
        #         in: body
        #         type: string
        #       - name: sql
        #         in: body
        #         type: string
        #       - name: ddl
        #         in: body
        #         type: string
        #       - name: documentation
        #         in: body
        #         type: string
        #     responses:
        #       200:
        #         schema:
        #           type: object
        #           properties:
        #             id:
        #               type: string
        #     """
        #     question = flask.request.json.get("question")
        #     sql = flask.request.json.get("sql")
        #     ddl = flask.request.json.get("ddl")
        #     documentation = flask.request.json.get("documentation")

        #     try:
        #         id = vn.train(
        #             question=question, sql=sql, ddl=ddl, documentation=documentation
        #         )

        #         return jsonify({"id": id})
        #     except Exception as e:
        #         print("TRAINING ERROR", e)
        #         return jsonify({"type": "error", "error": str(e)})

        @self.flask_app.route("/api/v0/create_function", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["question", "sql"])
        def create_function(user: any, id: str, question: str, sql: str):
            """
            Create function
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: function_template
                    id:
                      type: string
                    function_template:
                      type: object
            """
            plotly_code = self.cache.get(id=id, field="plotly_code")

            if plotly_code is None:
                plotly_code = ""

            function_data = self.vn.create_function(question=question, sql=sql, plotly_code=plotly_code)

            return jsonify(
                {
                    "type": "function_template",
                    "id": id,
                    "function_template": function_data,
                }
            )

        @self.flask_app.route("/api/v0/update_function", methods=["POST"])
        @self.requires_auth
        def update_function(user: any):
            """
            Update function
            ---
            parameters:
              - name: user
                in: query
              - name: old_function_name
                in: body
                type: string
                required: true
              - name: updated_function
                in: body
                type: object
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    success:
                      type: boolean
            """
            old_function_name = flask.request.json.get("old_function_name")
            updated_function = flask.request.json.get("updated_function")

            print("old_function_name", old_function_name)
            print("updated_function", updated_function)

            updated = vn.update_function(old_function_name=old_function_name, updated_function=updated_function)

            return jsonify({"success": updated})

        @self.flask_app.route("/api/v0/delete_function", methods=["POST"])
        @self.requires_auth
        def delete_function(user: any):
            """
            Delete function
            ---
            parameters:
              - name: user
                in: query
              - name: function_name
                in: body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    success:
                      type: boolean
            """
            function_name = flask.request.json.get("function_name")

            return jsonify({"success": vn.delete_function(function_name=function_name)})

        @self.flask_app.route("/api/v0/generate_followup_questions", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["df", "question", "sql"])
        def generate_followup_questions(user: any, id: str, df, question, sql):
            """
            Generate followup questions
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: question_list
                    questions:
                      type: array
                      items:
                        type: string
                    header:
                      type: string
            """
            parsed = sqlparse.parse(sql)[0]
            table_names = []
            for token in parsed.tokens:
                if isinstance(token, sqlparse.sql.Identifier) and 'FROM' not in str(token).upper() and 'JOIN' not in str(token).upper():
                    table_name = str(token).split(' ')[0].strip()
                    table_names.append(table_name)
                elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ['FROM', 'JOIN']:
                    next_token = parsed.token_next(parsed.token_index(token))
                    if next_token and isinstance(next_token, sqlparse.sql.Identifier):
                        table_name = str(next_token).split(' ')[0].strip()
                        table_names.append(table_name)
            table_names = list(dict.fromkeys(table_names))  # Remove duplicates
            if not table_names:
                table_names = ["Unknown table"]

            # Step 2: Fetch schema
            schema = {}
            if "Unknown table" not in table_names:
                # Fetch schema for all tables in table_names using vn.run_sql
                for table in table_names:
                    # Example schema query (adjust based on your DB system, e.g., INFORMATION_SCHEMA for SQL Server/MySQL)
                    schema_query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
                    schema_df = vn.run_sql(schema_query)  # Assuming this returns a DataFrame
                    if not schema_df.empty:
                        schema[table] = dict(zip(schema_df['COLUMN_NAME'], schema_df['DATA_TYPE']))
                    else:
                        schema[table] = "Schema unavailable"
            else:
                # Fallback to DataFrame schema if table is unknown
                schema = df.dtypes.to_dict()

            logger.info(f"inside generate follwoup endpoint sql - {sql} tables-{schema}")            
            if self.allow_llm_to_see_data:
                followup_questions = vn.generate_followup_questions(
                    question=question, sql=sql, df=df,schema=schema
                )
                if followup_questions is not None and len(followup_questions) > 5:
                    followup_questions = followup_questions[:5]

                self.cache.set(id=id, field="followup_questions", value=followup_questions)

                return jsonify(
                    {
                        "type": "question_list",
                        "id": id,
                        "questions": followup_questions,
                        "header": "Here are some potential followup questions:",
                    }
                )
            else:
                self.cache.set(id=id, field="followup_questions", value=[])
                return jsonify(
                    {
                        "type": "question_list",
                        "id": id,
                        "questions": [],
                        "header": "Followup Questions can be enabled if you set allow_llm_to_see_data=True",
                    }
                )
    ########################generate summary without translation ##################


        # @self.flask_app.route("/api/v0/generate_summary", methods=["GET"])
        # @self.requires_auth
        # @self.requires_cache(["question", "sql", "df"])
        # def generate_summary(user: any, id: str, df:pd.DataFrame, question, sql):
        #     """
        #     Generate summary
        #     ---
        #     parameters:
        #       - name: user
        #         in: query
        #       - name: id
        #         in: query|body
        #         type: string
        #         required: true
        #     responses:
        #       200:
        #         schema:
        #           type: object
        #           properties:
        #             type:
        #               type: string
        #               default: text
        #             id:
        #               type: string
        #             text:
        #               type: string
        #     """
        #     # Early exit if df is None or empty
        #     workspace = flask.request.args.get("workspace")
        #     user_role = session.get('username', None)
        #     user_id = session.get('user_id', None)
            
        #     logger.info(f"workspace fetched from generate_summary {workspace}")
        #     try:
        #         logger.info(f"inside generate summary endpoint sql - {id} and {df.columns}")
        #     except:
        #         logger.info(f"inside generate summary endpoint sql - {id} and {df}")
           
        #     # Early exit if df is None or empty
        #     if df is None or df.empty:
        #         summary = "No data available to generate a summary."
        #         self.cache.set(id=id, field="summary", value=summary)
               
        #         # Log activity even for no data case
        #         # self._log_complete_user_activity(
        #         #     question=question,
        #         #     sql_query=sql,
        #         #     summary=summary,
        #         #     workspace_name=workspace,
        #         #     user_role=user_role,
        #         #     user_id = user_id,
        #         #     cache_id=id
        #         # )
               
        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": summary
        #         })
                
        #     # Early exit if no data is available
        #     parsed = sqlparse.parse(sql)[0]
        #     table_names = []
        #     for token in parsed.tokens:
        #         if isinstance(token, sqlparse.sql.Identifier) and 'FROM' not in str(token).upper() and 'JOIN' not in str(token).upper():
        #             table_name = str(token).split(' ')[0].strip()
        #             table_names.append(table_name)
        #         elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ['FROM', 'JOIN']:
        #             next_token = parsed.token_next(parsed.token_index(token))
        #             if next_token and isinstance(next_token, sqlparse.sql.Identifier):
        #                 table_name = str(next_token).split(' ')[0].strip()
        #                 table_names.append(table_name)
        #     table_names = list(dict.fromkeys(table_names))  # Remove duplicates
        #     if not table_names:
        #         table_names = ["Unknown table"]

        #     # Step 2: Fetch schema
        #     schema = []
        #     if "Unknown table" not in table_names:
        #         # Fetch schema for all tables in table_names using vn.run_sql
        #         #for table in table_names:
        #         #    # Example schema query (adjust based on your DB system, e.g., INFORMATION_SCHEMA for SQL Server/MySQL)
        #         #    schema_query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
        #         #    schema_df = vn.run_sql(schema_query)  # Assuming this returns a DataFrame
        #         #    if not schema_df.empty:
        #         #        schema[table] = dict(zip(schema_df['COLUMN_NAME'], schema_df['DATA_TYPE']))
        #         #    else:
        #         #        schema[table] = "Schema unavailable"
        #         schema = table_names
        #     else:
        #         # Fallback to DataFrame schema if table is unknown
        #         schema = df.dtypes.to_dict()

        #     logger.info(f"inside generate summary endpoint sql - {sql} tables-{schema}")
        #     if self.allow_llm_to_see_data:
        #         if df is None or df.empty:
        #             logger.info("No data available to generate a summary.")
        #             summary = "No data available to generate a summary."
        #         else:
        #             try:
        #                 summary = vn.generate_summary(question=question, df=df, schema=schema, sql=sql, workspace=workspace)
        #             except Exception as e:
        #                 summary = f"Failed to generate summary: {str(e)}"
        #                 logger.error(f"Error generating summary: {str(e)}")
 
        #         self.cache.set(id=id, field="summary", value=summary)
 
        #         # Log complete user activity with all available data (including plot data)
        #         # self._log_complete_user_activity(
        #         #     question=question,
        #         #     sql_query=sql,
        #         #     summary=summary,
        #         #     workspace_name=workspace,
        #         #     user_role=user_role,
        #         #     user_id = user_id,
        #         #     cache_id=id
        #         # )
 
        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": summary,
        #         })
        #     else:
        #         summary = "Summarization can be enabled if you set allow_llm_to_see_data=True"
               
        #         # Log even when summarization is disabled
        #         # self._log_complete_user_activity(
        #         #     question=question,
        #         #     sql_query=sql,
        #         #     summary=summary,
        #         #     workspace_name=workspace,
        #         #     user_role=user_role,
        #         #     user_id = user_id,
        #         #     cache_id=id
        #         # )        detected_language=detected_language,
               
        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": summary,
        #         })


        def localize_text(self, text: str, cache_id: str) -> str:
            """
            Translate given text into the user's detected language.
            """
            if not text:
                return text

            user_language = self.get_user_language(cache_id)
            return translate_text(text, user_language)
        
        def get_user_language(self, cache_id: str) -> str:
            """
            Returns detected language code stored in cache by /generate_sql.
            Default is English ('en').
            """
            try:
                detected_language = self.cache.get(id=cache_id, field="detected_language")

                if not detected_language or detected_language in ("unknown", "", None):
                    logger.info("No valid language info in cache, defaulting to English")
                    return "en"

                # normalize: "EN" -> "en"
                detected_language = str(detected_language).lower().strip()

                logger.info(f"Retrieved user language: {detected_language}")
                return detected_language

            except Exception as e:
                logger.error(f"Error retrieving language: {str(e)}")
                return "en"



        # @self.flask_app.route("/api/v0/generate_summary", methods=["GET"])
        # @self.requires_auth
        # @self.requires_cache(["question", "sql", "df"])
        # def generate_summary(user: any, id: str, df: pd.DataFrame, question, sql):
        #     """
        #     Generate summary in the same language as the original question.
        #     Works for EN / ES / FR / DE / IT / PT / HI / etc. – anything Google Translate supports.
        #     """
        #     workspace = flask.request.args.get("workspace")

        #     # Get detected language stored earlier (default: English)
        #     detected_language = self.cache.get(id=id, field="detected_language") or "en"
        #     logger.info(f"User language detected for summary: {detected_language}")

        #     # Handle no data scenario early
        #     if df is None or df.empty:
        #         summary_en = "No data available to generate a summary."
        #         summary = translate_text(summary_en, detected_language)

        #         self.cache.set(id=id, field="summary", value=summary)

        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": summary
        #         })

        #     # Extract table names from SQL
        #     parsed = sqlparse.parse(sql)[0]
        #     table_names = []

        #     for token in parsed.tokens:
        #         # Identifier that's not just the word FROM
        #         if isinstance(token, sqlparse.sql.Identifier) and 'FROM' not in str(token).upper():
        #             table_names.append(str(token).split(' ')[0].strip())
        #         # FROM / JOIN then next token is table name
        #         elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ['FROM', 'JOIN']:
        #             next_token = parsed.token_next(parsed.token_index(token))
        #             if next_token and isinstance(next_token, sqlparse.sql.Identifier):
        #                 table_names.append(str(next_token).split(' ')[0].strip())

        #     # Remove duplicates, fallback to df schema if none detected
        #     table_names = list(dict.fromkeys(table_names)) or ["Unknown table"]
        #     schema = table_names if table_names[0] != "Unknown table" else df.dtypes.to_dict()

        #     logger.info(f"Tables detected for summary: {schema}")

        #     # Generate Summary with LLM (in EN)
        #     if self.allow_llm_to_see_data:
        #         try:
        #             summary_en = vn.generate_summary(
        #                 question=question,   # original question (in user language or EN)
        #                 df=df,
        #                 schema=schema,
        #                 sql=sql,
        #                 workspace=workspace
        #             )
        #             logger.info(f"Generated Summary (EN): {summary_en}")
        #         except Exception as e:
        #             summary_en = f"Failed to generate summary: {str(e)}"
        #             logger.error(f"Summary generation error: {str(e)}")
        #     else:
        #         summary_en = "Summarization is disabled. Enable allow_llm_to_see_data=True."

        #     # 🌍 Translate summary to original language (if needed)
        #     summary = translate_text(summary_en, detected_language)

        #     # Cache final text
        #     self.cache.set(id=id, field="summary", value=summary)

        #     return jsonify({
        #         "type": "text",
        #         "id": id,
        #         "text": summary,
        #     })
                        
        # @self.flask_app.route("/api/v0/generate_summary", methods=["GET"])
        # @self.requires_auth
        # @self.requires_cache(["question", "sql", "df"])
        # def generate_summary(user: any, id: str, df: pd.DataFrame, question, sql):
        #     """
        #     Generate summary in the same language as the original user question.
        #     """

        #     workspace = flask.request.args.get("workspace")
        #     user_role = session.get("username", None)
        #     user_id = session.get("user_id", None)

        #     logger.info(f"workspace fetched from generate_summary {workspace}")

        #     # --------------------------------------------------
        #     # Fetch detected language from cache (default: EN)
        #     # --------------------------------------------------
        #     detected_language = self.cache.get(id=id, field="language") or "en"
            

        #     was_translated = self.cache.get(id=id, field="was_translated") or False

        #     logger.info(f"Detected language for summary: {detected_language}")

        #     try:
        #         logger.info(f"generate_summary id={id}, columns={df.columns}")
        #     except Exception:
        #         logger.info(f"generate_summary id={id}, df={df}")

        #     # --------------------------------------------------
        #     # No data scenario
        #     # --------------------------------------------------
        #     if df is None or df.empty:
        #         summary_en = "No data available to generate a summary."
        #         summary = translate_text(summary_en, detected_language)

        #         self.cache.set(id=id, field="summary", value=summary)

        #         return jsonify({
        #             "type": "text",
        #             "id": id,
        #             "text": summary
        #         })

        #     # --------------------------------------------------
        #     # Extract table names from SQL
        #     # --------------------------------------------------
        #     parsed = sqlparse.parse(sql)[0]
        #     table_names = []

        #     for token in parsed.tokens:
        #         if isinstance(token, sqlparse.sql.Identifier) and \
        #         'FROM' not in str(token).upper() and \
        #         'JOIN' not in str(token).upper():
        #             table_names.append(str(token).split(" ")[0].strip())

        #         elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ["FROM", "JOIN"]:
        #             next_token = parsed.token_next(parsed.token_index(token))
        #             if next_token and isinstance(next_token, sqlparse.sql.Identifier):
        #                 table_names.append(str(next_token).split(" ")[0].strip())

        #     table_names = list(dict.fromkeys(table_names)) or ["Unknown table"]

        #     # --------------------------------------------------
        #     # Schema resolution
        #     # --------------------------------------------------
        #     if "Unknown table" not in table_names:
        #         schema = table_names
        #     else:
        #         schema = df.dtypes.to_dict()

        #     logger.info(f"Tables detected for summary: {schema}")

        #     # --------------------------------------------------
        #     # Generate summary (LLM always in EN)
        #     # --------------------------------------------------
        #     if self.allow_llm_to_see_data:
        #         try:
        #             summary_en = vn.generate_summary(
        #                 question=question,  # original user question
        #                 df=df,
        #                 schema=schema,
        #                 sql=sql,
        #                 workspace=workspace
        #             )
        #             logger.info(f"Generated summary (EN): {summary_en}")
        #         except Exception as e:
        #             summary_en = f"Failed to generate summary: {str(e)}"
        #             logger.error(f"Summary generation error: {str(e)}")
        #     else:
        #         summary_en = "Summarization is disabled. Enable allow_llm_to_see_data=True."

        #     # --------------------------------------------------
        #     # Translate summary back to user language
        #     # --------------------------------------------------
        #     summary = translate_text(summary_en, detected_language)

        #     self.cache.set(id=id, field="summary", value=summary)

        #     return jsonify({
        #         "type": "text",
        #         "id": id,
        #         "text": summary,
        #         "detected_language": detected_language,
        #         "was_translated": was_translated
        #     })

        @self.flask_app.route("/api/v0/generate_summary", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(["question", "sql", "df"])
        def generate_summary(user: any, id: str, df: pd.DataFrame, question: str, sql: str):
            """
            Generate natural-language summary of query results.
            - Uses detected language from cache to return summary in user's language
            - LLM always sees English prompt + question
            - Logs tokens & billing
            """
            workspace   = flask.request.args.get("workspace")
            user_id     = session.get('user_id')
            user_role   = session.get('username', None)

            if not workspace:
                return jsonify({"type": "error", "error": "No workspace provided"}), 400

            # ────────────────────────────────────────────────
            # Language info (from cache – authoritative source)
            # ────────────────────────────────────────────────
            detected_language = self.cache.get(id=id, field="detected_language") or "en"
            question_en       = self.cache.get(id=id, field="translated_question") or question

            logger.info(
                f"Summary generation | id={id} | lang={detected_language} | question_en={question_en[:80]}...",
                extra={"admin": True}
            )

            # ────────────────────────────────────────────────
            # Early exit: no data
            # ────────────────────────────────────────────────
            if df is None or df.empty:
                summary_local = "No data available to generate a summary."
                self.cache.set(id=id, field="summary", value=summary_local)

                # Minimal logging for empty case
                try:
                    self.log_user_activity(
                        question_id=id,
                        question=question,
                        sql_query=sql,
                        summary=summary_local,
                        workspace_name=workspace,
                        user_role=user_role,
                        user_id=user_id,
                        detected_language=detected_language
                    )
                except Exception as e:
                    logger.error(f"Activity log failed (empty df): {e}")

                return jsonify({
                    "type": "text",
                    "id": id,
                    "text": summary_local,
                    "detected_language": detected_language
                })

            # ────────────────────────────────────────────────
            # Extract table names (used for schema/context)
            # ────────────────────────────────────────────────
            try:
                parsed = sqlparse.parse(sql)[0]
                table_names = []
                for token in parsed.tokens:
                    if isinstance(token, sqlparse.sql.Identifier) and 'FROM' not in str(token).upper():
                        table_names.append(str(token).split(' ')[0].strip())
                    elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ['FROM', 'JOIN']:
                        next_token = parsed.token_next(parsed.token_index(token))
                        if next_token and isinstance(next_token, sqlparse.sql.Identifier):
                            table_names.append(str(next_token).split(' ')[0].strip())
                table_names = list(dict.fromkeys(table_names)) or ["Unknown table"]

                schema = table_names if table_names[0] != "Unknown table" else df.dtypes.to_dict()
            except Exception:
                schema = df.dtypes.to_dict()
                logger.warning("SQL parsing failed → falling back to dtypes schema", exc_info=True)

            logger.info(f"Schema context for summary: {schema}", extra={"admin": True})

            # ────────────────────────────────────────────────
            # LLM not allowed to see data
            # ────────────────────────────────────────────────
            if not self.allow_llm_to_see_data:
                summary_local = "Summarization is disabled. Enable allow_llm_to_see_data=True."
                self.cache.set(id=id, field="summary", value=summary_local)
                return jsonify({
                    "type": "text",
                    "id": id,
                    "text": summary_local,
                    "detected_language": detected_language
                })

            # ────────────────────────────────────────────────
            # Generate summary (LLM sees English)
            # ────────────────────────────────────────────────
            try:
                summary_en, total_tokens, input_tokens, output_tokens, model_name = vn.generate_summary(
                    question=question_en,           # always English
                    df=df,
                    schema=schema,
                    sql=sql,
                    workspace=workspace
                )
            except Exception as e:
                summary_en = f"Failed to generate summary: {str(e)}"
                total_tokens = input_tokens = output_tokens = 0
                model_name = "error"
                logger.error(f"Summary generation failed: {e}", exc_info=True)

            # ────────────────────────────────────────────────
            # Translate back to user's language
            # ────────────────────────────────────────────────
            summary_local = translate_text(summary_en, detected_language)

            # ────────────────────────────────────────────────
            # Cache everything
            # ────────────────────────────────────────────────
            self.cache.set(id=id, field="summary",           value=summary_local)
            self.cache.set(id=id, field="summary_en",        value=summary_en)         # useful for debugging
            self.cache.set(id=id, field="token_total",       value=total_tokens)
            self.cache.set(id=id, field="token_input",       value=input_tokens)
            self.cache.set(id=id, field="token_output",      value=output_tokens)
            self.cache.set(id=id, field="model_name",        value=model_name)

            logger.info(
                f"Summary tokens | id:{id} | total={total_tokens} in={input_tokens} out={output_tokens} model={model_name}",
                extra={"token_count": True}
            )

            # ────────────────────────────────────────────────
            # Billing
            # ────────────────────────────────────────────────
            cost_usd = None
            try:
                cost_usd = self.log_token_count(
                    question_id=id,
                    total_tokens=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    cached_input_tokens=0,
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Token billing failed: {e}")

            # ────────────────────────────────────────────────
            # Activity logging
            # ────────────────────────────────────────────────
            try:
                self.log_user_activity(
                    question_id=id,
                    question=question,
                    sql_query=sql,
                    summary=summary_local,
                    workspace_name=workspace,
                    user_role=user_role,
                    user_id=user_id,
                    token_count=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    cost_usd=cost_usd,
                    detected_language=detected_language
                )
            except Exception as e:
                logger.error(f"User activity logging failed: {e}")

            # ────────────────────────────────────────────────
            # Response
            # ────────────────────────────────────────────────
            return jsonify({
                "type":              "text",
                "id":                id,
                "text":              summary_local,
                "detected_language": detected_language,
                # optional debug helpers
                "summary_en":        summary_en if detected_language != "en" else None,
            })

        def chromadb_token_logger(
            self,
            workspace_id: str,
            total_tokens: int,
            input_tokens: int,
            output_tokens: int,
            model_name: str,
            suggestion_type: str,
            cached_input_tokens: int = 0,
        ):
            # Existing log (unchanged spirit)
            logger.info(
                f"ChromaDB Workspace ID: {workspace_id} | "
                f"total={total_tokens}, in={input_tokens}, out={output_tokens}, model={model_name}",
                extra={"token_count": True},
            )

            # -----------------------------
            # Validation
            # -----------------------------
            try:
                total_tokens = int(total_tokens)
                input_tokens = int(input_tokens)
                output_tokens = int(output_tokens)
                cached_input_tokens = int(cached_input_tokens)
            except Exception as e:
                logger.error(
                    f"Invalid token values for Workspace ID {workspace_id}: {e}",
                    extra={"token_count": True},
                )
                return

            if total_tokens == 0:
                logger.info(
                    f"No-op token update for Workspace ID: {workspace_id}",
                    extra={"token_count": True},
                )
                return

            # -----------------------------
            # Normalize model
            # -----------------------------
            try:
                normalized_model = self.normalize_model_name(model_name)
            except Exception:
                normalized_model = model_name or "unknown"

            # -----------------------------
            # Pricing table (same as billing)
            # -----------------------------
            MODEL_PRICING = {
                "gpt-4.1": {"input": 5.00, "output": 15.00},
                "gpt-4.1-mini": {"input": 0.60, "output": 2.40},
                "gpt-4.1-preview": {"input": 3.00, "output": 10.00},
                "o3": {"input": 1.00, "output": 3.00},
                "o1": {"input": 6.00, "output": 18.00},
                "o1-preview": {"input": 6.00, "output": 18.00},
                "gpt-5.1": {"input": 1.25, "output": 10.00},
            }

            price_in = MODEL_PRICING.get(normalized_model, {}).get("input", 0.0)
            price_out = MODEL_PRICING.get(normalized_model, {}).get("output", 0.0)

            billable_input = max(0, input_tokens - cached_input_tokens)

            cost_usd = round(
                (billable_input / 1_000_000) * price_in +
                (output_tokens / 1_000_000) * price_out,
                8,
            )

            # -----------------------------
            # Metadata keys
            # -----------------------------
            base = suggestion_type
            keys = {
                "total": f"{base}_total_tokens",
                "input": f"{base}_input_tokens",
                "output": f"{base}_output_tokens",
                "cost": f"{base}_cost_usd",
                "model": f"{base}_model_name",
            }

            id_str = str(workspace_id)

            # Retry parameters (unchanged)
            max_retries = 5
            base_backoff = 0.1

            for attempt in range(1, max_retries + 1):
                try:
                    rec = self.workspace_collection.get(ids=[id_str])
                    curr_meta = (rec.get("metadatas") or [{}])[0] or {}

                    def safe_int(val):
                        try:
                            return int(val)
                        except Exception:
                            return 0

                    def safe_float(val):
                        try:
                            return float(val)
                        except Exception:
                            return 0.0

                    new_meta = dict(curr_meta)
                    new_meta[keys["total"]] = safe_int(curr_meta.get(keys["total"])) + total_tokens
                    new_meta[keys["input"]] = safe_int(curr_meta.get(keys["input"])) + input_tokens
                    new_meta[keys["output"]] = safe_int(curr_meta.get(keys["output"])) + output_tokens
                    new_meta[keys["cost"]] = round(
                        safe_float(curr_meta.get(keys["cost"])) + cost_usd,
                        8,
                    )
                    new_meta[keys["model"]] = normalized_model  # last-used model

                    self.workspace_collection.update(
                        ids=[id_str],
                        metadatas=[new_meta],
                    )

                    # Best-effort verification
                    check = self.workspace_collection.get(ids=[id_str])
                    check_meta = (check.get("metadatas") or [{}])[0] or {}

                    if safe_int(check_meta.get(keys["total"])) < new_meta[keys["total"]]:
                        raise RuntimeError("Post-update verification failed")

                    logger.info(
                        f"[CHROMA BILLING OK] ws={workspace_id} | type={suggestion_type} | "
                        f"model={normalized_model} | in={input_tokens} | out={output_tokens} | "
                        f"total={total_tokens} | cost=${cost_usd:.8f}",
                        extra={"billing": True},
                    )
                    return cost_usd

                except Exception as e:
                    wait = base_backoff * (2 ** (attempt - 1))
                    logger.error(
                        f"Attempt {attempt} error updating Chroma billing for {id_str}: {e}; retrying in {wait:.2f}s",
                        extra={"token_count": True},
                    )
                    if attempt == max_retries:
                        logger.error(
                            f"Failed Chroma billing update for {id_str} after {max_retries} attempts",
                            extra={"token_count": True},
                        )
                        return 0.0
                    try:
                        import time
                        time.sleep(wait)
                    except Exception:
                        continue

###############################################################################################  
        import uuid

        def is_uuid(val: str) -> bool:
            try:
                uuid.UUID(str(val))
                return True
            except Exception:
                return False
      
        def resolve_workspace_id_pr(self, value):

            if not value:
                return None

            value = value.strip()

            # If already UUID → return
            if is_uuid(value):
                return value

            # Else resolve by metadata name
            recs = self.workspace_collection.get(include=["metadatas"])

            ids = recs.get("ids", [])
            metas = recs.get("metadatas", [])

            target = value.lower().replace("_", "-")

            for wid, meta in zip(ids, metas):

                name = (meta.get("name") or "").lower().replace("_", "-")

                if name == target:
                    return wid

            return None

        @self.flask_app.route("/api/v0/get_prediction_suggestions", methods=["GET"])
        @self.requires_auth
        def get_prediction_suggestions(user: any):

            logger.info("[Token count] get_prediction_suggestion", extra={"flow": True})

            from flask import session

            table_name = flask.request.args.get("table_name")
            query = flask.request.args.get("query")
            workspace_name = flask.request.args.get("workspace_name")

            # ✅ MAIN: Get workspace_id from request OR session
            workspace_id = (
                flask.request.args.get("workspace_id")
                or session.get("workspace_id")
            )

            logger.info(
                f"[Prediction] workspace_id={workspace_id}, workspace_name={workspace_name}",
                extra={"token_count": True}
            )

            # ---- Validation ----
            if not workspace_id:
                return jsonify({
                    "type": "error",
                    "error": "No active workspace"
                }), 400

            if not workspace_name or not table_name:
                return jsonify({
                    "type": "error",
                    "error": "Missing workspace_name or table_name"
                }), 400

            try:

                # ---- Call Vanna ----
                (
                    suggestion_raw,
                    token_count,
                    input_tokens,
                    output_tokens,
                    model_name,
                ) = vn.get_prediction_suggestions(
                    table=table_name,
                    user_query=query,
                    workspace=workspace_name,
                )

                logger.info(
                    f"[Prediction] ws={workspace_name} | model={model_name} | "
                    f"in={input_tokens} | out={output_tokens} | total={token_count}",
                    extra={"token_count": True},
                )

                logger.info(f"[Prediction] Raw: {suggestion_raw}")

                # ---- Billing (UUID ONLY) ----
                chromadb_token_logger(
                    self,
                    workspace_id=workspace_id,
                    total_tokens=token_count,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    suggestion_type="prediction",
                )

                # ---- Parse Result ----
                suggestions = []

                try:
                    parsed = json.loads(suggestion_raw)

                    if isinstance(parsed, list):
                        suggestions = parsed
                    elif isinstance(parsed, dict):
                        suggestions = [parsed]
                    else:
                        logger.warning("Unexpected suggestion format")

                except Exception as e:
                    logger.warning(f"Failed to parse suggestion: {e}")

                    return jsonify({
                        "type": "error",
                        "error": "Failed to parse AI response"
                    }), 500

                # ---- Response ----
                return jsonify({
                    "type": "success",
                    "workspace_name": workspace_name,
                    "table_name": table_name,
                    "suggestions": suggestions
                })


            except Exception as e:

                logger.exception("Error generating prediction suggestions")

                return jsonify({
                    "type": "error",
                    "error": str(e)
                }), 500


        @self.flask_app.route("/api/v0/get_anomaly_suggestions", methods=["GET"])
        @self.requires_auth
        def get_anomaly_suggestions(user: any):
            logger.info(f"[Token count] get_anomaly_suggestions", extra={"flow": True})

            
            table_name = flask.request.args.get("table_name")
            query = flask.request.args.get("query")
            workspace = flask.request.args.get("workspace_name")
            raw_ws_id = flask.request.args.get("workspace_id")
            workspace_id = flask.request.args.get("workspace_id")
            # Resolve ID properly
            workspace_id_billing = resolve_workspace_id_pr(self, raw_ws_id or workspace)

            logger.info(f"Workspace id passed: {workspace_id}", extra={"token_count": True})
            logger.info(
                f"[Anomaly Suggestions] Workspace: {workspace}, Table: {table_name}, Query: {query}"
            )

            if not workspace or not table_name:
                return jsonify({"type": "error", "error": "Missing workspace or table_name"}), 400

            try:
                # ---- UPDATED UNPACKING ----
                (
                    suggestion_raw,
                    token_count,
                    input_tokens,
                    output_tokens,
                    model_name,
                ) = vn.get_anomaly_suggestions(
                    table=table_name,
                    user_query=query,
                    workspace=workspace,
                )

                logger.info(
                    f"get_anomaly_suggestions | ws={workspace} | "
                    f"model={model_name} | in={input_tokens} | out={output_tokens} | "
                    f"total={token_count}",
                    extra={"token_count": True},
                )

                logger.info(f"[Anomaly Suggestions] Raw Suggestion: {suggestion_raw}")

                # ---- ChromaDB billing update ----
                chromadb_token_logger(
                    self,
                    workspace_id=workspace_id_billing,
                    total_tokens=token_count,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    suggestion_type="anomaly",
                )

                # ---- Ensure response is always a list for frontend ----
                suggestions = []
                try:
                    parsed = json.loads(suggestion_raw)
                    if isinstance(parsed, list):
                        suggestions = parsed
                    elif isinstance(parsed, dict):
                        suggestions = [parsed]
                    else:
                        logger.warning("Unexpected suggestion format")
                except Exception as e:
                    logger.warning(f"Failed to parse suggestion: {e}")
                    return jsonify({
                        "type": "error",
                        "error": "Failed to parse AI suggestion response"
                    }), 500

                return jsonify({
                    "type": "success",
                    "workspace_name": workspace,
                    "table_name": table_name,
                    "suggestions": suggestions
                })

            except Exception as e:
                logger.exception("Error generating anomaly suggestions")
                return jsonify({"type": "error", "error": str(e)}), 500
            
            
            
        @self.flask_app.route("/api/v0/load_question", methods=["GET"])
        @self.requires_auth
        @self.requires_cache(
            ["question", "sql", "df"],
            optional_fields=["summary", "fig_json"]
        )
        def load_question(user: any, id: str, question, sql, df, fig_json, summary):
            """
            Load question
            ---
            parameters:
              - name: user
                in: query
              - name: id
                in: query|body
                type: string
                required: true
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: question_cache
                    id:
                      type: string
                    question:
                      type: string
                    sql:
                      type: string
                    df:
                      type: object
                    fig:
                      type: object
                    summary:
                      type: string
            """
            logger.info(f"load_question", extra={"flow":True})
            try:
                # workspace = flask.request.args.get("workspace")
                # user_role = session.get('username', None)
                # user_id = session.get('user_id', None)
                # self._log_complete_user_activity(
                #     question=question,
                #     sql_query=sql,
                #     summary=summary,
                #     workspace_name=workspace,
                #     user_role=user_role,
                #     user_id = user_id,
                #     cache_id=id
                # )
                return jsonify(
                    {
                        "type": "question_cache",
                        "id": id,
                        "question": question,
                        "sql": sql,
                        "df": df.head(10).to_json(orient="records", date_format="iso"),
                        "fig": fig_json,
                        "summary": summary,
                    }
                )

            except Exception as e:
                return jsonify({"type": "error", "error": str(e)})

        # @self.flask_app.route("/api/v0/load_question", methods=["GET"])
        # @self.requires_auth
        # @self.requires_cache(
        #     ["question", "sql", "df"],
        #     optional_fields=["summary", "fig_json"]
        # )
        # def load_question(user: any, id: str, question, sql, df, fig_json, summary):
        #     """
        #     Load question
        #     ---
        #     parameters:
        #     - name: user
        #         in: query
        #     - name: id
        #         in: query|body
        #         type: string
        #         required: true
        #     responses:
        #     200:
        #         schema:
        #         type: object
        #         properties:
        #             type:
        #             type: string
        #             default: question_cache
        #             id:
        #             type: string
        #             question:
        #             type: string
        #             sql:
        #             type: string
        #             df:
        #             type: object
        #             fig:
        #             type: object
        #             summary:
        #             type: string
        #     """
        #     logger.info(f"load_question", extra={"flow":True})
        #     try:
        #         response_data = {
        #             "type": "question_cache",
        #             "id": id,
        #             "question": question,
        #             "sql": sql,
        #             "df": df.head(10).to_json(orient="records", date_format="iso"),
        #             "fig": fig_json,
        #             "summary": summary,
        #         }
                
        #         # Clear the DataFrame from cache after preparing the response
        #         # This frees up memory now that the data has been sent to frontend
        #         try:
        #             self.cache.clear_df_after_load(id, user_id=user.get('id') if isinstance(user, dict) else None)
        #         except Exception as e:
        #             logger.warning(f"Failed to clear df after load for id={id}: {e}", extra={"cache": True})
                
        #         return jsonify(response_data)

        #     except Exception as e:
        #         return jsonify({"type": "error", "error": str(e)})


        @self.flask_app.route("/api/v0/get_question_history", methods=["GET"])
        @self.requires_auth
        def get_question_history(user: any):
            """
            Get question history
            ---
            parameters:
              - name: user
                in: query
            responses:
              200:
                schema:
                  type: object
                  properties:
                    type:
                      type: string
                      default: question_history
                    questions:
                      type: array
                      items:
                        type: string
            """
            logger.info(f"get_question_history", extra={"flow":True})
            return jsonify(
                {
                    "type": "question_history",
                    "questions": cache.get_all(field_list=["question"]),
                }
            )

        @self.flask_app.route("/api/v0/<path:catch_all>", methods=["GET", "POST"])
        def catch_all(catch_all):
            return jsonify(
                {"type": "error", "error": "The rest of the API is not ported yet."}
            )

        if self.debug:
            @self.sock.route("/api/v0/log")
            def sock_log(ws):
                self.ws_clients.append(ws)

                try:
                    while True:
                        message = ws.receive()  # This example just reads and ignores to keep the socket open
                finally:
                    self.ws_clients.remove(ws)






        # @self.flask_app.route('/api/v0/save_feedback', methods=['POST'])
        # def save_feedback():
        #     data = request.json
        #     workspace_id = data.get('workspace_id')
        #     question_id = data.get('question_id')
        #     question = data.get('question')
        #     sql = data.get('sql', '')  # allow empty
        #     rating = data.get('rating')
        #     comment = data.get('comment')
        #     conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
        #     cursor = conn.cursor()
        #     # Fix: Use SELECT COUNT(*) to check existence, include all keys
        #     cursor.execute("""
        #         SELECT COUNT(*)
        #         FROM user_feedback
        #         WHERE workspace_id = ? AND question_id = ? AND question = ? AND sql = ?
        #     """, workspace_id, question_id, question, sql)
        #     exists = cursor.fetchone()[0] > 0
        #     if exists:
        #         cursor.execute("""
        #             UPDATE user_feedback
        #             SET rating = ?, comment = ?, created_at = GETDATE()
        #             WHERE workspace_id = ? AND question_id = ? AND question = ? AND sql = ?
        #         """, rating, comment, workspace_id, question_id, question, sql)
        #     else:
        #         cursor.execute("""
        #             INSERT INTO user_feedback (workspace_id, question_id, question, sql, rating, comment, created_at)
        #             VALUES (?, ?, ?, ?, ?, ?, GETDATE())
        #         """, workspace_id, question_id, question, sql, rating, comment)
        #     conn.commit()
        #     conn.close()
        #     return jsonify({"status": "success"})



        @self.flask_app.route('/api/v0/save_feedback', methods=['POST'])
        def save_feedback():
            data = request.json
            workspace_id = data.get('workspace_id')
            question_id = data.get('question_id')
            question = data.get('question')
            sql = data.get('sql', '')  # allow empty
            rating = data.get('rating')
            comment = data.get('comment')
            conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
            cursor = conn.cursor()
            # Fix: Use SELECT COUNT(*) to check existence, include all keys
            # cursor.execute("""
            #     SELECT COUNT(*)
            #     FROM user_feedback
            #     WHERE workspace_id = ? AND question_id = ? AND question = ? AND sql = ?
            # """, workspace_id, question_id, question, sql)
            # exists = cursor.fetchone()[0] > 0
            # if exists:
            #     cursor.execute("""
            #         UPDATE user_feedback
            #         SET rating = ?, comment = ?, created_at = GETDATE()
            #         WHERE workspace_id = ? AND question_id = ? AND question = ? AND sql = ?
            #     """, rating, comment, workspace_id, question_id, question, sql)
            # else:
            #     cursor.execute("""
            #         INSERT INTO user_feedback (workspace_id, question_id, question, sql, rating, comment, created_at)
            #         VALUES (?, ?, ?, ?, ?, ?, GETDATE())
            #     """, workspace_id, question_id, question, sql, rating, comment)

            cursor.execute("""
                SELECT COUNT(*)
                FROM user_feedback
                WHERE workspace_id = ? AND question_id = ?
            """, workspace_id, question_id)

            exists = cursor.fetchone()[0] > 0

            if exists:
                cursor.execute("""
                    UPDATE user_feedback
                    SET
                        rating = ?,
                        comment = ?,
                        sql = COALESCE(NULLIF(?, ''), sql),
                        created_at = GETDATE()
                    WHERE workspace_id = ? AND question_id = ?
                """, rating, comment, sql, workspace_id, question_id)
            else:
                cursor.execute("""
                    INSERT INTO user_feedback
                        (workspace_id, question_id, question, sql, rating, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                """, workspace_id, question_id, question, sql, rating, comment)

            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
            


        @self.flask_app.route('/api/v0/get_feedback', methods=['GET'])
        def get_feedback():
            workspace_id = request.args.get('workspace_id')
            question_id  = request.args.get('question_id')
            sql          = request.args.get('sql')

            if not workspace_id or not question_id:
                return jsonify({"exists": False})

            conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT TOP 1 rating, comment
                FROM user_feedback
                WHERE workspace_id = ? AND question_id = ?
                ORDER BY created_at DESC
            """, workspace_id, question_id)

            row = cursor.fetchone()
            conn.close()

            if row:
                return jsonify({
                    "exists": True,
                    "rating": row.rating,
                    "comment": row.comment
                })

            return jsonify({"exists": False})
        


        @self.flask_app.route("/api/get_feedback_config", methods=["GET"])
        def get_feedback_config():
            cfg = load_email_config()

            return jsonify(cfg)
        

        @self.flask_app.route("/api/save_feedback_config", methods=["POST"])
        def save_feedback_config():

            data = request.json or {}

            cfg = {}

            # Common settings
            cfg.update({
                "email_provider": data.get("email_provider", "gmail"),
                "recipients": data.get("recipients", []),
                "cc": data.get("cc", []),
                "subject": data.get("subject", "Low Rating Feedback Alert"),
                "body": data.get("body", ""),
                "include_sent": data.get("include_sent", False),
                "email_interval": int(data.get("email_interval", 120)),
                "send_email_enabled": data.get("send_email_enabled", True)
            })

            # Gmail
            if data.get("email_provider") == "gmail":

                gmail_cfg = data.get("gmail", {})

                # Merge top-level sender fields if provided by frontend
                top_sender = {
                    "sender_email": data.get("sender_email"),
                    "sender_password": data.get("sender_password")
                }

                # Prefer nested gmail config, fall back to top-level fields
                gmail_cfg = {**(gmail_cfg or {}), **{k: v for k, v in top_sender.items() if v}}

                cfg["gmail"] = gmail_cfg

                cfg["smtp_server"] = gmail_cfg.get(
                    "smtp_server",
                    "smtp.gmail.com"
                )

                cfg["smtp_port"] = gmail_cfg.get(
                    "smtp_port",
                    587
                )

                cfg["sender_email"] = gmail_cfg.get(
                    "sender_email",
                    ""
                )

                cfg["sender_password"] = gmail_cfg.get(
                    "sender_password",
                    ""
                )

            # Outlook
            elif data.get("email_provider") == "outlook":

                outlook_cfg = data.get("outlook", {})

                cfg["outlook"] = outlook_cfg
                
                # Set SMTP server details for Outlook
                cfg["smtp_server"] = "smtp.office365.com"
                cfg["smtp_port"] = 587
                
                # Get sender credentials from request
                cfg["sender_email"] = data.get("sender_email", "")
                cfg["sender_password"] = data.get("sender_password", "")

            save_email_config(cfg)

            return jsonify({
                "success": True,
                "message": "Feedback email configuration updated"
            })












    def run(self, *args, **kwargs):
        """
        Run the Flask app.

        Args:
            *args: Arguments to pass to Flask's run method.
            **kwargs: Keyword arguments to pass to Flask's run method.

        Returns:
            None
        """
        if args or kwargs:
            self.flask_app.run(*args, **kwargs)

        else:
            try:
                from google.colab import output

                output.serve_kernel_port_as_window(8084)
                from google.colab.output import eval_js

                print("Your app is running at:")
                print(eval_js("google.colab.kernel.proxyPort(8084)"))
            except:
                print("Your app is running at:")
                print("http://localhost:8084")

            self.flask_app.run(host="0.0.0.0", port=8084, debug=self.debug, use_reloader=False)




class VannaFlaskApp(VannaFlaskAPI):
    def __init__(
        self,
        #vn: VannaBase,  # Allow `vn` to be None
        cache: Cache = MemoryCache(),
        auth: AuthInterface = BasicAuth(),
        debug=False,
        allow_llm_to_see_data=True,
        logo="http://tychons.com/wp-content/uploads/2025/09/warehouse_logo-2.png",
        title="Warehouse Intelligence Delivered",
        subtitle="",
        show_training_data=False,
        suggested_questions=False,
        sql=True,
        table=True,
        csv_download=True,
        chart=True,
        redraw_chart=True,
        auto_fix_sql=True,
        ask_results_correct=True,
        followup_questions=True,
        summarization=True,
        function_generation=False,
        index_html_path=None,
        assets_folder=None,
        **kwargs
        
    ):
        global vn
        
        #self.client = chromadb.PersistentClient(path="D:/VANNA")
        #self.config_collection = self.client.get_or_create_collection(name="LLM_config")  # ✅ Initialize here
        """
        Expose a Flask app that can be used to interact with a Vanna instance.

        Args:
            vn: The Vanna instance to interact with.
            cache: The cache to use. Defaults to MemoryCache, which uses an in-memory cache. You can also pass in a custom cache that implements the Cache interface.
            auth: The authentication method to use. Defaults to NoAuth, which doesn't require authentication. You can also pass in a custom authentication method that implements the AuthInterface interface.
            debug: Show the debug console. Defaults to True.
            allow_llm_to_see_data: Whether to allow the LLM to see data. Defaults to False.
            logo: The logo to display in the UI. Defaults to the Vanna logo.
            title: The title to display in the UI. Defaults to "Welcome to Vanna.AI".
            subtitle: The subtitle to display in the UI. Defaults to "Your AI-powered copilot for SQL queries.".
            show_training_data: Whether to show the training data in the UI. Defaults to True.
            suggested_questions: Whether to show suggested questions in the UI. Defaults to True.
            sql: Whether to show the SQL input in the UI. Defaults to True.
            table: Whether to show the table output in the UI. Defaults to True.
            csv_download: Whether to allow downloading the table output as a CSV file. Defaults to True.
            chart: Whether to show the chart output in the UI. Defaults to True.
            redraw_chart: Whether to allow redrawing the chart. Defaults to True.
            auto_fix_sql: Whether to allow auto-fixing SQL errors. Defaults to True.
            ask_results_correct: Whether to ask the user if the results are correct. Defaults to True.
            followup_questions: Whether to show followup questions. Defaults to True.
            summarization: Whether to show summarization. Defaults to True.
            index_html_path: Path to the index.html. Defaults to None, which will use the default index.html
            assets_folder: The location where you'd like to serve the static assets from. Defaults to None, which will use hardcoded Python variables.

        Returns:
            None
        """
        super().__init__(cache, auth, debug, allow_llm_to_see_data, chart, **kwargs)
         

        self.flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
        # Initialize ChromaDB client and collections
        self.client = chromadb.PersistentClient(path="D:/Admin-Module/WAI")
        self.config_collection = self.client.get_or_create_collection(name="LLM_config")
        self.db_collection = self.client.get_or_create_collection(name="DB_connections")
        self.workspace_collection = self.client.get_or_create_collection(name="Workspaces") # New collection for workspaces
        self.users_collection = self.client.get_or_create_collection(name="users") 
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"),model_name="text-embedding-3-large")
        self.sop_collection = self.client.get_or_create_collection(name="SOP_documents", embedding_function=openai_ef) #sop agents

        self.user_mgmt_config = {
            'server': os.environ.get('USER_MGMT_SERVER', '192.168.1.74'),  # Default fallback
            'port': os.environ.get('USER_MGMT_PORT', '7274'),
            'database': os.environ.get('USER_MGMT_DATABASE', 'tychons_wi'),
            'username': os.environ.get('USER_MGMT_USERNAME', 'user'),  # Default fallback
            'password': os.environ.get('USER_MGMT_PASSWORD', os.environ.get('FEEDBACK_DB_PASSWORD', ''))  # Default fallback
        }
        self.config["logo"] = logo
        self.config["title"] = title
        self.config["subtitle"] = subtitle
        self.config["show_training_data"] = show_training_data
        self.config["suggested_questions"] = suggested_questions
        self.config["sql"] = sql
        self.config["table"] = table
        self.config["csv_download"] = csv_download
        self.config["chart"] = chart
        self.config["redraw_chart"] = redraw_chart
        self.config["auto_fix_sql"] = auto_fix_sql
        self.config["ask_results_correct"] = ask_results_correct
        self.config["followup_questions"] = followup_questions
        self.config["summarization"] = summarization
        # admin config
        self.ai_options = {
            "suggested_questions": suggested_questions,
            "sql": sql,
            "table": table,
            "csv_download": csv_download,
            "chart": chart,
            "redraw_chart": redraw_chart,
            "auto_fix_sql": auto_fix_sql,
            "ask_results_correct": ask_results_correct,
            "followup_questions": followup_questions,
            "summarization": summarization,
            "function_generation": function_generation,
        }
        self.workspace_settings = {}
        # admin config
        self.config["function_generation"] = function_generation and hasattr(vn, "get_function")
        self.config["version"] = importlib.metadata.version('vanna')

        self.index_html_path = index_html_path
        self.assets_folder = assets_folder

        # -------------  STOCK-OUT AGENT CRON  -------------
        def _stockout_cron_job():
            import json 
            """Executed every CRON_INTERVAL minutes for every workspace."""
            try:
                all_ws = self.workspace_collection.get()
                for idx, meta in enumerate(all_ws["metadatas"]):
                    ws_id = all_ws["ids"][idx]
                    raw  = meta.get("agent_config_stockout", "{}")
                    cfg  = json.loads(raw) if raw else {}
                    if not cfg.get("enabled", False):        # master toggle
                        continue
                    recipients = cfg.get("recipients", [])
                    if not recipients:                       # nobody to mail
                        continue
                    scenarios  = cfg.get("scenarios", [])
                    for sc in scenarios:
                        if not sc.get("enabled", True):      # scenario toggle
                            continue
                        sc_id   = sc["id"]
                        sql     = sc.get("sql", "")
                        if not sql:                          # fallback SQL map
                            sql = SCENARIO_SQL_MAP.get(sc_id, "")
                        if not sql:                          # still nothing
                            continue
                        # --- deduplication ---------------------------------
                        now = _dt.now().timestamp()
                        last = alert_history.get(ws_id, {}).get(sc_id, 0)
                        if now - last < ALERT_COOLDOWN_SECONDS:
                            continue
                        # --- run SQL ---------------------------------------
                        global vn
                        ok, err = self.ensure_vanna_initialized(ws_id)

                        if not ok:                           # vn not ready
                            logger.warning("stock-out cron: %s", err)
                            continue
                        try:
                            df = vn.run_sql(sql)
                            rows = df.to_dict(orient="records") if len(df) else []
                        except Exception as e:
                            logger.exception("stock-out SQL failed: %s", e)
                            continue
                        if not rows:                         # nothing found
                            continue
                        # --- send mail -------------------------------------
                        subject = f"[WAI-StockOut] {sc['name']}"
                        body = (
                            f"Workspace : {ws_id}\n"
                            f"Scenario  : {sc['name']}\n"
                            f"Found     : {len(rows)} affected records\n\n"
                            f"Please review the attached CSV for details."
                        )
                        _send_email(recipients, subject, body, rows,
                                    f"{sc_id}_{_dt.now():%Y%m%d_%H%M%S}.csv")
                        # --- update history --------------------------------
                        alert_history.setdefault(ws_id, {})[sc_id] = now
                        logger.info("stock-out alert mailed: %s / %s (%d rows)",
                                    ws_id, sc_id, len(rows))
            except Exception as e:
                logger.exception("stock-out cron global error: %s", e)

        # start the APScheduler thread
        global stockout_cron_scheduler
        stockout_cron_scheduler = BackgroundScheduler()
        stockout_cron_scheduler.add_job(
            func=_stockout_cron_job,
            trigger="interval",
            minutes=30,               # <-- change here if you want another interval
            max_instances=1,
            coalesce=True,
            next_run_time=_dt.now()   # fire immediately on start-up
        )
        stockout_cron_scheduler.start()
        atexit.register(lambda: stockout_cron_scheduler.shutdown())
        logger.info("stock-out agent cron started (15-min interval)")


        # ---------------- DATA INTEGRITY AGENT CRON ---------------- #
        # Similar structure to stock-out cron but with its own config, SQL
        def _data_integrity_cron_job():
            import json  # avoid free-variable issue caused by 'import json' elsewhere in __init__
            """
            Executed every 5 minutes globally.
            Each workspace controls:
                - interval_minutes (how often to check)
                - cooldown_days + cooldown_minutes (how often to notify)
            """

            try:
                all_ws = self.workspace_collection.get()

                for idx, meta in enumerate(all_ws["metadatas"]):
                    ws_id = all_ws["ids"][idx]

                    raw = meta.get("agent_config_data_integrity", "{}")
                    cfg = json.loads(raw) if raw else {}

                    # ---------------- MASTER TOGGLE ---------------- #
                    if not cfg.get("enabled", False):
                        continue

                    recipients = cfg.get("recipients", [])
                    if not recipients:
                        continue

                    now = _dt.now().timestamp()

                    # ---------------- INTERVAL CONTROL ---------------- #
                    interval_minutes = cfg.get("interval_minutes", 5)

                    last_run = alert_history.get(ws_id, {}).get(
                        "data_integrity_last_run", 0
                    )

                    if now - last_run < interval_minutes * 60:
                        continue  # Not time to check yet

                    scenarios = cfg.get("scenarios", [])

                    for sc in scenarios:

                        # ---------------- SCENARIO TOGGLE ---------------- #
                        if not sc.get("enabled", True):
                            continue

                        sc_id = sc.get("id")
                        if not sc_id:
                            continue

                        sql = sc.get("sql") or DATA_INTEGRITY_SQL_MAP.get(sc_id, "")
                        if not sql:
                            continue

                        # ---------------- SQL SAFETY ---------------- #
                        if not sql.strip().lower().startswith("select"):
                            logger.warning(
                                "Blocked non-select query in %s / %s", ws_id, sc_id
                            )
                            continue

                        # ---------------- USER CONTROLLED COOLDOWN ---------------- #
                        cooldown_days = cfg.get("cooldown_days", 0)
                        cooldown_minutes = cfg.get("cooldown_minutes", 60)

                        cooldown_seconds = (
                            cooldown_days * 86400 +
                            cooldown_minutes * 60
                        )

                        # Safety fallback
                        if cooldown_seconds <= 0:
                            cooldown_seconds = 3600  # 1 hour default

                        last_alert = alert_history.get(ws_id, {}).get(sc_id, 0)

                        if now - last_alert < cooldown_seconds:
                            continue  # Cooldown active

                        # ---------------- ENSURE VANNA ---------------- #
                        ok, err = self.ensure_vanna_initialized(ws_id)
                        if not ok:
                            logger.warning("data integrity cron: %s", err)
                            continue

                        try:
                            df = vn.run_sql(sql)
                            row_count = len(df) if df is not None else 0
                            rows = df.to_dict(orient="records") if row_count > 0 else []

                        except Exception as e:
                            logger.exception(
                                "Data Integrity SQL failed for %s / %s: %s",
                                ws_id, sc_id, e
                            )
                            continue

                        # ---------------- NO RECORDS → NO EMAIL ---------------- #
                        if not rows:
                            continue

                        # ---------------- EXTRACT LOCATION LIST ---------------- #
                        locations = list({
                            r.get("location_id")
                            for r in rows
                            if r.get("location_id")
                        })

                        location_list = ", ".join(locations[:20]) if locations else "N/A"

                        # ---------------- MESSAGE ---------------- #
                        scenario_cfg = DATA_INTEGRITY_MESSAGES.get(
                            sc_id,
                            {
                                "subject": sc.get("name", "Data Integrity Alert"),
                                "body": "Duplicate records detected."
                            }
                        )

                        subject = scenario_cfg["subject"]

                        body = (
                            f"Workspace : {ws_id}\n"
                            f"Scenario  : {sc.get('name')}\n"
                            f"Locations : {location_list}\n"
                            f"Total Rows: {len(rows)}\n\n"
                            f"{scenario_cfg['body']}\n\n"
                            "Please review attached CSV."
                        )

                        try:
                            send_alert_email_with_csv(
                                recipients=recipients,
                                subject=subject,
                                body=body,
                                rows=rows,
                                filename=f"{sc_id}_{_dt.now():%Y%m%d_%H%M%S}.csv"
                            )

                            # Update per-scenario cooldown timestamp
                            alert_history.setdefault(ws_id, {})[sc_id] = now

                            logger.info(
                                "Data Integrity alert mailed: %s / %s (%d rows)",
                                ws_id, sc_id, len(rows)
                            )

                        except Exception as e:
                            logger.exception(
                                "Email send failed for %s / %s: %s",
                                ws_id, sc_id, e
                            )
                            continue

                    # ---------------- UPDATE LAST RUN FOR WORKSPACE ---------------- #
                    alert_history.setdefault(ws_id, {})[
                        "data_integrity_last_run"
                    ] = now

            except Exception as e:
                logger.exception("Data Integrity cron global error: %s", e)


        # start the APScheduler thread for data integrity
        data_integrity_scheduler = BackgroundScheduler()

        data_integrity_scheduler.add_job(
            func=_data_integrity_cron_job,
            trigger="interval",
            minutes=5,              # global frequency
            max_instances=1,
            coalesce=True,
            next_run_time=_dt.now()
        )

        data_integrity_scheduler.start()
        atexit.register(lambda: data_integrity_scheduler.shutdown())
        logger.info("Data Integrity agent cron started (5-min global interval)")


        # -------------  IDENTIFY STUCK DEVICE CRON  -------------
        def _build_emp_engine():
            from urllib.parse import quote_plus
            server   = os.getenv("SCHEDULER_DB_SERVER", "").strip()
            port     = os.getenv("SCHEDULER_DB_PORT", "").strip()
            database = os.getenv("SCHEDULER_DB_NAME", "").strip()
            username = os.getenv("SCHEDULER_DB_USER", "").strip()
            password = os.getenv("SCHEDULER_DB_PASSWORD", "").strip()
            driver   = os.getenv("SCHEDULER_DB_DRIVER", "ODBC Driver 17 for SQL Server").strip()
            timeout  = int(os.getenv("SCHEDULER_QUERY_TIMEOUT", "15"))
            conn_str = (
                f"mssql+pyodbc://{quote_plus(username)}:{quote_plus(password)}"
                f"@{server}:{port}/{database}"
                f"?driver={driver.replace(' ', '+')}"
            )
            engine = create_engine(conn_str, pool_pre_ping=True)

            @sa_event.listens_for(engine, "connect")
            def set_timeout(dbapi_conn, _rec):
                dbapi_conn.timeout = timeout

            logger.info("Scheduler engine ready — server=%s db=%s timeout=%ss", server, database, timeout)
            return engine, timeout

        def _build_exec_engine():
            from urllib.parse import quote_plus
            server   = os.getenv("EXECUTOR_DB_SERVER", "").strip()
            port     = os.getenv("EXECUTOR_DB_PORT", "").strip()
            database = os.getenv("EXECUTOR_DB_NAME", "").strip()
            username = os.getenv("EXECUTOR_DB_USER", "").strip()
            password = os.getenv("EXECUTOR_SCHEDULERDB_PASSWORD", "").strip()
            driver   = os.getenv("EXECUTOR_DB_DRIVER", "ODBC Driver 17 for SQL Server").strip()
            timeout  = int(os.getenv("EXECUTOR_QUERY_TIMEOUT", "15"))
            conn_str = (
                f"mssql+pyodbc://{quote_plus(username)}:{quote_plus(password)}"
                f"@{server}:{port}/{database}"
                f"?driver={driver.replace(' ', '+')}"
            )
            engine = create_engine(conn_str, pool_pre_ping=True)

            @sa_event.listens_for(engine, "connect")
            def set_timeout(dbapi_conn, _rec):
                dbapi_conn.timeout = timeout

            logger.info("Executor engine ready — server=%s db=%s timeout=%ss", server, database, timeout)
            return engine, timeout

        # Scheduler/executor DB config is set per-workspace from the frontend, not a
        # required startup-time env var — a missing/invalid config must never block
        # the server from starting. The jobs below already guard their own engine
        # usage in try/except, so a None engine just means that job logs a warning
        # and no-ops until the workspace config is actually supplied.
        try:
            _emp_engine, _emp_timeout = _build_emp_engine()
        except Exception as e:
            logger.warning(f"Scheduler engine not configured, related cron jobs will no-op: {e}", extra={"admin": True})
            _emp_engine, _emp_timeout = None, None

        try:
            _exec_engine, _exec_timeout = _build_exec_engine()
        except Exception as e:
            logger.warning(f"Executor engine not configured, related cron jobs will no-op: {e}", extra={"admin": True})
            _exec_engine, _exec_timeout = None, None

        def _identify_stuck_device_job():
            global _current_stuck_run_id
            _current_stuck_run_id = _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            _log_stuck("INFO", "Automated device reset job started.")

            # Step 1: Query scheduler database for stuck devices in the last 2 hours
            try:
                with _emp_engine.connect() as conn:
                    rows = conn.execute(text("""
                        SELECT device_id
                        FROM t_log_message
                        WHERE details LIKE '%Data Error%'
                          AND device_id IS NOT NULL
                          AND user_id IS NOT NULL
                          AND logged_on_utc >= DATEADD(HOUR, -2, GETUTCDATE())
                          AND logged_on_utc < GETUTCDATE()
                    """)).fetchall()
                if not rows:
                    _log_stuck("INFO", "Step 1: No stuck devices detected in the last 2 hours. No action required.")
                    _log_stuck("INFO", "Automated device reset job completed.")
                    return
                stuck_devices = pd.DataFrame(rows, columns=["device_id"]).drop_duplicates(subset=["device_id"])
                _log_stuck("INFO", f"Step 1: Found {len(stuck_devices)} stuck device(s) requiring reset: {stuck_devices['device_id'].tolist()}")
            except Exception as exc:
                _log_stuck("ERROR", f"Step 1: Database query failed while scanning for stuck devices. Error: {exc}")
                _log_stuck("INFO", "Automated device reset job completed.")
                return

            # Steps 2 through 6: Process each stuck device via the executor database
            for _, row in stuck_devices.iterrows():
                device_id = row["device_id"]
                _log_stuck("INFO", f"Device {device_id}: Processing started.", device_id=device_id)
                fork_loc = wh_id = temp_loc = emp_id = None
                try:
                    # Step 2: Resolve employee and fork location
                    _log_stuck("INFO", f"Device {device_id} - Step 2: Resolving assigned fork location.", device_id=device_id)
                    with _exec_engine.connect() as conn:
                        emp_row = conn.execute(text(
                            "SELECT id FROM t_employee WHERE device = :dev"
                        ), {"dev": device_id}).fetchone()
                    if not emp_row:
                        _log_stuck("WARNING", f"Device {device_id} - Step 2: No employee record found for this device. Device remains in stuck state.", device_id=device_id)
                        continue
                    emp_id = emp_row[0]
                    _log_stuck("INFO", f"Device {device_id} - Step 2: Employee identified. Employee ID: {emp_id}.", device_id=device_id)

                    with _exec_engine.connect() as conn:
                        loc_row = conn.execute(text(
                            "SELECT wh_id, location_id FROM t_location WHERE c1 = :emp"
                        ), {"emp": emp_id}).fetchone()
                    if not loc_row:
                        _log_stuck("WARNING", f"Device {device_id} - Step 2: No fork location found for employee {emp_id}. Device remains in stuck state.", device_id=device_id)
                        continue
                    wh_id, fork_loc = loc_row[0], loc_row[1]
                    _log_stuck("INFO", f"Device {device_id} - Step 2: Fork location resolved. Location: {fork_loc}, Warehouse: {wh_id}.", device_id=device_id)

                    # Step 3: Check inventory at fork location
                    _log_stuck("INFO", f"Device {device_id} - Step 3: Checking inventory at fork location {fork_loc}.", device_id=device_id)
                    with _exec_engine.connect() as conn:
                        si_rows = conn.execute(text("SELECT * FROM t_stored_item WHERE location_id = :loc AND wh_id = :wh"), {"loc": fork_loc, "wh": wh_id}).fetchall()
                        hm_rows = conn.execute(text("SELECT * FROM t_hu_master   WHERE location_id = :loc AND wh_id = :wh"), {"loc": fork_loc, "wh": wh_id}).fetchall()
                        hd_rows = conn.execute(text("SELECT * FROM t_hu_detail   WHERE location_id = :loc AND wh_id = :wh"), {"loc": fork_loc, "wh": wh_id}).fetchall()
                    has_inventory = bool(si_rows or hm_rows or hd_rows)
                    _log_stuck("INFO", f"Device {device_id} - Step 3: Inventory check complete. Stored items: {len(si_rows)}, HU master records: {len(hm_rows)}, HU detail records: {len(hd_rows)}. Inventory present: {has_inventory}.", device_id=device_id)

                    if has_inventory:
                        # Step 4: Find an available staging location
                        _log_stuck("INFO", f"Device {device_id} - Step 4: Searching for an available staging location.", device_id=device_id)
                        with _exec_engine.connect() as conn:
                            stage_row = conn.execute(text("""
                                SELECT TOP 1 tl.location_id
                                FROM t_location tl (NOLOCK)
                                WHERE tl.wh_id = :wh
                                  AND (tl.status = 'E' OR tl.status = 'P')
                                  AND tl.type = 'S'
                                  AND (tl.description LIKE '%STAGE%' OR tl.description LIKE '%STAGING%')
                                  AND NOT EXISTS (
                                      SELECT 1 FROM t_stored_item si (NOLOCK)
                                      WHERE si.location_id = tl.location_id AND si.wh_id = tl.wh_id
                                  )
                                  AND NOT EXISTS (
                                      SELECT 1 FROM t_hu_master hm (NOLOCK)
                                      WHERE hm.location_id = tl.location_id AND hm.wh_id = tl.wh_id
                                  )
                                ORDER BY tl.status ASC, ISNULL(tl.stored_qty, 0) ASC
                            """), {"wh": wh_id}).fetchone()
                        if not stage_row:
                            _log_stuck("ERROR", f"Device {device_id} - Step 4: No available staging location found. Device remains in stuck state.", device_id=device_id)
                            continue
                        temp_loc = stage_row[0]
                        _log_stuck("INFO", f"Device {device_id} - Step 4: Staging location selected. Location: {temp_loc}.", device_id=device_id)

                    # Steps 5 and 6: Execute atomic transaction — all changes committed together or rolled back entirely
                    _log_stuck("INFO", f"Device {device_id} - Steps 5 and 6: Initiating atomic database transaction.", device_id=device_id)
                    with _exec_engine.begin() as conn:
                        if has_inventory and temp_loc:
                            conn.execute(text("UPDATE t_stored_item SET location_id = :new WHERE location_id = :old AND wh_id = :wh"), {"new": temp_loc, "old": fork_loc, "wh": wh_id})
                            _log_stuck("INFO", f"Device {device_id} - Step 5: Stored items relocated from {fork_loc} to {temp_loc}.", device_id=device_id)
                            conn.execute(text("UPDATE t_hu_master SET location_id = :new WHERE location_id = :old AND wh_id = :wh"), {"new": temp_loc, "old": fork_loc, "wh": wh_id})
                            _log_stuck("INFO", f"Device {device_id} - Step 5: Handling unit master records relocated from {fork_loc} to {temp_loc}.", device_id=device_id)
                            conn.execute(text("UPDATE t_hu_detail SET location_id = :new WHERE location_id = :old AND wh_id = :wh"), {"new": temp_loc, "old": fork_loc, "wh": wh_id})
                            _log_stuck("INFO", f"Device {device_id} - Step 5: Handling unit detail records relocated from {fork_loc} to {temp_loc}.", device_id=device_id)

                        if emp_id:
                            conn.execute(text("UPDATE t_employee SET device = NULL WHERE id = :id AND wh_id = :wh AND device = :dev"), {"id": emp_id, "wh": wh_id, "dev": device_id})
                            _log_stuck("INFO", f"Device {device_id} - Step 6: Employee device assignment cleared.", device_id=device_id)

                        conn.execute(text("UPDATE t_location SET c1 = NULL, status = 'E' WHERE location_id = :loc AND wh_id = :wh"), {"loc": fork_loc, "wh": wh_id})
                        _log_stuck("INFO", f"Device {device_id} - Step 6: Fork location cleared and status set to available.", device_id=device_id)

                    _log_stuck("INFO", f"Device {device_id}: All steps completed successfully. Device has been reset.", device_id=device_id)

                except Exception as exc:
                    # Transaction auto-rolled back by context manager — no partial writes committed
                    logger.exception("Automated device reset failed for device %s: %s", device_id, exc)
                    _log_stuck("ERROR", f"Device {device_id}: Processing failed. All database changes have been rolled back. Error: {exc}", device_id=device_id)
                    _log_stuck("WARNING", f"Device {device_id}: Device remains in stuck state. No changes were committed.", device_id=device_id)

            _log_stuck("INFO", "Automated device reset job completed.")

        global _stuck_device_scheduler
        _stuck_device_scheduler = BackgroundScheduler()
        _stuck_device_scheduler.add_job(
            func=_identify_stuck_device_job,
            trigger="interval",
            hours=2,
            id="identify_stuck_device",
            name="Identify Stuck Device",
            max_instances=1,
            coalesce=True,
            next_run_time=_dt.now(),
        )
        _stuck_device_scheduler.start()
        atexit.register(lambda: _stuck_device_scheduler.shutdown())
        logger.info("Identify Stuck Device cron started — runs every 2 hours.")

        # -------------  AUTOMATED UNPICK CRON  -------------
        _AUTO_UNPICK_SQL = """
            SELECT DISTINCT
                  TL.control_number AS order_number
                , TL.wh_id
                , TL.item_number
            FROM t_tran_log TL WITH(NOLOCK)

            LEFT JOIN t_pick_detail PD
                ON PD.order_number = TL.control_number
                AND PD.wh_id = TL.wh_id
                AND PD.item_number = TL.item_number
                AND PD.line_number = TL.line_number

            LEFT JOIN t_stored_item SI
                ON SI.wh_id = TL.wh_id
                AND SI.item_number = TL.item_number
                AND SI.type = TL.control_number

            LEFT JOIN t_hu_master HM
                ON HM.wh_id = TL.wh_id
                AND HM.hu_id = TL.hu_id

            LEFT JOIN t_hu_detail HD
                ON HD.wh_id = TL.wh_id
                AND HD.hu_id = TL.hu_id
                AND HD.item_number = TL.item_number

            LEFT JOIN t_work_q WQ
                ON WQ.wh_id = TL.wh_id
                AND WQ.pick_ref_number = TL.control_number
                AND WQ.item_number = TL.item_number

            WHERE TL.tran_type = '391'
            AND TL.description = 'Unload/Unpick (pick)'

            AND NOT EXISTS (
                SELECT 1
                FROM t_tran_log TL2
                WHERE TL2.control_number = TL.control_number
                AND TL2.wh_id = TL.wh_id
                AND TL2.item_number = TL.item_number
                AND TL2.tran_type = '301'
                AND TL2.description = 'Picking (pick)'
                AND (
                    CAST(TL2.start_tran_date AS DATETIME) + CAST(TL2.start_tran_time AS DATETIME)
                    > CAST(TL.start_tran_date AS DATETIME) + CAST(TL.start_tran_time AS DATETIME)
                )
            )

            AND (
                ISNULL(PD.picked_quantity, 0) <> 0
                OR ISNULL(PD.staged_quantity, 0) <> 0
                OR PD.status <> 'RELEASED'
                OR SI.type <> 'STORAGE'
                OR SI.location_id <> (
                    SELECT TOP 1 TL_PICK.location_id
                    FROM t_tran_log TL_PICK
                    WHERE TL_PICK.control_number = TL.control_number
                    AND TL_PICK.wh_id = TL.wh_id
                    AND TL_PICK.item_number = TL.item_number
                    AND TL_PICK.tran_type = '301'
                    ORDER BY TL_PICK.start_tran_date DESC, TL_PICK.start_tran_time DESC
                )
                OR HM.control_number IS NOT NULL
                OR HM.type <> 'IV'
                OR HD.storage_type IS NOT NULL
                OR WQ.work_status <> 'U'
            )
        """

        def _auto_unpick_job():
            global _current_unpick_run_id
            _current_unpick_run_id = _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            run_id = _current_unpick_run_id
            _log_unpick("INFO", "Automated unpick job started.", run_id=run_id)

            # Step 1: Find dirty unpick records
            try:
                with _exec_engine.connect() as conn:
                    rows = conn.execute(text(_AUTO_UNPICK_SQL)).fetchall()
                if not rows:
                    _log_unpick("INFO", "No dirty unpick records found. Nothing to do.", run_id=run_id)
                    _log_unpick("INFO", "Automated unpick job completed.", run_id=run_id)
                    return
                records = [{"order_number": r[0], "wh_id": r[1], "item_number": r[2]} for r in rows]
                _log_unpick("INFO", f"Found {len(records)} record(s) requiring unpick: {[(r['order_number'], r['item_number']) for r in records]}", run_id=run_id)
            except Exception as exc:
                _log_unpick("ERROR", f"Scan query failed: {exc}", run_id=run_id)
                _log_unpick("INFO", "Automated unpick job completed.", run_id=run_id)
                return

            # Step 2: Process each record atomically
            for rec in records:
                wh_id        = str(rec["wh_id"]).strip()
                order_number = str(rec["order_number"]).strip()
                item_number  = str(rec["item_number"]).strip()
                _log_unpick("INFO", "Processing started.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                try:
                    with _exec_engine.begin() as conn:
                        # ── Resolve pick_location (column-existence check + tran_log fallback) ──
                        col_chk = conn.execute(text(
                            "SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('t_pick_detail') AND name = 'pick_location'"
                        )).fetchone()
                        if col_chk:
                            row = conn.execute(text(
                                "SELECT pick_location FROM t_pick_detail WHERE wh_id = :w AND order_number = :o AND item_number = :i"
                            ), {"w": wh_id, "o": order_number, "i": item_number}).fetchone()
                            pick_location = row[0] if row else None
                            if not pick_location:
                                row2 = conn.execute(text(
                                    "SELECT TOP 1 location_id FROM t_tran_log WHERE wh_id = :w AND tran_type = '301' AND item_number = :i AND control_number = :o ORDER BY start_tran_date DESC, start_tran_time DESC"
                                ), {"w": wh_id, "i": item_number, "o": order_number}).fetchone()
                                pick_location = row2[0] if row2 else None
                        else:
                            row = conn.execute(text(
                                "SELECT TOP 1 source_location_id FROM t_tran_log WHERE wh_id = :w AND tran_type = '301' AND item_number = :i AND control_number = :o ORDER BY start_tran_date DESC, start_tran_time DESC"
                            ), {"w": wh_id, "i": item_number, "o": order_number}).fetchone()
                            pick_location = row[0] if row else None
                        if not pick_location:
                            _log_unpick("WARNING", "Could not resolve pick_location — skipping.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                            continue
                        _log_unpick("INFO", f"pick_location = {pick_location}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        # ── Step 1: Full unstage — set quantities to zero ──────────────
                        result = conn.execute(text("""
                            UPDATE t_pick_detail
                            SET staged_quantity = 0, picked_quantity = 0, status = 'RELEASED'
                            WHERE wh_id = :w AND order_number = :o AND item_number = :i
                        """), {"w": wh_id, "o": order_number, "i": item_number})
                        _log_unpick("INFO", f"Step 1: t_pick_detail fully unstaged. Rows: {result.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        # ── Step 2: Get location type ──────────────────────────────────
                        loc_row = conn.execute(text(
                            "SELECT item_hu_indicator FROM t_location WHERE wh_id = :w AND location_id = :l"
                        ), {"w": wh_id, "l": pick_location}).fetchone()
                        item_hu_indicator = loc_row[0] if loc_row else None
                        _log_unpick("INFO", f"Step 2: item_hu_indicator = '{item_hu_indicator}'.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        def _restore_si_full(case_label):
                            si_exists = conn.execute(text(
                                "SELECT 1 FROM t_stored_item WHERE wh_id = :w AND item_number = :i AND type = 'STORAGE' AND location_id = :l"
                            ), {"w": wh_id, "i": item_number, "l": pick_location}).fetchone()
                            if si_exists:
                                conn.execute(text("""
                                    UPDATE S SET S.actual_qty = S.actual_qty + O.actual_qty
                                    FROM t_stored_item S
                                    JOIN t_stored_item O ON O.wh_id = S.wh_id AND O.item_number = S.item_number
                                    WHERE S.wh_id = :w AND S.item_number = :i AND S.type = 'STORAGE'
                                      AND S.location_id = :l AND O.type = :o
                                """), {"w": wh_id, "i": item_number, "l": pick_location, "o": order_number})
                                conn.execute(text(
                                    "DELETE FROM t_stored_item WHERE wh_id = :w AND item_number = :i AND type = :o"
                                ), {"w": wh_id, "i": item_number, "o": order_number})
                                _log_unpick("INFO", f"Step 2 ({case_label}): Merged qty into STORAGE and deleted order-type row.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                            else:
                                conn.execute(text(
                                    "UPDATE t_stored_item SET type = 'STORAGE', location_id = :l WHERE wh_id = :w AND item_number = :i AND type = :o"
                                ), {"l": pick_location, "w": wh_id, "i": item_number, "o": order_number})
                                _log_unpick("INFO", f"Step 2 ({case_label}): Renamed order-type row to STORAGE.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        if item_hu_indicator == 'I':
                            hu_row = conn.execute(text(
                                "SELECT TOP 1 hu_id FROM t_hu_detail WHERE wh_id = :w AND item_number = :i AND storage_type = :o"
                            ), {"w": wh_id, "i": item_number, "o": order_number}).fetchone()
                            picked_hu_id = hu_row[0] if hu_row else None
                            _restore_si_full("Case I")
                            if picked_hu_id:
                                conn.execute(text(
                                    "DELETE FROM t_hu_detail WHERE wh_id = :w AND hu_id = :h AND item_number = :i AND storage_type = :o"
                                ), {"w": wh_id, "h": picked_hu_id, "i": item_number, "o": order_number})
                                remaining = conn.execute(text(
                                    "SELECT 1 FROM t_hu_detail WHERE wh_id = :w AND hu_id = :h"
                                ), {"w": wh_id, "h": picked_hu_id}).fetchone()
                                if not remaining:
                                    conn.execute(text(
                                        "DELETE FROM t_hu_master WHERE wh_id = :w AND hu_id = :h"
                                    ), {"w": wh_id, "h": picked_hu_id})
                            _log_unpick("INFO", "Step 2 (Case I): Item-controlled location updates done.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        elif item_hu_indicator == 'H':
                            hu_row = conn.execute(text(
                                "SELECT TOP 1 hu_id FROM t_hu_detail WHERE wh_id = :w AND item_number = :i AND storage_type = :o"
                            ), {"w": wh_id, "i": item_number, "o": order_number}).fetchone()
                            picked_hu_id = hu_row[0] if hu_row else None
                            if picked_hu_id:
                                item_count = conn.execute(text(
                                    "SELECT COUNT(DISTINCT item_number) FROM t_hu_detail WHERE wh_id = :w AND hu_id = :h"
                                ), {"w": wh_id, "h": picked_hu_id}).scalar()
                                if item_count == 1:
                                    conn.execute(text(
                                        "DELETE FROM t_hu_detail WHERE wh_id = :w AND hu_id = :h AND item_number = :i AND storage_type = :o"
                                    ), {"w": wh_id, "h": picked_hu_id, "i": item_number, "o": order_number})
                                    remaining = conn.execute(text(
                                        "SELECT 1 FROM t_hu_detail WHERE wh_id = :w AND hu_id = :h"
                                    ), {"w": wh_id, "h": picked_hu_id}).fetchone()
                                    if not remaining:
                                        conn.execute(text(
                                            "DELETE FROM t_hu_master WHERE wh_id = :w AND hu_id = :h"
                                        ), {"w": wh_id, "h": picked_hu_id})
                                    _restore_si_full("Case 2A")
                                    _log_unpick("INFO", "Step 2 (Case 2A): Single-item LP updates done.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                                else:
                                    new_hu_id = conn.execute(text(
                                        "SELECT 'UP' + RIGHT('00000000' + CAST(ABS(CHECKSUM(NEWID())) % 100000000 AS VARCHAR), 8)"
                                    )).scalar()
                                    conn.execute(text(
                                        "INSERT INTO t_hu_master (hu_id, type, control_number, location_id, status, wh_id) VALUES (:h, 'LP', NULL, :l, 'A', :w)"
                                    ), {"h": new_hu_id, "l": pick_location, "w": wh_id})
                                    conn.execute(text(
                                        "UPDATE t_hu_detail SET hu_id = :nh, location_id = :l, storage_type = NULL WHERE wh_id = :w AND hu_id = :h AND item_number = :i"
                                    ), {"nh": new_hu_id, "l": pick_location, "w": wh_id, "h": picked_hu_id, "i": item_number})
                                    _restore_si_full("Case 2B")
                                    _log_unpick("INFO", f"Step 2 (Case 2B): Multi-item LP split to new HU {new_hu_id}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                            else:
                                _log_unpick("WARNING", "Step 2 (Case H): No HU detail found — skipping HU updates.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                                _restore_si_full("Case H/no HU")
                        else:
                            _log_unpick("WARNING", f"Step 2: Unknown item_hu_indicator='{item_hu_indicator}' — skipping HU updates.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                        # ── Step 3: Release work queue (full unpick → always 'U') ──────
                        result = conn.execute(text("""
                            UPDATE t_work_q SET work_status = 'U'
                            WHERE wh_id = :w AND pick_ref_number = :o
                            AND work_q_id IN (
                                SELECT work_q_id FROM t_pick_detail
                                WHERE order_number = :o AND wh_id = :w AND item_number = :i
                            )
                        """), {"w": wh_id, "o": order_number, "i": item_number})
                        _log_unpick("INFO", f"Step 3: t_work_q updated. Rows: {result.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    _log_unpick("INFO", "All steps completed. Transaction committed.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                except Exception as exc:
                    logger.exception("Automated unpick failed for order=%s item=%s wh=%s: %s", order_number, item_number, wh_id, exc)
                    _log_unpick("ERROR", f"All changes rolled back. Error: {exc}", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

            _log_unpick("INFO", "Automated unpick job completed.", run_id=run_id)

        _unpick_interval_hours = int(os.getenv("UNPICK_SCHEDULE_HOURS", "2"))
        global _auto_unpick_scheduler
        _auto_unpick_scheduler = BackgroundScheduler()
        _auto_unpick_scheduler.add_job(
            func=_auto_unpick_job,
            trigger="interval",
            hours=_unpick_interval_hours,
            id="auto_unpick",
            name="Automated Unpick",
            max_instances=1,
            coalesce=True,
            next_run_time=_dt.now(),
        )
        _auto_unpick_scheduler.start()
        atexit.register(lambda: _auto_unpick_scheduler.shutdown())
        logger.info(f"Automated Unpick cron started — runs every {_unpick_interval_hours} hour(s).")
        # --------------------------------------------------------

        # @self.flask_app.route("/auth/login", methods=["GET", "POST"], endpoint="login")
        # def login_page():
        #     return render_template("login.html")  # no 'templates/' prefix

        @self.flask_app.route("/", methods=["GET", "POST"])
        def login():
            return self.auth.login_handler(request)

        @self.flask_app.route("/auth/callback", methods=["GET"])
        def callback():
            try:
                # Define the specific query you want to execute
                specific_query = "select * from t_tychons_archive_log;"

                # Call the run_sql function directly
                result = vn.run_sql_2(user="test_user", id="unique_id_123", sql=specific_query)

                # Process the response if needed
                response_data = result.get_json()  # Convert Flask Response object to JSON

                # Return the result to the user
                return jsonify(response_data), 200

            except Exception as e:
                # Handle any errors
                return jsonify({"type": "error", "message": str(e)}), 500

        @self.flask_app.route("/auth/logout", methods=["GET"])
        def logout():
            uid = session.get('user_id')
            wid = session.get('workspace_id')
            #RBA
            self.cache.clear_workspace_for_user(uid, wid)
            return auth.logout_handler(flask.request)


        @self.flask_app.route("/assets/<path:filename>")
        def proxy_assets(filename):
            if self.assets_folder:
                return send_from_directory(self.assets_folder, filename)

            if ".css" in filename:
                return Response(css_content, mimetype="text/css")

            if ".js" in filename:
                return Response(js_content, mimetype="text/javascript")

            # Return 404
            return "File not found", 404

        # Proxy the /vanna.svg file to the remote server
        @self.flask_app.route("/vanna.svg")
        def proxy_vanna_svg():
            remote_url = "https://vanna.ai/img/vanna.svg"
            response = requests.get(remote_url, stream=True)

            # Check if the request to the remote URL was successful
            if response.status_code == 200:
                excluded_headers = [
                    "content-encoding",
                    "content-length",
                    "transfer-encoding",
                    "connection",
                ]
                headers = [
                    (name, value)
                    for (name, value) in response.raw.headers.items()
                    if name.lower() not in excluded_headers
                ]
                return Response(response.content, response.status_code, headers)
            else:
                return "Error fetching file from remote server", response.status_code

        @self.flask_app.route("/prediction-page")
       
        def prediction_page():
            return Response(prediction_template, mimetype='text/html')
        

        @self.flask_app.route("/anomaly-page")
        def anomaly_page():
            return Response(anomaly_template, mimetype='text/html')

        @self.flask_app.route("/home", defaults={"path": ""})
        @self.flask_app.route("/home/<path:path>")
        def hello(path: str):
            if self.index_html_path:
                directory = os.path.dirname(self.index_html_path)
                filename = os.path.basename(self.index_html_path)
                return send_from_directory(directory=directory, path=filename)
            return html_content
        chroma_db_path = "chroma"
        if not os.path.exists(chroma_db_path):
            os.makedirs(chroma_db_path)

        # # Initialize ChromaDB client and collection
        client = chromadb.PersistentClient(path="D:/Admin-Module/WAI")
        collection = client.get_or_create_collection("DB_connections")
        # Get or create collections
        config_collection = client.get_or_create_collection(name="LLM_config")
        users_collection = client.get_or_create_collection(name="users_collection")
        #llm_data_collection = client.get_or_create_collection(name="LLM_data")




        # @self.flask_app.route("/get-saved-llms", methods=["GET"])
        # def get_saved_llms():
        #     """Retrieve saved LLM configurations from ChromaDB."""
        #     try:
        #         results = config_collection.get()

        #         # Ensure results contain the necessary fields
        #         if not results or not results.get("ids"):
        #             return jsonify([]), 200  # No data found, return empty list

        #         llm_list = []
        #         ids = results.get("ids", [])
        #         metadatas = results.get("metadatas", [{}] * len(ids))  # Ensure metadata length matches ids
                
        #         for i, llm_id in enumerate(ids):
        #             metadata = metadatas[i] if i < len(metadatas) else {}
        #             llm_list.append({
        #                 "id": llm_id,
        #                 "model_type": metadata.get("model_type", "Unknown"),
        #                 "model_name": metadata.get("model_name", "Unnamed Model")
        #             })

        #         return jsonify(llm_list), 200

        #     except Exception as e:
        #         print(f"❌ Error fetching saved LLMs: {e}")
        #         return jsonify({"error": "Failed to fetch saved LLMs"}), 500





        def get_available_models():
            """Fetch locally available Ollama models."""
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
                local_models = [line.split()[0] for line in result.stdout.splitlines() if line and not line.startswith("NAME")]
            except Exception as e:
                print("Error fetching Ollama models:", e)
                local_models = []
            return local_models, local_models + ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "o3"]



        @self.flask_app.route("/user", endpoint="user")
        @self.requires_auth
        def admin(**kwargs):
            """Render the admin dashboard."""
            return render_template("user.html")

        @self.flask_app.route('/api/get_user_workspace_id')
        def get_user_workspace_id():
            user = auth.get_user(request)
            if not auth.is_logged_in(user):
                return jsonify({"error": "User not logged in"}), 401

            workspace_id = auth.get_user_workspace_id(user['username'])
            if workspace_id:
                return jsonify({"workspace_id": workspace_id})
            else:
                return jsonify({"error": "Workspace not found for user"}), 404
        @self.flask_app.route("/admin", endpoint="admin")
        @self.requires_role("admin")
        @self.requires_auth
        def admin(**kwargs):
            """Render the admin dashboard."""
            return render_template("admin.html")
        @self.flask_app.route("/superadmin", endpoint="superadmin")
        @self.requires_role("superadmin")
        @self.requires_auth
        def superadmin(**kwargs):
            """Render the super-admin dashboard."""
            return render_template("superadmin.html")

        @self.flask_app.route("/workspace", endpoint="workspace")
        @self.requires_role("admin")
        @self.requires_auth
        def index(**kwargs):
            """Render index page with available models and last saved config."""
            local_models, available_models = get_available_models()
            
            # Fetch the last stored configuration
            last_config = None
            results = config_collection.get()

            # if "ids" in results and results["ids"]:
            #     try:
            #         sorted_ids = sorted(map(int, results["ids"]))  # Convert to int for sorting
            #         last_id = str(sorted_ids[-1])  # Get the highest ID
            #         last_config_index = results["ids"].index(last_id)
            #         last_config = results["metadatas"][last_config_index]
            #     except Exception as e:
            #         print("Error fetching last config:", e)

            if "ids" in results and results["ids"]:
                try:
                    sorted_ids = sorted(results["ids"])  # Simple string sorting
                    last_id = sorted_ids[-1]  # Last one
                    last_config_index = results["ids"].index(last_id)
                    last_config = results["metadatas"][last_config_index]
                except Exception as e:
                    print("Error fetching last config:", e)


            return render_template_string(index_template, available_models=available_models, last_config=last_config, local_models=local_models)

        saved_llms = []
        #@self.flask_app.route("/save-llm-config", methods=["POST"])
        # def save_llm_config():
        #     """Save model configuration to ChromaDB."""
        #     data = request.json  # Fetch JSON data correctly

        #     model_type = data.get("modelType", "").strip()
        #     model_name = data.get("ollamaModel", "").strip() if model_type == "ollama" else data.get("openaiModel", "").strip()
        #     api_key = data.get("apiKey", "").strip()  # Ensure it’s a string
        #     base_url = data.get("ollamaBaseUrl", "").strip()

        #     if not model_type:
        #         return jsonify({"error": "Model type is required"}), 400
        #     if not model_name:
        #         return jsonify({"error": "Model name is required"}), 400

        #     # Get existing data and generate new ID
        #     existing_data = config_collection.get()
        #     existing_ids = existing_data.get("ids", [])
        #     new_id = str(max(map(int, existing_ids)) + 1 if existing_ids else 1)

        #     print(f"🔹 Saving LLM Config with ID: {new_id}")  # Debugging

        #     # Ensure all metadata fields are strings
        #     metadata = {
        #         "model_type": model_type,
        #         "model_name": model_name,
        #         "api_key": api_key if model_type == "openai" else "",
        #         "base_url": base_url if model_type == "ollama" else "",
        #     }

        #     # FIX: Add a `documents` field to meet ChromaDB requirements
        #     config_collection.add(
        #         ids=[new_id], 
        #         metadatas=[metadata], 
        #         documents=[f"Configuration for {model_name}"]  # Required field
        #     )
        #     logger.info(f"vanna LLM Model - {model_name}")
            
        #     return model_name
            #return jsonify({"message": "Configuration saved successfully"}), 200
        # @self.flask_app.route("/save-llm-config", methods=["POST"])    
        # def save_llm_config():
        #     try:
        #         data = request.get_json()
        #         logger.info(f"Received LLM config data: {data}")

        #         model_type = data.get('modelType')
        #         if not model_type:
        #             logger.warning("No model type provided")
        #             return jsonify({"success": False, "error": "Model type is required"}), 400

        #         # Prepare LLM config
        #         llm_id = str(uuid.uuid4())
        #         llm_config_raw = {
        #             "model_type": model_type,
        #             "model_name": data.get('ollamaModel') if model_type == "ollama" else data.get('openaiModel'),
        #             "base_url": data.get('ollamaBaseUrl') if model_type == "ollama" else None,
        #             "api_key": data.get('apiKey') if model_type == "openai" else None
        #         }

        #         # Validate required fields
        #         if not llm_config_raw["model_name"]:
        #             logger.warning("No model name provided")
        #             return jsonify({"success": False, "error": "Model name is required"}), 400

        #         # Filter out None values from metadata
        #         llm_config = {k: v for k, v in llm_config_raw.items() if v is not None}
        #         logger.info(f"Filtered LLM config for ChromaDB: {llm_config}")

        #         # Save to ChromaDB
        #         config_collection.add(
        #             ids=[llm_id],
        #             metadatas=[llm_config],
        #             documents=[f"{model_type}:{llm_config['model_name']}"]  # Optional document content
        #         )
        #         logger.info(f"Saved LLM to ChromaDB: ID={llm_id}, Config={llm_config}")

        #         return jsonify({
        #             "success": True,
        #             "message": "LLM configuration saved successfully",
        #             "llm_id": llm_id
        #         }), 200

        #     except Exception as e:
        #         logger.error(f"Error saving LLM config to ChromaDB: {str(e)}", exc_info=True)
        #         return jsonify({"success": False, "error": f"Failed to save LLM: {str(e)}"}), 500

        # Existing /get-saved-llms (from your snippet)
        @self.flask_app.route("/get-saved-llms", methods=["GET"])
        def get_saved_llms():
          try:
              results = config_collection.get()
              logger.info(f"ChromaDB get results: {results}")

              if not results or not results.get("ids"):
                  logger.info("No LLMs found in ChromaDB")
                  return jsonify([]), 200

              llm_list = []
              ids = results.get("ids", [])
              metadatas = results.get("metadatas", [{}] * len(ids))

              for i, llm_id in enumerate(ids):
                  llm_id = str(llm_id)  # Ensure IDs are treated as strings
                  metadata = metadatas[i] if i < len(metadatas) else {}

                  llm_list.append({
                      "id": llm_id,
                      "model_type": metadata.get("model_type", "Unknown"),
                      "model_name": metadata.get("model_name", "Unnamed Model"),
                      "base_url": metadata.get("base_url"),  # Include if saved
                      "api_key": metadata.get("api_key")     # Include if saved
                  })

              logger.info(f"Returning LLM list: {llm_list}")
              return jsonify(llm_list), 200

          except Exception as e:
              logger.error(f"Error fetching saved LLMs: {str(e)}", exc_info=True)
              return jsonify({"error": "Failed to fetch saved LLMs"}), 500





        @self.flask_app.route("/get-ollama-models", methods=["GET"])
        def get_ollama_models():
            """Fetch locally available Ollama models."""
            local_models, _ = get_available_models()
            return jsonify({"models": local_models})


        from flask import Flask, request, jsonify
        # import logging

        # Configure logger
        
        #logger.basicConfig(level=logger.ERROR)

        @self.flask_app.route('/log_error', methods=['POST'])
        def log_error():
            data = request.get_json()
            error_message = data.get("error", "Unknown error")
            logger.error(f"Frontend Error: {error_message}")
            return jsonify({"message": "Error logged successfully"}), 200


        @self.flask_app.route("/update-llm/<llm_id>", methods=["PUT"])
        def update_llm(llm_id):
            """Update an LLM config in ChromaDB."""
            data = request.json
            config_collection.update(
                ids=[llm_id],
                metadatas=[data]
            )
            return jsonify({"message": "LLM updated successfully"}), 200

        @self.flask_app.route("/delete-llm/<llm_id>", methods=["DELETE"])
        def delete_llm(llm_id):
            """Delete an LLM from ChromaDB."""
            config_collection.delete(ids=[llm_id])
            return jsonify({"message": "LLM deleted successfully"}), 200


        @self.flask_app.route("/validate-openai-api", methods=["POST"])
        def validate_openai_api():
            """Check if the OpenAI API key is valid."""
            data = request.json
            api_key = data.get("api_key")

            if not api_key:
                return jsonify({"success": False, "error": "API key is required"}), 400

            try:
                openai.api_key = api_key
                openai.models.list()  # Making a test request to validate the key
                return jsonify({"success": True}), 200
            except OpenAIError as e:
                print(f"OpenAI API Error: {e}")
                return jsonify({"success": False, "error": "Invalid API key"}), 401
            except Exception as e:
                print(f"Unexpected Error: {e}")
                return jsonify({"success": False, "error": "Failed to validate API key"}), 500










        def test_db_connection(server, port, database, username, password):
            """Helper function to test MSSQL connection with port."""
            try:
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}'
                conn = pyodbc.connect(conn_str, timeout=5)
                conn.close()
                return True, "Connection successful"
            except Exception as e:
                return False, str(e)







        # @self.flask_app.route("/save_connection", methods=["POST"])
        # def save_connection():
        #     logger.info("started saving function")
        #     data = request.json
        #     server = data.get("serverName")
        #     port = data.get("port")
        #     database = data.get("databaseName")
        #     username = data.get("username")
        #     password = data.get("password")

        #     if not all([server, port, database, username, password]):
        #         return jsonify({"error": "All fields are required"}), 400

        #     success, message = test_db_connection(server, port, database, username, password)

        #     if not success:
        #         return jsonify({"error": f"Connection failed: {message}"}), 400

        #     # Check if a record already exists
        #     existing_records = collection.get()  # Fetch all records from the collection
        #     if existing_records and len(existing_records["ids"]) > 0:
        #         logger.info("updating the first recoed")
        #         first_record_id = existing_records["ids"][0]  # Get the first record ID
        #         collection.update(
        #             ids=[first_record_id],
        #             metadatas=[data],  # Update with new details
        #             documents=["SQL Connection"]
        #         )
        #         return jsonify({"message": "Connection updated successfully"}), 200

        #     # If no records exist, insert a new one
        #     logger.info("new record")
        #     conn_id = str(uuid.uuid4())  # Generate a unique ID
        #     collection.add(
        #         ids=[conn_id],
        #         metadatas=[data],  # Store all connection details
        #         documents=["SQL Connection"]
        #     )
        #     logger.info(f"vanna connection sql - {server}, {port}, {database}, {username}, {password}")

        #     if success:
        #         return vn.connect_to_mssql(odbc_conn_str=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}')
    

        # @self.flask_app.route("/save_connection", methods=["POST"])
        # def save_connection():
        #     logger.info("started saving function")
        #     data = request.json
        #     server = data.get("serverName")
        #     port = data.get("port")
        #     database = data.get("databaseName")
        #     username = data.get("username")
        #     password = data.get("password")

        #     if not all([server, port, database, username, password]):
        #         return jsonify({"error": "All fields are required"}), 400

        #     success, message = test_db_connection(server, port, database, username, password)

        #     if not success:
        #         return jsonify({"error": f"Connection failed: {message}"}), 400

        #     # Check if a record already exists
        #     existing_records = collection.get()  # Fetch all records from the collection
        #     if existing_records and len(existing_records["ids"]) > 0:
        #         logger.info("updating the first record")
        #         first_record_id = existing_records["ids"][0]  # Get the first record ID
        #         collection.update(
        #             ids=[first_record_id],
        #             metadatas=[data],  # Update with new details
        #             documents=["SQL Connection"]
        #         )
        #         return jsonify({"message": "Connection updated successfully"}), 200

        #     # If no records exist, insert a new one
        #     logger.info("new record")
        #     conn_id = str(uuid.uuid4())  # Generate a unique ID
        #     collection.add(
        #         ids=[conn_id],
        #         metadatas=[data],  # Store all connection details
        #         documents=["SQL Connection"]
        #     )
        #     logger.info(f"vanna connection sql - {server}, {port}, {database}, {username}, {password}")
        
        #     # Connect to the database using Vanna
        #     try:
                
        #         vn.connect_to_mssql(odbc_conn_str=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}')
        #         return jsonify({"message": "Connection saved and established successfully"}), 200
        #     except Exception as e:
        #         logger.error(f"Failed to connect to database: {e}")
        #         return jsonify({"error": f"Failed to connect to database: {e}"}), 400

        # @self.flask_app.route("/save_connection", methods=["POST"])
        # def save_connection():
        #     logger.info("Started saving function")
        #     data = request.json
        #     server = data.get("serverName")
        #     port = data.get("port")
        #     database = data.get("databaseName")
        #     username = data.get("username")
        #     password = data.get("password")

        #     if not all([server, port, database, username, password]):
        #         return jsonify({"error": "All fields are required"}), 400

        #     success, message = test_db_connection(server, port, database, username, password)

        #     if not success:
        #         return jsonify({"error": f"Connection failed: {message}"}), 400

        #     # Check if a record already exists
        #     existing_records = collection.get()  # Fetch all records
        #     if existing_records and len(existing_records["ids"]) > 0:
        #         logger.info("Updating the first record")
        #         first_record_id = existing_records["ids"][0]  # Get first record ID
        #         collection.update(
        #             ids=[first_record_id],
        #             metadatas=[data],  # Update with new details
        #             documents=["SQL Connection"]
        #         )
        #         logger.info("Database configuration updated successfully.")

        #     else:
        #         # If no records exist, insert a new one
        #         logger.info("Inserting a new database configuration.")
        #         conn_id = str(uuid.uuid4())  # Generate unique ID
        #         collection.add(
        #             ids=[conn_id],
        #             metadatas=[data],  # Store all connection details
        #             documents=["SQL Connection"]
        #         )
            
        #     # Fetch the updated record again to ensure latest data is used
        #     updated_records = collection.get()
        #     if not updated_records or len(updated_records["ids"]) == 0:
        #         return jsonify({"error": "Failed to retrieve updated database configuration"}), 500

        #     # Extract the latest saved connection details
        #     latest_metadata = updated_records["metadatas"][0]
        #     updated_server = latest_metadata.get("serverName")
        #     updated_port = latest_metadata.get("port")
        #     updated_database = latest_metadata.get("databaseName")
        #     updated_username = latest_metadata.get("username")
        #     updated_password = latest_metadata.get("password")

        #     # Connect to the database using the updated details
        #     try:
        #         # vn.connect_to_mssql(odbc_conn_str=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}')
        #         #vn.connect_to_mssql( odbc_conn_str =f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={updated_server},{updated_port};DATABASE={updated_database};UID={updated_username};PWD={updated_password}')
        #         # vn.connect_to_mssql(odbc_conn_str=odbc_conn_str)db_id
        #         logger.info("Successfully connected to the database after update.")
        #         return jsonify({
        #             "success": True,
        #             "message": "DB configuration saved successfully",
        #             "db_id": updated_records["ids"][0] 
        #         }), 200
        #     except Exception as e:
        #         logger.error(f"Failed to connect to database: {e}")
        #         return jsonify({"error": f"Failed to connect to database: {e}"}), 400



        @self.flask_app.route("/test_connection", methods=["POST"])
        def test_connection():
            logger.info("started testing function")

            data = request.json
            server = data.get("serverName")
            port = data.get("port")  # Capture port
            database = data.get("databaseName")
            username = data.get("username")
            password = data.get("password")

            if not all([server, port, database, username, password]):
                return jsonify({"error": "All fields are required"}), 400

            success, message = test_db_connection(server, port, database, username, password)
            logger.info(f"vanna connection sql - {server}, {port}, {database}, {username}, {password}")
            if success:
                # vn.connect_to_mssql(odbc_conn_str=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}')

                return jsonify({"message": "Connection successful"}), 200
            else:
                return jsonify({"error": f"Connection failed: {message}"}), 400
            


        @self.flask_app.route("/get_connections", methods=["GET"])
        def get_connections():
            logger.info("started getting function in get connection")
            connections = collection.get(ids=None)  # Retrieve all records

            if connections and "metadatas" in connections and "ids" in connections:
                result = []
                for i in range(len(connections["metadatas"])):
                    conn_data = connections["metadatas"][i]
                    conn_data["conn_id"] = connections["ids"][i]  # Attach unique ID
                    result.append(conn_data)
                    logger.info(f"result from get connection {result}")

                return jsonify(result)  # Send modified response

            return jsonify({"error": "No connections found"}), 404


        @self.flask_app.route("/delete_connection", methods=["DELETE"])
        def delete_connection():
            logger.info("started delete function")
            data = request.json
            conn_id = data.get("conn_id")  # Expecting a unique ID for deletion

            if not conn_id:
                return jsonify({"error": "Connection ID is required"}), 400

            # Check if the ID exists before deleting
            existing_connections = collection.get(ids=[conn_id])
            if not existing_connections or "metadatas" not in existing_connections or not existing_connections["metadatas"]:
                return jsonify({"error": "Connection ID not found"}), 404

            collection.delete(ids=[conn_id])
            return jsonify({"message": "Connection deleted successfully"}), 200
        





     
        # vn = None
        
        # @self.flask_app.route("/connect-vanna", methods=["POST"])


        # def connect_vanna():
        #     global vn  # Ensure we use the global vn
        #     data = request.json
        #     model_name = data.get("model_name")

        #     if not model_name:
        #         return jsonify({"success": False, "error": "No model selected"}), 400

        #     try:
        #         # Initialize a new Vanna instance with the selected model
        #         vn = MyVanna(config={'model': model_name})
        #         vn.connect_to_mssql(odbc_conn_str="DRIVER={ODBC Driver 17 for SQL Server};SERVER=TYC-335;1433;DATABASE=Demo;UID=suriyan;pwd=12345")

        #         return jsonify({"success": True, "message": f"Connected Vanna with model: {model_name}"})
        #     except Exception as e:
        #         return jsonify({"success": False, "error": str(e)}), 500



#----------------------------------------------------------------------------------------------------------------------------------
        #vanna_api = VannaFlaskAPI()
        #@self.flask_app.route("/connect-vanna", methods=["POST"])
        # def connect_vanna():
        #     global vn  # Ensure we use the global vn
        #     try:
        #         data = request.json  # Fetch JSON data correctly
        #         logger.info(f"Data received: {data}")
        #         model_name = data.get("model_name")
        #         logger.info(f"Selected model: {model_name}")

        #         if not model_name:
        #             return jsonify({"success": False, "error": "No model selected"}), 400

        #         # Initialize the Vanna instance based on the selected model
        #         if model_name == "gpt-4":
        #             class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
        #                 def __init__(self, config=None):
        #                     ChromaDB_VectorStore.__init__(self, config=config)
        #                     OpenAI_Chat.__init__(self, config=config)

        #             vn = MyVanna(config={
        #                 'api_key': '<redacted>',
        #                 'model': 'gpt-4',
        #                 'allow_llm_to_see_data': True
        #             })
        #             logger.info("Initialized GPT-4 model")
        #         elif model_name == "granite3-dense:8b":
        #             class MyVanna(ChromaDB_VectorStore, Ollama):
        #                 def __init__(self, config=None):
        #                     ChromaDB_VectorStore.__init__(self, config=config)
        #                     Ollama.__init__(self, config=config)

        #             vn = MyVanna(config={
        #                 'model': 'granite3-dense:8b',
        #                 'allow_llm_to_see_data': True
        #             })
        #             logger.info("Initialized Ollama model")
        #         else:
        #             return jsonify({"success": False, "error": f"Unsupported model: {model_name}"}), 400

        #         # Connect to the database
        #         #vn.connect_to_mssql(odbc_conn_str="DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-TOE82GG;DATABASE=Dinesh_db;UID=DESKTOP-TOE82GG\\Tychons;Trusted_connection=yes")
        #         vn.connect_to_mssql(
        #                                 odbc_conn_str="DRIVER={ODBC Driver 17 for SQL Server};"
        #                                               "SERVER=DESKTOP-TOE82GG,1433;"
        #                                               "DATABASE=demo_1;"
        #                                               "UID=user;"
        #                                               "PWD=12345;"
        #                             )

        #         logger.info("Successfully connected to the database")

        #         # Assign the vn instance to the global vn
        #         vanna_api.vn = vn

        #         return jsonify({"success": True, "message": f"Connected Vanna with model: {model_name}"}), 200

        #     except Exception as e:
        #         logger.error(f"Failed to connect Vanna: {e}")
        #         return jsonify({"success": False, "error": str(e)}), 500
                
    # def get_latest_saved_model(self):
    #     """Retrieve the most recently saved LLM model from ChromaDB."""
    #     if not hasattr(self, "config_collection"):
    #         raise AttributeError("config_collection is not initialized")

    #     existing_data = self.config_collection.get()
    #     if not existing_data or not existing_data.get("ids"):
    #         return None  # No models found

    #     latest_id = max(map(int, existing_data["ids"]))  # Get latest ID
    #     latest_metadata = self.config_collection.get(ids=[str(latest_id)]).get("metadatas")[0]

    #     return latest_metadata.get("model_name")  # Return latest model name



        # Workspace-related endpoints using ChromaDB
        # @self.flask_app.route('/save_workspace', methods=['POST'])
        # def save_workspace():
        #     try:
        #         data = request.get_json()
        #         workspace_id = str(uuid.uuid4())

        #         name = data.get("name")
        #         llm_id = data.get("llm_id")
        #         db_id = data.get("db_id")
        #         training_id = data.get("training_id")

        #         if not name or not llm_id or not db_id:
        #             return jsonify({"error": "Name, LLM ID, and DB ID are required"}), 400

        #         llm_results = self.config_collection.get(ids=[llm_id])
        #         logger.info(f"LLM Results: {llm_results}")
        #         if not llm_results.get("metadatas"):
        #             return jsonify({"error": f"LLM with ID {llm_id} not found"}), 404
        #         llm_config = llm_results["metadatas"][0]
        #         if not llm_config.get("model_name"):
        #             logger.warning(f"LLM config for ID {llm_id} missing model_name: {llm_config}")

        #         db_results = self.db_collection.get(ids=[db_id])
        #         logger.info(f"DB Results: {db_results}")
        #         if not db_results.get("metadatas"):
        #             return jsonify({"error": f"DB with ID {db_id} not found"}), 404
        #         db_config = db_results["metadatas"][0]
        #         if not db_config.get("databaseName"):
        #             logger.warning(f"DB config for ID {db_id} missing databaseName: {db_config}")

        #         workspace_metadata = {
        #             "name": name,
        #             "llm_config": json.dumps(llm_config if llm_config else {}),
        #             "db_config": json.dumps(db_config if db_config else {}),
        #             "training_id": training_id if training_id is not None else ""
        #         }
        #         logger.info(f"Workspace Metadata: {workspace_metadata}")

        #         self.workspace_collection.add(
        #             ids=[workspace_id],
        #             metadatas=[workspace_metadata],
        #             documents=[f"Workspace: {name}"]
        #         )

        #         logger.info(f"Saved workspace: ID={workspace_id}, Name={name}")
        #         return jsonify({"message": "Workspace saved successfully", "id": workspace_id}), 200
        #     except Exception as e:
        #         logger.error(f"Error saving workspace: {str(e)}", exc_info=True)
        #        return jsonify({"error": "Failed to save workspace"}), 500

        vanna_api = VannaFlaskAPI()
        @self.flask_app.route("/connect-vanna", methods=["POST"])
        def connect_vanna():
            global vn  # Use the global vn instance
            try:
                # Fetch and log the incoming JSON data
                data = request.get_json()
                workspace_id = data.get("workspace_id")
                session["workspace_id"] = workspace_id


                # Extract LLM details
                llm_details = data.get('llm_details', {})
                model_name = llm_details.get('model_name')
                model_type = llm_details.get('model_type')
                api_key = llm_details.get('api_key')
                base_url = llm_details.get('base_url')
                logger.info(f"LLM Details - Model Name: {model_name}, Model Type: {model_type}, Base URL: {base_url}", extra={"admin": True})

                # Validate model_name
                if not model_name:
                    logger.warning("No model name provided in llm_details", extra={"admin": True})
                    logger.warning("No model name provided in llm_details", extra={"user": True})
                    return jsonify({"success": False, "error": "No model selected"}), 400

                # Extract DB details
                db_details = data.get('db_details', {})
                server_name = db_details.get('serverName')
                port = db_details.get('port')
                database_name = db_details.get('databaseName')
                username = db_details.get('username')
                password = db_details.get('password')
                logger.info(f"DB Details -  Database: {database_name}", extra={"admin": True})
                logger.info(f"DB Details -  Database: {database_name}", extra={"user": True})

                # Optional secondary DB (dual-DB workspace): linked-server alias only,
                # no separate live connection — reached from the primary connection
                # via a SQL Server linked server configured between the two instances.
                db_details_b = data.get('db_details_b') or {}

                # Validate DB details
                if not all([server_name, port, database_name, username, password]):
                    logger.warning("Incomplete database details provided", extra={"admin": True})
                    logger.warning("Incomplete database details provided", extra={"user": True})
                    return jsonify({"success": False, "error": "Incomplete database connection details"}), 400

                # Initialize Vanna based on model_type and model_name
                if model_type == "openai":
                    if not api_key:
                        logger.warning("API key missing for OpenAI model", extra={"admin": True})
                        logger.warning("API key missing for OpenAI model", extra={"user": True})
                        return jsonify({"success": False, "error": "API key is required for OpenAI models"}), 400

                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)

                    vn = MyVanna(config={
                        'api_key': api_key,
                        'model': model_name,
                        'allow_llm_to_see_data': True
                    })
                    logger.info(f"Initialized OpenAI model: {model_name} with provided API key", extra={"admin": True})

                elif model_type == "ollama":
                    class MyVanna(ChromaDB_VectorStore, Ollama):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            Ollama.__init__(self, config=config)

                    vn = MyVanna(config={
                        'model': model_name,
                        #'base_url': base_url if base_url else 'http://127.0.0.1:11434/',  # Default if not provided
                        'allow_llm_to_see_data': True
                    })
                    logger.info(f"Connect-Vanna Initialized Ollama model: {model_name} with base URL: {base_url or 'default'}", extra={"admin": True})

                else:
                    logger.warning(f"Unsupported model type: {model_type}", extra={"admin": True})
                    logger.warning(f"Unsupported model type: {model_type}", extra={"user": True})
                    return jsonify({"success": False, "error": f"Unsupported model type: {model_type}"}), 400

                # Construct ODBC connection string
                odbc_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={server_name},{port};"
                    f"DATABASE={database_name};"
                    f"UID={username};"
                    f"PWD={password};"
                )
                logger.info(f"ODBC Connection String: {odbc_conn_str.replace(password, '****')}")  # Mask password in logs

                # Connect to the database
                vn.connect_to_mssql(odbc_conn_str=odbc_conn_str)
                logger.info(f"Connect-Vanna Successfully connected to the MSSQL database {odbc_conn_str}")

                # Record primary/secondary DB aliases on the vn instance for cross-DB
                # SQL qualification (see get_sql_prompt). No live connection is opened
                # to the secondary DB — it's reached either via same-instance three-part
                # naming (if both databases share the same server+port) or a linked
                # server (if genuinely separate servers) — get_sql_prompt picks the
                # right form using vn.same_instance.
                vn.primary_db_alias = db_details.get("db_alias") or "PRIMARY"
                vn.primary_db_name = database_name
                if db_details_b.get("databaseName"):
                    vn.secondary_db_alias = db_details_b.get("db_alias") or "SECONDARY"
                    vn.secondary_db_name = db_details_b.get("databaseName")
                    vn.same_instance = (
                        str(db_details_b.get("serverName") or "").strip().lower() == str(server_name or "").strip().lower()
                        and str(db_details_b.get("port") or "").strip() == str(port or "").strip()
                    )
                else:
                    vn.secondary_db_alias = None
                    vn.secondary_db_name = None
                    vn.same_instance = False

                # Assign the vn instance to the global vn (assuming vanna_api.vn is for external use)
                # If vanna_api is a module, ensure it's imported correctly
                # For now, assuming it's a typo or external reference; we'll just set the global vn
                vanna_api.vn = vn  # Uncomment and fix if vanna_api is defined elsewhere
                self.vn = vn # Assign to self.vn for class usage

                logger.info(f"Vanna fully initialized with model: {model_name} and database: {database_name}", extra={"admin": True})
                user_id = session.get('user_id')
                #RBA
                self.cache.refresh_cache_for_user(user_id, workspace_id)
                return jsonify({"success": True, "redirect": url_for('hello')}), 200


            except Exception as e:
                logger.error(f"Failed to connect Vanna: {str(e)}", exc_info=True, extra={"admin": True})  # Include stack trace
                logger.error(f"Failed to connect Vanna: {str(e)}", exc_info=True, extra={"user": True})  # Include stack trace
                return jsonify({"success": False, "error": str(e)}), 500

        @self.flask_app.route("/_debug/cache_contents")
        def debug_cache():
            logger.info(f"debug_cache", extra={"flow":True})
            uid = session.get("user_id")
            wid = session.get("workspace_id")
            user_name = session.get("username")
            Cache = self.cache.get_all(["question","sql", "summary"], user_id=uid,)
            data = {
            "user_id": uid,
            "workspace_id": wid,
            "username": user_name,
            "cache count": len(Cache),
            "cache_keys": list(self.cache.user_caches.get(uid, {}).get(str(wid), {}).keys() if uid and wid else []),
            "get_all": Cache
            }

            # Use json.dumps with sort_keys=False to preserve insertion order
            return Response(
                json.dumps(data, sort_keys=False),
                mimetype="application/json"
            )
        
        @self.flask_app.route("/_debug/cache_contents/<user_id>")
        def debug_user_cache(user_id):
            logger.info(f"debug_user_cache", extra={"flow":True})
            uid = user_id
            wid = session.get("workspace_id")
            user_name = session.get("username")
            Cache = self.cache.get_all(["question","sql","summary"], user_id=uid,)
            return jsonify({
                "user_id": uid,
                "workspace_id": wid,
                "username": user_name,
                "cache_keys": list(self.cache.user_caches.get(uid, {}).get(str(wid), {}).keys() if uid and wid else []),
                # "get_all": vanna_api.cache.get_all(["question","sql","summary","fig_json"], user_id=uid, workspace_id=wid)
                "get_all": Cache,
                "cache count": len(Cache)
            })
        @self.flask_app.route("/_cache")
        def cache():
            logger.info(f"cache", extra={"flow":True})
            try:
                return jsonify(self.cache.user_caches)
            except Exception:
                return jsonify(self.cache.get_all(["question","sql","summary", "detected_language"]))

        # @self.flask_app.route('/get_workspaces', methods=['GET'])
        # def get_workspaces():
        #     try:
        #         results = self.workspace_collection.get()
        #         if not results or not results.get("ids"):
        #             return jsonify([]), 200

        #         workspace_list = []
        #         ids = results.get("ids", [])
        #         metadatas = results.get("metadatas", [{}] * len(ids))

        #         for i, workspace_id in enumerate(ids):
        #             metadata = metadatas[i] if i < len(metadatas) else {}
        #             workspace_data = {
        #                 "id": workspace_id,
        #                 "name": metadata.get("name", "Unnamed Workspace"),
        #                 "llm_config": json.loads(metadata.get("llm_config", "{}")),
        #                 "db_config": json.loads(metadata.get("db_config", "{}")),
        #                 "training_id": metadata.get("training_id")
        #             }
        #             logger.info(f"Workspace Data: {workspace_data}")
        #             workspace_list.append(workspace_data)

        #         return jsonify(workspace_list), 200
        #     except Exception as e:
        #         logger.error(f"Error fetching workspaces: {str(e)}", exc_info=True)
        #         return jsonify({"error": "Failed to fetch workspaces"}), 500

        # Add this route to your Flask application for dynamic TTL management
        @self.flask_app.route("/_cache/ttl", methods=["GET", "POST"])
        @self.requires_auth
        def manage_cache_ttl(user: any):
            """
            Get or update cache TTL settings
            ---
            GET:
            responses:
                200:
                schema:
                    type: object
                    properties:
                    current_ttl_seconds:
                        type: integer
                    current_ttl_minutes:
                        type: integer
            POST:
            parameters:
                - name: ttl_minutes
                in: body
                type: integer
                required: true
                description: New TTL in minutes
            responses:
                200:
                schema:
                    type: object
                    properties:
                    success:
                        type: boolean
                    old_ttl_seconds:
                        type: integer
                    new_ttl_seconds:
                        type: integer
                    message:
                        type: string
            """
            logger.info(f"manage_cache_ttl", extra={"flow": True})
            
            if request.method == "GET":
                # Get current TTL
                current_ttl = self.cache.heavy_cache_ttl_seconds
                return jsonify({
                    "current_ttl_seconds": current_ttl,
                    "current_ttl_minutes": current_ttl // 60
                })
            
            elif request.method == "POST":
                # Update TTL
                try:
                    data = request.get_json()
                    ttl_minutes = data.get("ttl_minutes")
                    
                    if ttl_minutes is None:
                        return jsonify({
                            "success": False,
                            "error": "ttl_minutes is required"
                        }), 400
                    
                    # Validate
                    try:
                        ttl_minutes = int(ttl_minutes)
                        if ttl_minutes < 1:
                            return jsonify({
                                "success": False,
                                "error": "ttl_minutes must be at least 1"
                            }), 400
                        if ttl_minutes > 1440:  # Max 24 hours
                            return jsonify({
                                "success": False,
                                "error": "ttl_minutes cannot exceed 1440 (24 hours)"
                            }), 400
                    except ValueError:
                        return jsonify({
                            "success": False,
                            "error": "ttl_minutes must be an integer"
                        }), 400
                    
                    old_ttl = self.cache.heavy_cache_ttl_seconds
                    new_ttl = ttl_minutes * 60
                    
                    self.cache.update_cache_ttl(new_ttl)
                    
                    return jsonify({
                        "success": True,
                        "old_ttl_seconds": old_ttl,
                        "new_ttl_seconds": new_ttl,
                        "old_ttl_minutes": old_ttl // 60,
                        "new_ttl_minutes": ttl_minutes,
                        "message": f"Cache TTL updated from {old_ttl // 60} minutes to {ttl_minutes} minutes"
                    })
                
                except Exception as e:
                    logger.exception("Error updating cache TTL", extra={"cache": True})
                    return jsonify({
                        "success": False,
                        "error": str(e)
                    }), 500


        @self.flask_app.route("/_cache/stats", methods=["GET"])
        @self.requires_auth
        def get_cache_stats(user: any):
            """
            Get cache statistics
            ---
            responses:
            200:
                schema:
                type: object
                properties:
                    total_questions:
                    type: integer
                    questions_with_df:
                    type: integer
                    questions_with_fig:
                    type: integer
                    questions_with_summary:
                    type: integer
                    ttl_seconds:
                    type: integer
            """
            logger.info(f"get_cache_stats", extra={"flow": True})
            
            try:
                user_id = user.get('id') if isinstance(user, dict) else None
                workspace_id = session.get("workspace_id")
                
                uid, wid = self.cache._resolve_user_workspace(user_id, workspace_id)
                
                if uid is None or wid is None:
                    return jsonify({
                        "total_questions": 0,
                        "questions_with_df": 0,
                        "questions_with_fig": 0,
                        "questions_with_summary": 0,
                        "ttl_seconds": self.cache.heavy_cache_ttl_seconds
                    })
                
                workspace_map = self.cache.user_caches.get(uid, {}).get(wid, {})
                
                stats = {
                    "total_questions": len(workspace_map),
                    "questions_with_df": 0,
                    "questions_with_fig": 0,
                    "questions_with_summary": 0,
                    "ttl_seconds": self.cache.heavy_cache_ttl_seconds,
                    "ttl_minutes": self.cache.heavy_cache_ttl_seconds // 60
                }
                
                for entry in workspace_map.values():
                    if isinstance(entry, dict):
                        if "df" in entry and entry.get("df") is not None:
                            stats["questions_with_df"] += 1
                        if "fig_json" in entry and entry.get("fig_json") is not None:
                            stats["questions_with_fig"] += 1
                        if "summary" in entry and entry.get("summary") is not None:
                            stats["questions_with_summary"] += 1
                
                return jsonify(stats)
            
            except Exception as e:
                logger.exception("Error getting cache stats", extra={"cache": True})
                return jsonify({"error": str(e)}), 500


        @self.flask_app.route("/_cache/force_evict", methods=["GET","POST"])
        @self.requires_auth
        def force_cache_eviction(user: any):
            """
            Manually trigger cache eviction (useful for testing or forcing cleanup)
            ---
            responses:
            200:
                schema:
                type: object
                properties:
                    success:
                    type: boolean
                    message:
                    type: string
            """
            logger.info(f"force_cache_eviction", extra={"flow": True})
            
            try:
                self.cache._evict_stale_entries()
                return jsonify({
                    "success": True,
                    "message": "Cache eviction triggered successfully"
                })
            except Exception as e:
                logger.exception("Error forcing cache eviction", extra={"cache": True})
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500


        @self.flask_app.route('/get_workspaces', methods=['GET'])
        def get_workspaces():
            try:
                results = self.workspace_collection.get()
                if not results or not results.get("ids"):
                    return jsonify([]), 200

                workspace_list = []
                ids = results.get("ids", [])
                metadatas = results.get("metadatas", [{}] * len(ids))

                for i, workspace_id in enumerate(ids):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    workspace_data = {
                        "id": workspace_id,
                        "name": metadata.get("name", "Unnamed_Workspace"),  # underscore version
                        "display_name": metadata.get("display_name", metadata.get("name")),  # original version
                        "llm_config": json.loads(metadata.get("llm_config", "{}")),
                        "db_config": json.loads(metadata.get("db_config", "{}")),
                        "training_id": metadata.get("training_id")
                    }
                    logging.info(f"Workspace Data: {workspace_data}")
                    workspace_list.append(workspace_data)

                return jsonify(workspace_list), 200
            except Exception as e:
                logging.error(f"Error fetching workspaces: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to fetch workspaces"}), 500




        @self.flask_app.route('/update_workspace/<uuid:id>', methods=['PUT'])
        def update_workspace(id):
            try:
                id_str = str(id)
                data = request.get_json()
                existing = self.workspace_collection.get(ids=[id_str])
                if not existing.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404

                name = data.get("name")
                llm_id = data.get("llm_id")
                db_id = data.get("db_id")
                training_id = data.get("training_id")

                if not name or not llm_id or not db_id:
                    return jsonify({"error": "Name, LLM ID, and DB ID are required"}), 400

                llm_results = self.config_collection.get(ids=[llm_id])
                if not llm_results.get("metadatas"):
                    return jsonify({"error": f"LLM with ID {llm_id} not found"}), 404
                llm_config = llm_results["metadatas"][0]

                db_results = self.db_collection.get(ids=[db_id])
                if not db_results.get("metadatas"):
                    return jsonify({"error": f"DB with ID {db_id} not found"}), 404
                db_config = db_results["metadatas"][0]

                updated_metadata = {
                    "name": name,
                    "llm_config": json.dumps(llm_config),
                    "db_config": json.dumps(db_config),
                    "training_id": training_id if training_id is not None else ""
                }

                self.workspace_collection.update(
                    ids=[id_str],
                    metadatas=[updated_metadata],
                    documents=[f"Workspace: {name}"]
                )

                logger.info(f"Updated workspace: ID={id_str}, Name={name}", extra={"admin": True})
                return jsonify({"message": "Workspace updated successfully"}), 200
            except Exception as e:
                logger.error(f"Error updating workspace with ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Failed to update workspace"}), 500

        # @self.flask_app.route('/delete_workspace/<uuid:id>', methods=['DELETE'])
        # def delete_workspace(id):
        #     try:
        #         id_str = str(id)
        #         existing = self.workspace_collection.get(ids=[id_str])
        #         if not existing.get("metadatas"):
        #             return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404

        #         self.workspace_collection.delete(ids=[id_str])
        #         logger.info(f"Deleted workspace: ID={id_str}")
        #         return jsonify({"message": "Workspace deleted successfully"}), 200
        #     except Exception as e:
        #         logger.error(f"Error deleting workspace with ID {id}: {str(e)}", exc_info=True)
        #         return jsonify({"error": "Failed to delete workspace"}), 500











































































































































































































































































































































































































        @self.flask_app.route('/delete_workspace/<uuid:id>', methods=['DELETE'])
        def delete_workspace(id):
            try:
                id_str = str(id)
                # Fetch workspace metadata
                existing = self.workspace_collection.get(ids=[id_str])
                if not existing.get("metadatas"):
                    logger.error(f"Workspace with ID {id_str} not found in workspace_collection", extra={"admin": True})
                    return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404
 
                workspace_name = existing["metadatas"][0]["name"]
                if not workspace_name:
                    logger.error(f"Workspace name not found for ID {id_str}", extra={"admin": True})
                    return jsonify({"error": "Workspace name not found"}), 404
 
                # Ensure vn is initialized

                global vn
                if vn is None:
                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)
                    logger.info("vn is None, initializing MyVanna", extra={"admin": True})
                    vn = MyVanna(config={'allow_llm_to_see_data': 'True'})
 
                # Check if chroma_client is available
                if not hasattr(vn, 'chroma_client') or vn.chroma_client is None:
                    logger.error("ChromaDB client not initialized in MyVanna", extra={"admin": True})
                    return jsonify({"error": "ChromaDB client not initialized"}), 500
 
                # Log all collections before deletion for debugging
                collection_names = vn.chroma_client.list_collections()
                logger.info(f"Current ChromaDB collections: {collection_names}", extra={"admin": True})

                # Check if the collection exists before attempting deletion
                collection_exists = workspace_name in collection_names
                if collection_exists:
                    try:
                        vn.chroma_client.delete_collection(name=workspace_name)
                        logger.info(f"Successfully deleted ChromaDB collection: {workspace_name}", extra={"admin": True})
                    except Exception as e:
                        logger.error(f"Failed to delete ChromaDB collection {workspace_name}: {str(e)}", exc_info=True, extra={"admin": True})
                        return jsonify({"error": f"Failed to delete training data collection: {str(e)}"}), 500
                else:
                    logger.warning(f"No ChromaDB collection found for workspace: {workspace_name}", extra={"admin": True})

 
                # Delete the workspace from the workspace collection
                self.workspace_collection.delete(ids=[id_str])
                logger.info(f"Successfully deleted workspace: ID={id_str}", extra={"admin": True})
 
                # Verify deletion
                collections_after = vn.chroma_client.list_collections()
                collection_names_after = vn.chroma_client.list_collections()
                if workspace_name in collection_names_after:
                    logger.error(f"ChromaDB collection {workspace_name} still exists after deletion attempt", extra={"admin": True})
                    return jsonify({"error": f"Failed to delete ChromaDB collection {workspace_name}"}), 500

 
                return jsonify({"message": "Workspace and associated training data deleted successfully"}), 200
            except Exception as e:
                logger.error(f"Error deleting workspace with ID {id_str}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": f"Failed to delete workspace: {str(e)}"}), 500



















        @self.flask_app.route('/connect_workspace/<uuid:id>', methods=['POST'])
        def connect_workspace(id):
            global vn
            try:
                id_str = str(id)
                results = self.workspace_collection.get(ids=[id_str])
                if not results.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404

                workspace = results["metadatas"][0]
                logger.info(f"Get-Workspace {workspace}", extra={"admin": True})
                llm_config = json.loads(workspace.get("llm_config", "{}"))
                db_config = json.loads(workspace.get("db_config", "{}"))

                data_to_send = {
                    "llm_details": {
                        "model_name": llm_config.get("model_name"),
                        "model_type": llm_config.get("model_type"),
                        "api_key": llm_config.get("api_key"),
                        "base_url": llm_config.get("base_url")
                    },
                    "db_details": {
                        "serverName": db_config.get("serverName"),
                        "port": db_config.get("port"),
                        "databaseName": db_config.get("databaseName"),
                        "username": db_config.get("username"),
                        "password": db_config.get("password")
                    }
                }

                response = requests.post(
                    url_for('connect_vanna', _external=True),
                    json=data_to_send,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    logger.info(f"Connected to workspace: ID={id_str}, Name={workspace.get('name')}", extra={"admin": True})
                    return jsonify({"message": "Workspace connected successfully"}), 200
                else:
                    logger.error(f"Failed to connect workspace: {response.text}", extra={"admin": True})
                    return jsonify({"error": "Failed to connect workspace", "details": response.text}), response.status_code
            except Exception as e:
                logger.error(f"Error connecting workspace with ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Failed to connect workspace"}), 500

        @self.flask_app.route('/get_workspace/<uuid:id>', methods=['GET'])
        def get_workspace(id):
            try:
                logger.info(f"Received ID: {id}, Type: {type(id)}")
                id_str = str(id)
                results = self.workspace_collection.get(ids=[id_str])
                if not results.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404
                metadata = results["metadatas"][0]
                response = {
                    "id": id_str,
                    "name": metadata.get("name"),
                    "llm_config": json.loads(metadata["llm_config"]) if "llm_config" in metadata else {},
                    "db_config": json.loads(metadata["db_config"]) if "db_config" in metadata else {},
                    "db_config_b": json.loads(metadata["db_config_b"]) if "db_config_b" in metadata else {},
                    "training_id": metadata.get("training_id")
                }
                logger.info(f"Returning workspace data: {response}")
                return jsonify(response)
            except ValueError as e:
                logger.error(f"ValueError processing ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": f"Invalid ID format: {str(e)}"}), 400
            except Exception as e:
                logger.error(f"Error fetching workspace with ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": f"Failed to fetch workspace: {str(e)}"}), 500
#---------------------------------------------------------Updated Code---------------------------------------

        # @self.flask_app.route('/save_workspace', methods=['POST'])
        # def save_workspace():
        #     try:
        #         data = request.get_json()
        #         workspace_id = str(uuid.uuid4())
        #         name = data.get("name")

        #         if not name:
        #             return jsonify({"error": "Workspace name is required"}), 400

        #         # Initialize with empty configs if not provided
        #         workspace_metadata = {
        #             "name": name,
        #             "llm_config": json.dumps({}),  # Empty LLM config
        #             "db_config": json.dumps({}),   # Empty DB config
        #             "training_id": ""
        #         }
        #         logger.info(f"Workspace Metadata: {workspace_metadata}")

        #         self.workspace_collection.add(
        #             ids=[workspace_id],
        #             metadatas=[workspace_metadata],
        #             documents=[f"Workspace: {name}"]
        #         )

        #         logger.info(f"Saved workspace: ID={workspace_id}, Name={name}")
        #         return jsonify({"message": "Workspace saved successfully", "id": workspace_id}), 200
        #     except Exception as e:
        #         logger.error(f"Error saving workspace: {str(e)}", exc_info=True)
        #         return jsonify({"error": "Failed to save workspace"}), 500




        # @self.flask_app.route('/save_workspace', methods=['POST'])
        # def save_workspace():
        #     try:
        #         data = request.get_json()
        #         workspace_id = str(uuid.uuid4())
        #         original_name = data.get("name")

        #         if not original_name:
        #             return jsonify({"error": "Workspace name is required"}), 400

        #         # Replace spaces with underscores for storage
        #         sanitized_name = original_name.replace(" ", "_")

        #         workspace_metadata = {
        #             "name": sanitized_name,           # storage-safe name
        #             "display_name": original_name,    # original name for UI
        #             "llm_config": json.dumps({}),
        #             "db_config": json.dumps({}),
        #             "training_id": ""
        #         }

        #         logger.info(f"Workspace Metadata: {workspace_metadata}", extra={"admin": True})

        #         self.workspace_collection.add(
        #             ids=[workspace_id],
        #             metadatas=[workspace_metadata],
        #             documents=[f"Workspace: {original_name}"]  # keep readable
        #         )

        #         logger.info(f"Saved workspace: ID={workspace_id}, Name={sanitized_name}", extra={"admin": True})
        #         return jsonify({
        #             "message": "Workspace saved successfully",
        #             "id": workspace_id
        #         }), 200

        #     except Exception as e:
        #         logger.error(f"Error saving workspace: {str(e)}", exc_info=True, extra={"admin": True})
        #         return jsonify({"error": "Failed to save workspace"}), 500






        @self.flask_app.route('/save_workspace', methods=['POST'])
        def save_workspace():
            try:
                data = request.get_json()
                workspace_id = str(uuid.uuid4())
                original_name = data.get("name")

                if not original_name:
                    return jsonify({"error": "Workspace name is required"}), 400

                # Replace spaces with underscores for storage
                sanitized_name = original_name.replace(" ", "_")

                # --- 🔍 Check for duplicate workspace (case-insensitive match on display_name) ---
                existing = self.workspace_collection.get()
                if existing and existing.get("metadatas"):
                    for meta in existing.get("metadatas"):
                        if meta and meta.get("display_name", "").lower() == original_name.lower():
                            logging.warning(f"Duplicate workspace name attempted: {original_name}")
                            return jsonify({
                                "error": f"A workspace with the name '{original_name}' already exists."
                            }), 400

                # -------------------------------------------------------------------------------

                workspace_metadata = {
                    "name": sanitized_name,           # storage-safe name
                    "display_name": original_name,    # original name for UI
                    "llm_config": json.dumps({}),
                    "db_config": json.dumps({}),
                    "training_id": ""
                }

                logging.info(f"Workspace Metadata: {workspace_metadata}")

                self.workspace_collection.add(
                    ids=[workspace_id],
                    metadatas=[workspace_metadata],
                    documents=[f"Workspace: {original_name}"]
                )

                logging.info(f"Saved workspace: ID={workspace_id}, Name={sanitized_name}")
                return jsonify({
                    "message": f"Workspace '{original_name}' created successfully!",
                    "id": workspace_id
                }), 200

            except Exception as e:
                logging.error(f"Error saving workspace: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to save workspace"}), 500





                        
        @self.flask_app.route('/save-llm-config', methods=['POST'])
        def save_llm_config():
            try:
                data = request.get_json()
                workspace_id = data.get("workspace_id")
                model_type = data.get("model_type")
                ollama_base_url = data.get("ollama_base_url")
                ollama_model = data.get("ollama_model")
                openai_model = data.get("openai_model")
                api_key = data.get("api_key")

                if not workspace_id:
                    return jsonify({"error": "Workspace ID is required"}), 400
                if not model_type:
                    return jsonify({"error": "Model type is required"}), 400

                # Verify workspace exists
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {workspace_id} not found"}), 404

                # Construct LLM config
                llm_config = {"model_type": model_type}
                if model_type == "ollama":
                    llm_config["ollama_base_url"] = ollama_base_url
                    llm_config["model_name"] = ollama_model
                elif model_type == "openai":
                    llm_config["model_name"] = openai_model
                    llm_config["api_key"] = api_key

                # Update workspace with LLM config
                metadata = existing["metadatas"][0]
                metadata["llm_config"] = json.dumps(llm_config)
                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[metadata],
                    documents=[f"Workspace: {metadata['name']}"]
                )

                logger.info(f"Saved LLM config for workspace: ID={workspace_id}", extra={"admin": True})
                return jsonify({"message": "LLM configuration saved successfully"}), 200
            except Exception as e:
                logger.error(f"Error saving LLM config: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to save LLM config"}), 500
            
        @self.flask_app.route('/save-ai-options', methods=['POST'])
        def save_ai_options():
            try:
                data = request.get_json()
                workspace_id = data.get("workspace_id")
                if not workspace_id:
                    return jsonify({"error": "Workspace ID is required"}), 400
 
                # Build ai_options from the payload (default values if missing)
                ai_options = {
                    "suggested_questions": bool(data.get("suggested_questions", True)),
                    "sql":                 bool(data.get("sql",                 True)),
                    "table":               bool(data.get("table",               True)),
                    "csv_download":        bool(data.get("csv_download",        True)),
                    "chart":               bool(data.get("chart",               True)),
                    "redraw_chart":        bool(data.get("redraw_chart",        True)),
                    "auto_fix_sql":        bool(data.get("auto_fix_sql",        True)),
                    "ask_results_correct": bool(data.get("ask_results_correct",True)),
                    "followup_questions":  bool(data.get("followup_questions",  True)),
                    "summarization":       bool(data.get("summarization",       True))
                }
 
                # Get existing workspace metadata
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({"error": f"Workspace {workspace_id} not found"}), 404
 
                meta = existing["metadatas"][0]
 
                # Normalize and ensure metadata values are primitives
                normalized_meta = self._normalize_and_store_ai_options(meta, ai_options)
 
                # Update collection - provide primitive-valued metadata and keep a simple document string
                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[normalized_meta],
                    documents=[f"Workspace: {normalized_meta.get('name', workspace_id)}"]
                )
 
                # Apply immediately to running app config and broadcast
                self._apply_ai_options_to_config(workspace_id, ai_options)
                self._broadcast_config_change(workspace_id, ai_options)
                self.ai_options.update(ai_options)
 
                return jsonify({"message": "AI options saved"}), 200
 
            except Exception as e:
                logger.error(f"save_ai_options error: {e}", exc_info=True)
                return jsonify({"error": "Failed to save"}), 500
 
 
        @self.flask_app.route('/get-ai-options/<workspace_id>', methods=['GET'])
        def get_ai_options(workspace_id):
            try:
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({"error": "Workspace not found"}), 404
 
                meta = existing["metadatas"][0]
 
                # Try to parse ai_options which might be stored as JSON string or absent
                ai_options = {}
                raw = meta.get("ai_options")
                if isinstance(raw, str) and raw:
                    try:
                        ai_options = json.loads(raw)
                    except Exception:
                        # If raw is string but not JSON, ignore and fallback to flattened keys
                        ai_options = {}
                elif isinstance(raw, dict):
                    # defensive: if older data accidentally stored a dict, accept it
                    ai_options = raw
 
                # If still empty, try flattened fields (ai_sql, ai_chart, etc.)
                if not ai_options:
                    # collect any ai_ prefixed keys
                    for k, v in meta.items():
                        if k.startswith("ai_"):
                            ai_options[k[3:]] = bool(v)
 
                # Apply immediately to the runtime config for the workspace
                self._apply_ai_options_to_config(workspace_id, ai_options)
 
                return jsonify({
                    "workspace_id": workspace_id,
                    "ai_options": ai_options,
                    "effective_config": self.config
                }), 200
 
            except Exception as e:
                logger.error(f"get_ai_options error: {e}", exc_info=True)
                return jsonify({"error": "Failed to load"}), 500
           
 
 
 
        @self.flask_app.route('/api/v0/get-active-workspace')
        @self.requires_auth
        def get_active_workspace(user):
            from flask import session, jsonify

            uid = session.get("user_id")
            wid = session.get("workspace_id")
            uname = session.get("username")
            ws_name = session.get("workspace")

            logger.info(
                "get_active_workspace | user=%s username=%s workspace_id=%s workspace_name=%s session=%s",
                uid,
                uname,
                wid,
                ws_name,
                dict(session),
                extra={"cache": True}
            )

            if not wid:
                logger.warning(
                    "get_active_workspace | NO workspace_id for user=%s session=%s",
                    uid,
                    dict(session),
                    extra={"cache": True}
                )
                return jsonify({"error": "No active workspace"}), 404

            return jsonify({"workspace_id": wid}), 200


       
 
 
 
        @self.flask_app.route('/api/update_workspace_settings', methods=['POST'])
        def update_workspace_settings():
            data = request.get_json()
            workspace_id = data.get("workspace_id")
            settings = data.get("settings", {})
 
            if not workspace_id:
                return jsonify({"error": "workspace_id required"}), 400
 
            # Initialize if not exists
            if workspace_id not in self.workspace_settings:
                self.workspace_settings[workspace_id] = {}
 
            # Update settings dynamically
            self.workspace_settings[workspace_id].update(settings)
 
            return jsonify({"success": True, "settings": self.workspace_settings[workspace_id]})
 
 
        @self.flask_app.route('/api/get_workspace_settings', methods=['GET'])
        def get_workspace_settings():
            workspace_id = request.args.get("workspace_id")
 
            if not workspace_id:
                return jsonify({"error": "workspace_id required"}), 400
 
            settings = self.workspace_settings.get(workspace_id, {
                "sql": True,
                "summarization": False,
                "function_generation": False
            })
            return jsonify({"success": True, "settings": settings})
 
        
        def _sync_linked_server(primary_cfg, secondary_cfg):
            """Keep the SQL Server linked server in sync with whatever is actually
            saved in db_config/db_config_b — if the user changes the secondary DB's
            server, port, credentials, or alias, the real linked server object on
            the primary instance is dropped and recreated to match, rather than
            going stale (the same failure mode trained SQL examples had before the
            db-scope validator existed). No-op — and cleans up any existing linked
            server with that alias — when both databases are on the same
            server+port, since a linked server isn't needed there at all.

            Never raises: failures here (e.g. insufficient permissions, provider
            not registered) are logged and returned as a warning, without blocking
            the DB config save itself."""
            if not secondary_cfg or not secondary_cfg.get("databaseName"):
                return True, "No secondary DB configured — nothing to sync."

            alias = secondary_cfg.get("db_alias") or "SECONDARY"
            same_instance = (
                str(primary_cfg.get("serverName") or "").strip().lower()
                    == str(secondary_cfg.get("serverName") or "").strip().lower()
                and str(primary_cfg.get("port") or "").strip()
                    == str(secondary_cfg.get("port") or "").strip()
            )

            conn = None
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={primary_cfg['serverName']},{primary_cfg['port']};"
                    f"DATABASE={primary_cfg['databaseName']};"
                    f"UID={primary_cfg['username']};"
                    f"PWD={primary_cfg['password']};"
                )
                conn = pyodbc.connect(conn_str, timeout=10, autocommit=True)
                cursor = conn.cursor()

                cursor.execute("SELECT 1 FROM sys.servers WHERE name = ?", (alias,))
                exists = cursor.fetchone() is not None

                if same_instance:
                    if exists:
                        cursor.execute("EXEC sp_dropserver ?, 'droplogins'", (alias,))
                        logger.info(f"Dropped now-unneeded linked server '{alias}' (databases are same-instance).", extra={"admin": True})
                    return True, "Same-instance topology — no linked server needed."

                if exists:
                    cursor.execute("EXEC sp_dropserver ?, 'droplogins'", (alias,))

                datasrc = f"{secondary_cfg['serverName']},{secondary_cfg['port']}"
                cursor.execute(
                    "EXEC sp_addlinkedserver @server=?, @srvproduct=N'', @provider=N'MSOLEDBSQL', @datasrc=?",
                    (alias, datasrc),
                )
                cursor.execute(
                    "EXEC sp_addlinkedsrvlogin @rmtsrvname=?, @useself=N'False', @locallogin=NULL, @rmtuser=?, @rmtpassword=?",
                    (alias, secondary_cfg["username"], secondary_cfg["password"]),
                )
                cursor.execute("EXEC sp_serveroption ?, N'rpc', N'true'", (alias,))
                cursor.execute("EXEC sp_serveroption ?, N'rpc out', N'true'", (alias,))

                logger.info(f"Linked server '{alias}' synced to point at {datasrc}/{secondary_cfg['databaseName']}.", extra={"admin": True})
                return True, f"Linked server '{alias}' created/updated successfully."

            except Exception as e:
                logger.error(f"Failed to sync linked server '{alias}': {e}", exc_info=True, extra={"admin": True})
                return False, f"DB config saved, but linked server sync failed: {e}"
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        @self.flask_app.route("/save_connection", methods=["POST"])
        def save_connection():
            try:
                data = request.get_json()
                workspace_id = data.get("workspace_id")
                # slot "a" = primary DB (existing behavior, default). slot "b" = optional
                # second DB for dual-DB workspaces, reached via a linked server from
                # the primary connection (see get_sql_prompt cross-DB qualification).
                slot = str(data.get("slot") or "a").strip().lower()
                server = data.get("serverName")
                port = data.get("port")
                database = data.get("databaseName")
                username = data.get("username")
                password = data.get("password")
                db_alias = data.get("dbAlias") or ("PRIMARY" if slot == "a" else "SECONDARY")

                if not workspace_id:
                    return jsonify({"error": "Workspace ID is required"}), 400
                if slot not in ("a", "b"):
                    return jsonify({"error": "slot must be 'a' or 'b'"}), 400
                if not all([server, port, database, username, password]):
                    return jsonify({"error": "All DB fields are required"}), 400

                # Verify workspace exists
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {workspace_id} not found"}), 404

                # Test connection
                success, message = test_db_connection(server, port, database, username, password)
                if not success:
                    return jsonify({"error": f"Connection failed: {message}"}), 400

                # Construct DB config
                db_config = {
                    "serverName": server,
                    "port": port,
                    "databaseName": database,
                    "username": username,
                    "password": password,
                    "db_alias": db_alias
                }

                # Update workspace with DB config (slot "a" -> db_config, slot "b" -> db_config_b)
                metadata = existing["metadatas"][0]
                config_key = "db_config" if slot == "a" else "db_config_b"
                metadata[config_key] = json.dumps(db_config)
                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[metadata],
                    documents=[f"Workspace: {metadata['name']}"]
                )

                logger.info(f"Saved DB config (slot={slot}, alias={db_alias}) for workspace: ID={workspace_id}", extra={"admin": True})

                # Keep the SQL Server linked server in sync with whatever was just
                # saved — either slot changing can affect it (a new primary means
                # any existing linked server lives on the wrong server; a new
                # secondary means the linked server needs to point somewhere else).
                # Re-read both configs fresh from the metadata we just wrote so this
                # always reflects the current saved state, not just this request's slot.
                sync_message = None
                try:
                    current_primary = json.loads(metadata.get("db_config", "{}"))
                    current_secondary = json.loads(metadata.get("db_config_b", "{}"))
                    if current_primary.get("databaseName"):
                        sync_ok, sync_message = _sync_linked_server(current_primary, current_secondary)
                        if not sync_ok:
                            logger.warning(f"Linked server sync issue for workspace {workspace_id}: {sync_message}", extra={"admin": True})
                except Exception as sync_exc:
                    logger.error(f"Unexpected error syncing linked server for workspace {workspace_id}: {sync_exc}", exc_info=True, extra={"admin": True})
                    sync_message = f"DB config saved, but linked server sync raised an unexpected error: {sync_exc}"

                response = {"message": "DB configuration saved successfully"}
                if sync_message:
                    response["linked_server_status"] = sync_message
                return jsonify(response), 200
            except Exception as e:
                logger.error(f"Error saving DB config: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Failed to save DB config"}), 500
            
        @self.flask_app.route('/save_training_data', methods=['POST'])
        def save_training_data():
            try:
                workspace_id = request.form.get("workspace_id")
                file_type = request.form.get("file_type")
                column_count = int(request.form.get("column_count", 0))
                files = request.files.getlist("files")

                if not workspace_id:
                    return jsonify({"error": "Workspace ID is required"}), 400
                if not files:
                    return jsonify({"error": "No files uploaded"}), 400
                if file_type not in ['csv', 'pdf']:
                    return jsonify({"error": "Invalid file type"}), 400

                # Verify workspace exists
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {workspace_id} not found"}), 404
                workspace_name = existing["metadatas"][0]["name"]

                training_id = str(uuid.uuid4())
                global vn
                if vn is None:
                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)
                            self.chroma_client: chromadb.Client
                            self.collection_metadata = config.get("collection_metadata", {})
                    vn = MyVanna(config={'allow_llm_to_see_data': 'True'})

                for file in files:
                    if file_type == 'pdf':
                        with pdfplumber.open(file) as pdf:
                            text = ''.join(page.extract_text() or '' for page in pdf.pages)
                        if not text.strip():
                            return jsonify({"error": "No text extracted from PDF"}), 400
                        vn.add_documentation(text, collection_name=workspace_name)
                        file.save(f"training_data/{training_id}_{file.filename}")
                        logger.info(f"Saved PDF file: {file.filename} for workspace {workspace_id}", extra={"admin": True})
                    else:  # csv
                        file.seek(0)
                        df = pd.read_csv(file)
                        if column_count == 1:
                            text = '\n'.join(df.iloc[:, 0].astype(str).dropna())
                            if not text.strip():
                                return jsonify({"error": "No valid content in single-column CSV"}), 400
                            vn.add_documentation(text, collection_name=workspace_name)
                            logger.info(f"Processed single-column CSV as documentation for workspace {workspace_id}", extra={"admin": True})
                        file.save(f"training_data/{training_id}_{file.filename}")
                        logger.info(f"Saved CSV file: {file.filename} for workspace {workspace_id}", extra={"admin": True})

                # Update workspace with training ID
                metadata = existing["metadatas"][0]
                metadata["training_id"] = training_id
                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[metadata],
                    documents=[f"Workspace: {metadata['name']}"]
                )

                logger.info(f"Saved training data for workspace: ID={workspace_id}, Training ID={training_id}", extra={"admin": True})
                return jsonify({"message": "Training data saved successfully"}), 200
            except Exception as e:
                logger.error(f"Error saving training data: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Failed to save training data"}), 500
        
            

        @self.flask_app.route("/train-model", methods=["POST"])
        def train_model():
            try:
                file = request.files.get("file")
                if not file:
                    return jsonify({"message": "No file uploaded"}), 400

                df = pd.read_csv(file)
                logger.info(f"Training started on: {df.head()}")  # Log the first few rows

                # Simulate training process (integrate with Vanna if needed)
                return jsonify({"message": "Training started successfully!"}), 200
            except Exception as e:
                logger.error(f"Error training model: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to train model"}), 500
            

           

        @self.flask_app.route("/api/v0/get_training_data_module", methods=["GET"])
        def get_training_data_module(user: any = None):
            try:
                workspace_name = request.args.get('workspace_name')
                if not workspace_name:
                    return jsonify({"type": "error", "error": "workspace_name is required"}), 400

                global vn
                if vn is None:
                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)
                            self.chroma_client: chromadb.Client
                            self.collection_metadata = config.get("collection_metadata", {}) 

                    vn = MyVanna(config={'allow_llm_to_see_data': 'True'})

                df = vn.get_training_data_module(collection_name=workspace_name)

                if df is None or df.empty:
                    return jsonify({
                        "type": "error",
                        "error": "No training data found. Please add some training data first.",
                    })

                return jsonify({
                    "type": "df",
                    "id": "training_data",
                    "df": df.to_dict(orient="records"),  # Always return as real list
                })

            except Exception as e:
                logger.error(f"Error in get_training_data_module: {e}")
                return jsonify({"type": "error", "error": str(e)}), 500


        @self.flask_app.route("/api/v0/edit_training_data", methods=["POST"])
        @self.requires_auth
        def edit_training_data(user: any = None):
            try:
                data = flask.request.json
                training_id = data.get("id")
                new_question = data.get("question")
                new_content = data.get("content")
                is_documentation = data.get("is_documentation", False)
                workspace_name = flask.request.args.get("workspace_name")

                print("Received Edit Request:")
                print(f"ID: {training_id}")
                print(f"New Question: {new_question}")
                print(f"New Content: {new_content}")
                print(f"Is Documentation: {is_documentation}")
                print(f"Workspace: {workspace_name}")

                if not training_id:
                    return jsonify({"type": "error", "error": "No training_id provided"}), 400
                if not workspace_name:
                    return jsonify({"type": "error", "error": "No workspace_name provided"}), 400

                # Pass workspace_name and appropriate fields to edit_training_data
                success, new_id = vn.edit_training_data(
                    id=training_id,
                    new_question=new_question if not is_documentation else None,
                    new_content=new_content,
                    workspace=workspace_name
                )

                if success:
                    return jsonify({"success": True, "new_id": new_id})
                else:
                    return jsonify({"type": "error", "error": "Could not update training data"}), 400

            except Exception as e:
                logger.error(f"Error in edit_training_data: {e}")
                return jsonify({"type": "error", "error": str(e)}), 500



        # @self.flask_app.route("/api/v0/train", methods=["POST"])
        # def add_training_data(user: any=None):
        #     logger.info(f"Received request from user: {user}")
        #     data = flask.request.json
        #     logger.info(f"Request data: {data}")
        #     workspace_id = data.get("workspace_id")
        #     if not workspace_id:
        #         return jsonify({"error": "Workspace ID is required"}), 400

        #     try:
        #         results = self.workspace_collection.get(ids=[workspace_id])
        #         logger.info(f"Workspace query results: {results}")
        #         if not results or not results.get("ids"):
        #             return jsonify({"error": "Workspace not found"}), 404
        #         metadatas = results.get("metadatas", [{}])
        #         workspace = metadatas[0].get("name", None)
        #         if not workspace:
        #             return jsonify({"error": "Workspace name not found"}), 404
        #     except Exception as e:
        #         logger.error(f"Error fetching workspace: {str(e)}", exc_info=True)
        #         return jsonify({"error": f"Error fetching workspace: {str(e)}"}), 500

        #     training_data = data.get("training_data")
        #     if not training_data or not isinstance(training_data, list):
        #         return jsonify({"error": "Training data is missing or invalid"}), 400

        #     try:
        #         global vn
        #         if vn is None:
        #             class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
        #                 def __init__(self, config=None):
        #                     ChromaDB_VectorStore.__init__(self, config=config)
        #                     OpenAI_Chat.__init__(self, config=config)
                    
        #             logger.info("vn is None, initializing MyVanna")
        #             vn = MyVanna(config={'allow_llm_to_see_data': 'True'})
                
        #         for entry in training_data:
        #             question = entry.get("question")
        #             sql = entry.get("sql")
        #             logger.info(f"Adding question-SQL pair to workspace '{workspace}': {question} -> {sql}")
        #             id = vn.add_question_sql(question=question, sql=sql, workspace=workspace)
        #             logger.info(f"Trained: {question} -> {sql}, ID: {id}")
        #         return jsonify({"message": "Training completed successfully!"})
        #     except Exception as e:
        #         logger.error(f"Training error: {str(e)}", exc_info=True)
        #         return jsonify({"error": str(e)}), 500













        @self.flask_app.route("/api/v0/train", methods=["POST"])
        def add_training_data(user: any = None):
            logger.info(f"Received request from user: {user}")
            data = flask.request.json
            logger.info(f"Request data: {data}")

            workspace_id = data.get("workspace_id")
            if not workspace_id:
                return jsonify({"error": "Workspace ID is required"}), 400

            try:
                results = self.workspace_collection.get(ids=[workspace_id])
                logger.info(f"Workspace query results: {results}")
                if not results or not results.get("ids"):
                    return jsonify({"error": "Workspace not found"}), 404
                metadatas = results.get("metadatas", [{}])
                workspace = metadatas[0].get("name", None)
                if not workspace:
                    return jsonify({"error": "Workspace name not found"}), 404
            except Exception as e:
                logger.error(f"Error fetching workspace: {str(e)}", exc_info=True)
                return jsonify({"error": f"Error fetching workspace: {str(e)}"}), 500

            # Support both single entry and list of entries
            training_data = data.get("training_data", None)
            if isinstance(training_data, list):
                entries = training_data
            else:
                # Try to get question and sql directly
                question = data.get("question")
                sql = data.get("sql")
                if question and sql:
                    entries = [{"question": question, "sql": sql}]
                else:
                    return jsonify({"error": "Training data is missing or invalid"}), 400

            # Validate all entries
            valid_entries = []
            for idx, entry in enumerate(entries):
                question = entry.get("question")
                sql = entry.get("sql")
                if not question or not sql:
                    logger.warning(f"Skipping invalid entry at index {idx}: {entry}")
                    continue
                valid_entries.append(entry)

            if not valid_entries:
                return jsonify({"error": "No valid training data provided"}), 400

            try:
                global vn
                if vn is None:
                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)
                    logger.info("vn is None, initializing MyVanna")
                    vn = MyVanna(config={'allow_llm_to_see_data': 'True'})

                trained_ids = []
                for entry in valid_entries:
                    question = entry.get("question")
                    sql = entry.get("sql")
                    logger.info(f"Adding question-SQL pair to workspace '{workspace}': {question} -> {sql}")
                    id = vn.add_question_sql(question=question, sql=sql, workspace=workspace)
                    trained_ids.append(id)
                    logger.info(f"Trained: {question} -> {sql}, ID: {id}")

                return jsonify({
                    "message": "Training completed successfully!",
                    "trained_ids": trained_ids,
                    "total_entries": len(trained_ids)
                })

            except Exception as e:
                logger.error(f"Training error: {str(e)}", exc_info=True)
                return jsonify({"error": str(e)}), 500
            






        @self.flask_app.route("/api/v0/train_documentation", methods=["POST"])
        def add_documentation_training(user: any=None):
            logger.info(f"Received request from user: {user}")
            data = flask.request.json
            logger.info(f"Request data: {data}")
            workspace_id = data.get("workspace_id")
            workspace_name = data.get("workspace_name")
            documentation = data.get("documentation")

            if not workspace_id or not workspace_name:
                return jsonify({"error": "Workspace ID and name are required"}), 400

            if not documentation or not isinstance(documentation, list):
                return jsonify({"error": "Documentation data is missing or invalid"}), 400

            try:
                global vn
                if vn is None:
                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)
                    
                    logger.info("vn is None, initializing MyVanna")
                    vn = MyVanna(config={'allow_llm_to_see_data': 'True'})
                
                for doc in documentation:
                    if doc:
                        id = vn.add_documentation(documentation=doc, workspace=workspace_name)
                        logger.info(f"Trained documentation: {doc}, ID: {id}")
                return jsonify({"message": "Documentation training completed successfully!"})
            except Exception as e:
                logger.error(f"Training error: {str(e)}", exc_info=True)
                return jsonify({"error": str(e)}), 500
        

        # Helper function to initialize Vanna
        def initialize_vanna_instance(workspace_id, llm_details, db_details, db_details_b=None):
            global vn
            try:
                # Initialize Vanna based on LLM type
                if llm_details['model_type'] == 'openai':
                    if not llm_details['api_key']:
                        logger.warning("API key missing for OpenAI model", extra={"admin": True})
                        logger.warning("API key missing for OpenAI model", extra={"user": True})
                        return {"success": False, "error": "API key is required for OpenAI models"}

                    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            OpenAI_Chat.__init__(self, config=config)

                    vn = MyVanna(config={
                        'api_key': llm_details['api_key'],
                        'model': llm_details['model_name'],
                        'allow_llm_to_see_data': True
                    })
                elif llm_details['model_type'] == 'ollama':
                    class MyVanna(ChromaDB_VectorStore, Ollama):
                        def __init__(self, config=None):
                            ChromaDB_VectorStore.__init__(self, config=config)
                            Ollama.__init__(self, config=config)

                    vn = MyVanna(config={
                        'model': llm_details['model_name'],
                        'allow_llm_to_see_data': True
                    })
                else:
                    return {"success": False, "error": "Unsupported LLM model type."}

                # Use the same ODBC connection string as /connect-vanna
                odbc_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={db_details['serverName']},{db_details['port']};"
                    f"DATABASE={db_details['databaseName']};"
                    f"UID={db_details['username']};"
                    f"PWD={db_details['password']};"
                )
                logger.info(f"Connecting to MSSQL with: {odbc_conn_str.replace(db_details['password'], '****')}", extra={"admin": True})
                vn.connect_to_mssql(odbc_conn_str=odbc_conn_str)

                # Record primary/secondary DB aliases for cross-DB SQL qualification
                # (see get_sql_prompt). No live connection to the secondary DB — it's
                # reached either via same-instance three-part naming (if both databases
                # share the same server+port) or a linked server (if genuinely separate
                # servers) — get_sql_prompt picks the right form using vn.same_instance.
                vn.primary_db_alias = db_details.get("db_alias") or "PRIMARY"
                vn.primary_db_name = db_details.get("databaseName")
                if db_details_b and db_details_b.get("databaseName"):
                    vn.secondary_db_alias = db_details_b.get("db_alias") or "SECONDARY"
                    vn.secondary_db_name = db_details_b.get("databaseName")
                    vn.same_instance = (
                        str(db_details_b.get("serverName") or "").strip().lower()
                            == str(db_details.get("serverName") or "").strip().lower()
                        and str(db_details_b.get("port") or "").strip()
                            == str(db_details.get("port") or "").strip()
                    )
                else:
                    vn.secondary_db_alias = None
                    vn.secondary_db_name = None
                    vn.same_instance = False

                # Optionally store vn in vanna_api if needed
                # vanna_api.vn = vn  # Uncomment if vanna_api is a valid object
                logger.info(f"Vanna initialized for workspace {workspace_id}", extra={"admin": True})
                return {"success": True, "message": "Vanna initialized successfully."}
            except Exception as e:
                logger.error(f"Failed to initialize Vanna: {str(e)}", exc_info=True, extra={"admin": True})
                return {"success": False, "error": f"Failed to initialize Vanna: {str(e)}"}

        # Endpoint to initialize Vanna without redirect (used in Predictions section)
        @self.flask_app.route('/initialize-vanna', methods=['POST'])
        def initialize_vanna():
            global vn
            data = request.get_json()
            logger.info(f"initialize vanna data {data}")
            workspace_id = data.get('workspace_id')
            llm_details = data.get('llm_details', {})
            db_details = data.get('db_details', {})
            db_details_b = data.get('db_details_b') or {}
            session["workspace_id"] = workspace_id

            logger.info(
                        f"[SESSION] Active workspace set user= ws={workspace_id}",
                        extra={"session": True}
                    )
            if not workspace_id or not llm_details or not db_details:
                return jsonify({"type": "error", "error": "Missing required parameters."}), 400


            # Initialize Vanna
            result = initialize_vanna_instance(workspace_id, llm_details, db_details, db_details_b)
            if not result["success"]:
                return jsonify({"type": "error", "error": result["error"]}), 500

            return jsonify(result)


        # Endpoint to fetch columns for a given table
        @self.flask_app.route('/api/v0/get_columns', methods=['GET'])
        def get_columns():
            global vn
            workspace_id = request.args.get('workspace_id')
            table_name = request.args.get('table_name')

            if not workspace_id or not table_name:
                return jsonify({"type": "error", "error": "Workspace ID and table name are required."}), 400

            if workspace_id not in workspaces:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            if not vn or not hasattr(vn, 'run_sql_is_set') or not vn.run_sql_is_set:
                return jsonify({"type": "error", "error": "Vanna is not initialized. Please connect to Vanna first."}), 400

            try:
                # Fetch columns for the specified table
                columns = vn.get_columns(table_name)
                if not columns:
                    return jsonify({"type": "error", "error": f"No columns found for table {table_name}."}), 404
                return jsonify({"type": "success", "columns": columns})
            except Exception as e:
                return jsonify({"type": "error", "error": f"Failed to fetch columns: {str(e)}"}), 500

        # Helper function to get workspace metadata
        '''def get_workspace_metadata(self, workspace_id):
            try:
                results = self.workspace_collection.get(ids=[str(workspace_id)])
                if not results.get("metadatas"):
                    return None
                return results["metadatas"][0]
            except Exception as e:
                logger.error(f"Error fetching workspace metadata: {str(e)}", exc_info=True)
                return None'''

        # Helper function to initialize Vanna if not already done
        '''def ensure_vanna_initialized(self, workspace_id):
            global vn
            logger.info("ensure vanna function")
            
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return False, "Workspace not found"
            logger.info(f"Workspace inside ensure {workspace}")
            llm_config = json.loads(workspace.get("llm_config", "{}"))
            db_config = json.loads(workspace.get("db_config", "{}"))
            logger.info(f"ensure vanna function {llm_config} {db_config}")
            
            data_to_send = {
                "workspace_id": workspace_id,
                "llm_details": {
                    "model_name": llm_config.get("model_name"),
                    "model_type": llm_config.get("model_type"),
                    "api_key": llm_config.get("api_key"),
                    "base_url": llm_config.get("base_url")
                },
                "db_details": {
                    "serverName": db_config.get("serverName"),
                    "port": db_config.get("port"),
                    "databaseName": db_config.get("databaseName"),
                    "username": db_config.get("username"),
                    "password": db_config.get("password")
                }
            }
            result = initialize_vanna_instance(workspace_id, data_to_send["llm_details"], data_to_send["db_details"])
            if not result["success"]:
                return False, result["error"]
            return True, None'''

        # Updated /api/v0/test_sql_query (already exists, enhanced for predictions)
        @self.flask_app.route('/api/v0/test_sql_query', methods=['POST'])
        def test_sql_query():
            global vn
            workspace_id = request.args.get('workspace_id')
            data = request.get_json()
            sql_query = data.get('sql_query')
            logger.info(f"Test SQL  workspace_id {workspace_id}", extra={"admin": True})
            if not workspace_id or not sql_query:
                return jsonify({"type": "error", "error": "Workspace ID and SQL query are required."}), 400

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            try:
                df = vn.run_sql(sql_query)
                row_count = len(df) if df is not None else 0
                return jsonify({
                    "type": "success",
                    "row_count": row_count,
                    "df": df.to_dict(orient='records')  # Include full DataFrame for preview
                })
            except Exception as e:
                logger.error(f"SQL query failed: {str(e)}", exc_info=True)
                return jsonify({"type": "sql_error", "error": f"SQL query failed: {str(e)}"}), 500




#---------------------------------------------

        @self.flask_app.route('/api/v0/get_tables', methods=['GET'])
        def get_tables(self):
            global vn  # Use the global Vanna instance
            workspace_id = request.args.get('workspace_id')
            if not workspace_id:
                return jsonify({"type": "error", "error": "Workspace ID is required"}), 400
            
            # Ensure Vanna is initialized for this workspace
            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                logger.error(f"Vanna initialization failed: {error}")
                return jsonify({"type": "error", "error": error}), 400

            try:
                # Fetch tables using a SQL query via vn.run_sql()
                sql_query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                """
                df = vn.run_sql(sql_query)
                
                # Extract table names from the DataFrame
                if df is None or df.empty:
                    logger.info(f"No tables found for workspace {workspace_id}")
                    return jsonify({"type": "success", "tables": []})
                
                tables = df['TABLE_NAME'].tolist()
                logger.info(f"Retrieved tables for workspace {workspace_id}: {tables}")
                return jsonify({"type": "success", "tables": tables})
            except Exception as e:
                logger.error(f"Error fetching tables for workspace {workspace_id}: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to fetch tables: {str(e)}"}), 500
#=================================================================================================================
        def get_workspace_metadata(self, workspace_id):
            try:
                results = self.workspace_collection.get(ids=[str(workspace_id)])
                if not results.get("metadatas"):
                    return None
                return results["metadatas"][0]
            except Exception as e:
                logger.error(f"Error fetching workspace metadata: {str(e)}", exc_info=True)
                return None

        def ensure_vanna_initialized(self, workspace_id):
            global vn
            logger.info("ensure vanna function")
            
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return False, "Workspace not found"
            logger.info(f"Workspace inside ensure {workspace}")
            llm_config = json.loads(workspace.get("llm_config", "{}"))
            db_config = json.loads(workspace.get("db_config", "{}"))
            db_config_b = json.loads(workspace.get("db_config_b", "{}"))
            logger.info(f"ensure vanna function {llm_config} {db_config}")

            data_to_send = {
                "workspace_id": workspace_id,
                "llm_details": {
                    "model_name": llm_config.get("model_name"),
                    "model_type": llm_config.get("model_type"),
                    "api_key": llm_config.get("api_key"),
                    "base_url": llm_config.get("base_url")
                },
                "db_details": {
                    "serverName": db_config.get("serverName"),
                    "port": db_config.get("port"),
                    "databaseName": db_config.get("databaseName"),
                    "username": db_config.get("username"),
                    "password": db_config.get("password"),
                    "db_alias": db_config.get("db_alias")
                },
                "db_details_b": {
                    "databaseName": db_config_b.get("databaseName"),
                    "db_alias": db_config_b.get("db_alias"),
                    "serverName": db_config_b.get("serverName"),
                    "port": db_config_b.get("port")
                } if db_config_b.get("databaseName") else None
            }
            result = initialize_vanna_instance(
                workspace_id, data_to_send["llm_details"], data_to_send["db_details"],
                data_to_send["db_details_b"]
            )
            if not result["success"]:
                return False, result["error"]

            # CRITICAL: Sync the global vn instance back to the class property self.vn
            # This ensures that endpoints using self.vn can access the initialized model
            self.vn = vn

            return True, None

        # ==================================================================
        # Chat-driven writes: generate (preview only) -> confirm -> execute.
        # Mirrors the existing generate_sql/run_sql two-step shape, but the SQL is
        # cached server-side by write_id rather than trusted from the client, since
        # writes are higher stakes than the read flow's client-echoed-SQL pattern.
        # ==================================================================

        def _parse_write_statement(sql):
            """Best-effort (operation, table_ref, where_or_columns) extraction for
            building the affected-row preview. table_ref keeps any schema/bracket
            qualification exactly as written, unlike is_write_sql_valid's bare
            table-name extraction used for whitelist checks."""
            m = re.search(r"UPDATE\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)
            if m:
                where_m = re.search(r"\bWHERE\b(.*)$", sql, re.IGNORECASE | re.DOTALL)
                return "UPDATE", m.group(1), (where_m.group(1).strip() if where_m else None)

            m = re.search(r"DELETE\s+FROM\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)
            if m:
                where_m = re.search(r"\bWHERE\b(.*)$", sql, re.IGNORECASE | re.DOTALL)
                return "DELETE", m.group(1), (where_m.group(1).strip() if where_m else None)

            m = re.search(r"INSERT\s+INTO\s+([a-zA-Z0-9_.\[\]]+)", sql, re.IGNORECASE)
            if m:
                return "INSERT", m.group(1), None

            return None, None, None

        def _stage_pending_write(vn_instance, workspace_name, workspace_id, question_en, original_question=None):
            """Generate a write statement, validate it, compute an affected-row
            preview, and stage it in _pending_writes for confirmation. Shared by the
            auto-routed write branch in generate_sql and generate_write_sql_route.

            workspace_name is the ChromaDB collection identifier (same "workspace"
            param the read path already uses for retrieval); workspace_id is the
            actual workspace UUID needed later by execute_write_sql_route for
            ensure_vanna_initialized/get_workspace_metadata/get_db_connection_from_config.
            These are two different identifiers for the same workspace — the pending-
            write cache is keyed by workspace_id since that's what execute time has.

            Returns (response_dict, http_status)."""
            display_question = original_question if original_question is not None else question_en
            try:
                sql, total, inp, out, model = vn_instance.generate_write_sql(question=question_en, workspace=workspace_name)
            except Exception as e:
                logger.error(f"generate_write_sql failed: {e}", exc_info=True, extra={"admin": True})
                return {"type": "error", "error": str(e)}, 500

            whitelist = vn_instance.get_write_whitelist(workspace=workspace_name)
            is_valid, reason = vn_instance.is_write_sql_valid(sql, whitelist)
            if not is_valid:
                return {"type": "text", "text": sql, "original_question": display_question}, 200

            operation, table_ref, predicate = _parse_write_statement(sql)
            preview = {"operation": operation, "table": table_ref}
            if operation == "INSERT":
                preview["affected_rows_estimate"] = 1
            elif predicate:
                try:
                    count_df = vn_instance.run_sql(f"SELECT COUNT(*) AS cnt FROM {table_ref} WHERE {predicate}")
                    preview["affected_rows_estimate"] = int(count_df.iloc[0]["cnt"]) if count_df is not None and not count_df.empty else None
                except Exception as e:
                    logger.warning(f"Affected-row preview count failed: {e}", extra={"admin": True})
                    preview["affected_rows_estimate"] = None

            write_id = str(uuid.uuid4())
            with _pending_writes_lock:
                _pending_writes[write_id] = {
                    "sql": sql,
                    "workspace_id": workspace_id,
                    "question": display_question,
                    "created_at": time.time(),
                }

            return {
                "type": "write_confirmation",
                "write_id": write_id,
                "text": sql,
                "preview": preview,
                "original_question": display_question,
            }, 200

        def _insert_write_audit_log(workspace_id, user_id, question, generated_sql,
                                     target_table, operation, rows_affected, status, error_message=None):
            """Persist a record of every write attempt (executed or failed) to the
            existing app-level feedback database — a durable audit trail, unlike the
            unpick agent's in-memory-only log buffer. Requires a write_audit_log
            table (see plan doc) to already exist in that database."""
            try:
                conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO write_audit_log
                        (workspace_id, user_id, question, generated_sql, target_table,
                         operation, rows_affected, status, error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                    """,
                    workspace_id, user_id, question, generated_sql, target_table,
                    operation, rows_affected, status, error_message,
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to write audit log entry: {e}", exc_info=True, extra={"admin": True})

        @self.flask_app.route('/api/v0/generate_write_sql', methods=['POST'])
        @self.requires_auth
        def generate_write_sql_route(user=None):
            """Generate a write statement for confirmation only — never executes it."""
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            question = data.get('question')

            if not workspace_id or not question:
                return jsonify({"type": "error", "error": "workspace_id and question are required"}), 400

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            body, status = _stage_pending_write(vn, workspace_id, question)
            return jsonify(body), status

        @self.flask_app.route('/api/v0/execute_write_sql', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def execute_write_sql_route(user=None):
            """Execute a previously-generated write after explicit user confirmation.
            The SQL is looked up server-side by write_id — never accepted as a raw
            string from the client — and re-validated against the whitelist here,
            independent of whatever generate_write_sql_route already checked."""
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            write_id = data.get('write_id')

            if not workspace_id or not write_id:
                return jsonify({"type": "error", "error": "workspace_id and write_id are required"}), 400

            with _pending_writes_lock:
                pending = _pending_writes.pop(write_id, None)

            if not pending or pending.get("workspace_id") != workspace_id:
                return jsonify({"type": "error", "error": "Unknown or expired write_id"}), 404

            # A pending write is single-use and short-lived (10 minutes) — re-generate
            # if it has gone stale, so a confirmation click can't replay a write against
            # data that may have changed, or execute long after the user actually saw it.
            if time.time() - pending.get("created_at", 0) > 600:
                return jsonify({"type": "error", "error": "This write has expired — please ask again"}), 410

            sql = pending["sql"]
            question = pending["question"]

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            whitelist = vn.get_write_whitelist(workspace=workspace_id)
            valid, reason = vn.is_write_sql_valid(sql, whitelist)
            operation, table_ref, _ = _parse_write_statement(sql)
            user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)

            if not valid:
                _insert_write_audit_log(workspace_id, user_id, question, sql, table_ref, operation,
                                         None, "rejected", reason)
                return jsonify({"type": "error", "error": reason}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            db_config = json.loads(workspace.get("db_config", "{}")) if workspace else {}
            if not db_config:
                return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

            conn = None
            try:
                conn = self.get_db_connection_from_config(db_config)
                conn.autocommit = False
                cursor = conn.cursor()
                cursor.execute(sql)
                rows_affected = cursor.rowcount
                conn.commit()
                cursor.close()

                logger.info(
                    f"execute_write_sql committed. workspace={workspace_id} user={user_id} "
                    f"table={table_ref} op={operation} rows={rows_affected}",
                    extra={"admin": True},
                )
                _insert_write_audit_log(workspace_id, user_id, question, sql, table_ref, operation,
                                         rows_affected, "executed")

                return jsonify({
                    "type": "success",
                    "message": "Write executed successfully",
                    "rows_affected": rows_affected,
                })

            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                logger.error(f"execute_write_sql failed: {e}", exc_info=True, extra={"admin": True})
                _insert_write_audit_log(workspace_id, user_id, question, sql, table_ref, operation,
                                         None, "failed", str(e))
                return jsonify({"type": "error", "error": str(e)}), 200

            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        # Fixed Prediction Endpoints
        @self.flask_app.route('/api/v0/get_prediction_configs', methods=['GET'])
        def get_prediction_configs():
            workspace_id = request.args.get('workspace_id')
            logger.info(f"get prediction config workspaceid {workspace_id}")
            if not workspace_id:
                logger.warning("No workspace_id provided in get_prediction_configs request")
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400
            
            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400
            
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                logger.error(f"Workspace not found for ID: {workspace_id}")
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                # Safely get predictions, defaulting to empty list if missing or invalid
                predictions_raw = workspace.get("predictions", "[]")
                predictions = json.loads(predictions_raw)
                if not isinstance(predictions, list):
                    logger.warning(f"Invalid predictions format for workspace {workspace_id}: {predictions_raw}")
                    predictions = []  # Reset to empty list if not a list
                logger.info(f"Retrieved predictions for workspace {workspace_id}: {predictions}")
                return jsonify({"type": "success", "predictions": predictions})
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse predictions for workspace {workspace_id}: {str(e)}")
                return jsonify({"type": "success", "predictions": []})  # Return empty list on parse error
            except Exception as e:
                logger.error(f"Unexpected error in get_prediction_configs for workspace {workspace_id}: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to retrieve predictions: {str(e)}"}), 500

        @self.flask_app.route('/save_prediction_config', methods=['POST'])
        def save_prediction_config():
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            new_predictions = data.get('predictions', [])

            if not workspace_id:
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                # Load existing predictions
                existing_predictions = json.loads(workspace.get("predictions", "[]"))
                # Update or append new predictions
                for new_pred in new_predictions:
                    pred_type = new_pred.get("type")
                    existing_idx = next((i for i, p in enumerate(existing_predictions) if p["type"] == pred_type), -1)
                    if existing_idx >= 0:
                        existing_predictions[existing_idx] = new_pred
                    else:
                        existing_predictions.append(new_pred)
                
                # Update workspace metadata with predictions
                workspace["predictions"] = json.dumps(existing_predictions)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Saved prediction config for workspace: ID={workspace_id}")
                return jsonify({"type": "success", "message": "Predictions saved successfully."})
            except Exception as e:
                logger.error(f"Failed to save predictions: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to save predictions: {str(e)}"}), 500




        @self.flask_app.route('/save_anomaly_config', methods=['POST'])
        def save_anomaly_config():
            """
            Save or update anomaly detection configurations for a specified workspace.

            Expects a JSON payload with:
            - workspace_id: The ID of the workspace.
            - anomalies: A list of anomaly configurations, each containing:
            - enabled: Boolean indicating if the anomaly detection is enabled.
            - type: Unique identifier for the anomaly (lowercase, underscored).
            - sql_query: SQL query for fetching data.
            - algorithm: The anomaly detection algorithm (e.g., z_score, isolation_forest).
            - parameters: Algorithm-specific parameters.

            Returns:
                JSON response with either:
                - {"type": "success", "message": "Anomalies saved successfully."} on success.
                - {"type": "error", "error": "Error message"} on failure.
            """
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            new_anomalies = data.get('anomalies', [])

            if not workspace_id:
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                # Load existing anomaly configurations
                existing_anomalies = json.loads(workspace.get("anomalies", "[]"))
                # Update or append new anomaly configurations
                for new_anomaly in new_anomalies:
                    anomaly_type = new_anomaly.get("type")
                    if not anomaly_type:
                        return jsonify({"type": "error", "error": "Anomaly type is required."}), 400
                    existing_idx = next((i for i, a in enumerate(existing_anomalies) if a["type"] == anomaly_type), -1)
                    if existing_idx >= 0:
                        existing_anomalies[existing_idx] = new_anomaly
                    else:
                        existing_anomalies.append(new_anomaly)
                
                # Update workspace metadata with anomalies
                workspace["anomalies"] = json.dumps(existing_anomalies)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Saved anomaly config for workspace: ID={workspace_id}")
                return jsonify({"type": "success", "message": "Anomalies saved successfully."})
            except Exception as e:
                logger.error(f"Failed to save anomalies: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to save anomalies: {str(e)}"}), 500
            
        #delete prediction
        @self.flask_app.route('/delete_prediction_config', methods=['POST'])
        def delete_prediction_config():
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            prediction_type = data.get('prediction_type')
        
            if not workspace_id or not prediction_type:
                return jsonify({"type": "error", "error": "Workspace ID and prediction type are required."}), 400
        
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404
        
            try:
                existing_predictions = json.loads(workspace.get("predictions", "[]"))
                updated_predictions = [p for p in existing_predictions if p.get("type") != prediction_type]
        
                workspace["predictions"] = json.dumps(updated_predictions)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Deleted prediction '{prediction_type}' for workspace ID={workspace_id}")
                return jsonify({"type": "success", "message": "Prediction deleted successfully."})
            except Exception as e:
                logger.error(f"Failed to delete prediction: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to delete prediction: {str(e)}"}), 500

        @self.flask_app.route('/delete_anomaly_config', methods=['POST'])
        def delete_anomaly_config():
            """
            Delete an anomaly detection configuration for a specified workspace.

            Expects a JSON payload with:
            - workspace_id: The ID of the workspace.
            - anomaly_type: The unique identifier of the anomaly to delete.

            Returns:
                JSON response with:
                - {"type": "success", "message": "Anomaly deleted successfully."} on success.
                - {"type": "error", "error": "Error message"} on failure.
            """
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            anomaly_type = data.get('anomaly_type')

            if not workspace_id or not anomaly_type:
                return jsonify({"type": "error", "error": "Workspace ID and anomaly type are required."}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                # Load existing anomalies
                existing_anomalies = json.loads(workspace.get("anomalies", "[]"))
                # Filter out the anomaly with the specified type
                updated_anomalies = [a for a in existing_anomalies if a.get("type") != anomaly_type]

                # Update workspace metadata with filtered anomalies
                workspace["anomalies"] = json.dumps(updated_anomalies)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Deleted anomaly '{anomaly_type}' for workspace ID={workspace_id}")
                return jsonify({"type": "success", "message": "Anomaly deleted successfully."})
            except Exception as e:
                logger.error(f"Failed to delete anomaly: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to delete anomaly: {str(e)}"}), 500

        from flask import jsonify, request
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LinearRegression, LogisticRegression
        # import logging
        import json


        @self.flask_app.route('/api/v0/get_anomaly_configs', methods=['GET'])
        def get_anomaly_configs():
            """
            Retrieve anomaly detection configurations for a specified workspace.

            Query Parameters:
                workspace_id: The ID of the workspace.

            Returns:
                JSON response with:
                - {"type": "success", "anomalies": [...]} on success.
                - {"type": "error", "error": "Error message"} on failure.
            """
            workspace_id = request.args.get('workspace_id')
            logger.info(f"Fetching anomaly configs for workspace ID: {workspace_id}")
            if not workspace_id:
                logger.warning("No workspace_id provided in get_anomaly_configs request")
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400
            
            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400
            
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                logger.error(f"Workspace not found for ID: {workspace_id}")
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                # Safely get anomalies, defaulting to empty list if missing or invalid
                anomalies_raw = workspace.get("anomalies", "[]")
                anomalies = json.loads(anomalies_raw)
                if not isinstance(anomalies, list):
                    logger.warning(f"Invalid anomalies format for workspace {workspace_id}: {anomalies_raw}")
                    anomalies = []  # Reset to empty list if not a list
                logger.info(f"Retrieved anomalies for workspace {workspace_id}: {anomalies}")
                return jsonify({"type": "success", "anomalies": anomalies})
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse anomalies for workspace {workspace_id}: {str(e)}")
                return jsonify({"type": "error", "error": "Failed to parse anomalies: Invalid JSON format."}), 500
            except Exception as e:
                logger.error(f"Unexpected error in get_anomaly_configs for workspace {workspace_id}: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to retrieve anomalies: {str(e)}"}), 500


        @self.flask_app.route('/api/v0/run_anomaly', methods=['GET'])
        def run_anomaly():
            """
            Run anomaly detection for a specified anomaly type in a workspace.

            Query Parameters:
                workspace_id: The ID of the workspace.
                anomaly_type: The type of anomaly configuration to run.

            Returns:
                JSON response with:
                - {"type": "success", "results": [...]} containing all rows with is_anomaly flag.
                - {"type": "error", "error": "Error message"} on failure.
            """
            workspace_id = request.args.get('workspace_id')
            anomaly_type = request.args.get('anomaly_type')

            # Validate input parameters
            if not workspace_id or not anomaly_type:
                logger.warning(f"Missing parameters: workspace_id={workspace_id}, anomaly_type={anomaly_type}")
                return jsonify({"type": "error", "error": "Workspace ID and anomaly type are required."}), 400 

            # Ensure Vanna is initialized
            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                logger.error(f"Vanna initialization failed: {error}")
                return jsonify({"type": "error", "error": error}), 400

            # Fetch workspace metadata
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                logger.error(f"Workspace not found: ID={workspace_id}")
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            # Get anomaly configuration
            try:
                anomalies = json.loads(workspace.get("anomalies", "[]"))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse anomalies for workspace {workspace_id}: {str(e)}")
                return jsonify({"type": "error", "error": "Invalid anomaly configurations format."}), 500

            anomaly = next((a for a in anomalies if a['type'] == anomaly_type), None)

                                          
            if not anomaly:
                logger.error(f"Anomaly type {anomaly_type} not found in workspace {workspace_id}")
                return jsonify({"type": "error", "error": f"Anomaly type {anomaly_type} not found."}), 404

            if not anomaly.get('enabled', True):
                logger.warning(f"Anomaly type {anomaly_type} is disabled in workspace {workspace_id}")
                return jsonify({"type": "error", "error": f"Anomaly type {anomaly_type} is disabled."}), 400

            logger.info(f"Anomaly configuration for {anomaly_type}: {anomaly}")

            try:
                # Step 1: Fetch data using the SQL query
                df = vn.run_sql(anomaly['sql_query'])
                logger.info(f"Raw data from SQL query for {anomaly_type}:\n{df}")
                if df.empty:
                    logger.warning(f"SQL query returned no results for {anomaly_type}")
                    return jsonify({"type": "success", "results": []}), 200

                # Step 2: Preprocess data
                algorithm = anomaly.get('algorithm')
                parameters = anomaly.get('parameters', {})
                target = parameters.get('target')
                features = parameters.get('features', [])
                
                # Replace NaN with None for JSON compatibility
                df = df.replace({np.nan: None})
                # Convert datetime columns to strings
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].astype(str)

                # Initialize result_df to store all data
                result_df = df.copy()

                # Step 3: Apply anomaly detection logic based on algorithm
                if algorithm == 'z_score':
                    if not target:
                        logger.error(f"No target specified for z_score in {anomaly_type}")
                        return jsonify({"type": "error", "error": f"No target column specified for z_score anomaly {anomaly_type}."}), 400
                    if target not in df.columns:
                        logger.error(f"Target column {target} not found in data for {anomaly_type}")
                        return jsonify({"type": "error", "error": f"Target column {target} not found in query results for {anomaly_type}."}), 400
                    threshold = float(parameters.get('threshold', 2.0))
                    mean = df[target].mean()
                    std = df[target].std()
                    if std == 0:
                        logger.error(f"Standard deviation is zero for {target} in {anomaly_type}")
                        return jsonify({"type": "error", "error": f"Standard deviation is zero for {target}, cannot compute z-score."}), 400
                    result_df['z_score'] = (df[target] - mean) / std
                    result_df['is_anomaly'] = result_df['z_score'].abs() > threshold
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['z_score', 'is_anomaly']]

                elif algorithm == 'isolation_forest':
                    if not features or not all(f in df.columns for f in features):
                        logger.error(f"Invalid or missing features {features} for {anomaly_type}")
                        return jsonify({"type": "error", "error": f"Invalid or missing features {features} for isolation_forest anomaly {anomaly_type}."}), 400
                    contamination = float(parameters.get('contamination', 0.1))
                    model = IsolationForest(contamination=contamination, random_state=42)
                    X = df[features].values
                    result_df['is_anomaly'] = model.fit_predict(X) == -1
                    result_df['anomaly_score'] = model.score_samples(X)
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['anomaly_score', 'is_anomaly']]

                elif algorithm == 'dbscan':
                    if not features or not all(f in df.columns for f in features):
                        logger.error(f"Invalid or missing features {features} for {anomaly_type}")
                        return jsonify({"type": "error", "error": f"Invalid or missing features {features} for dbscan anomaly {anomaly_type}."}), 400
                    eps = float(parameters.get('eps', 0.5))
                    min_samples = int(parameters.get('min_samples', 5))
                    model = DBSCAN(eps=eps, min_samples=min_samples)
                    X = df[features].values
                    labels = model.fit_predict(X)
                    result_df['is_anomaly'] = labels == -1
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['is_anomaly']]

                elif algorithm == 'custom':
                    rule = parameters.get('rule')
                    if not rule:
                        logger.error(f"No rule provided for custom anomaly {anomaly_type}")
                        return jsonify({"type": "error", "error": f"No rule specified for custom anomaly {anomaly_type}."}), 400
                    try:
                        if rule.startswith('SELECT'):
                            result_df = vn.run_sql(rule)
                            result_df['is_anomaly'] = True
                            # Need to merge with original df to include normal data
                            original_df = df.copy()
                            original_df['is_anomaly'] = False
                            result_df = pd.concat([original_df, result_df]).drop_duplicates().reset_index(drop=True)
                        else:
                            result_df['is_anomaly'] = df.eval(rule)
                        # Do not filter, keep all rows
                        result_df = result_df[df.columns.tolist() + ['is_anomaly']]
                    except Exception as e:
                        logger.error(f"Failed to apply custom rule '{rule}' for {anomaly_type}: {str(e)}")
                        return jsonify({"type": "error", "error": f"Failed to apply custom rule for {anomaly_type}: {str(e)}"}), 400

                # Convert DataFrame to list of dicts for JSON response
                result = result_df.to_dict(orient='records')
                logger.info(f"Returning {len(result)} rows (including {len(result_df[result_df['is_anomaly']])} anomalies) for {anomaly_type}")
                return jsonify({"type": "success", "results": result})

            except Exception as e:
                logger.error(f"Error running anomaly {anomaly_type}: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Error running anomaly detection: {str(e)}"}), 500
        @self.flask_app.route('/api/v0/run_prediction', methods=['GET'])
        def run_prediction():
            global vn
            workspace_id = request.args.get('workspace_id')
            prediction_type = request.args.get('prediction_type')

            # Validate input parameters
            if not workspace_id or not prediction_type:
                return jsonify({"type": "error", "error": "Workspace ID and prediction type are required."}), 400 

            # Ensure Vanna is initialized
            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            # Fetch workspace metadata
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            # Get prediction configuration
            predictions = json.loads(workspace.get("predictions", "[]"))
            prediction = next((p for p in predictions if p['type'] == prediction_type), None)
            if not prediction:
                return jsonify({"type": "error", "error": f"Prediction type {prediction_type} not found."}), 404

            if not prediction.get('enabled', True):
                return jsonify({"type": "error", "error": f"Prediction type {prediction_type} is disabled."}), 400

            try:
                # Step 1: Fetch historical data using the SQL query
                df = vn.run_sql(prediction['sql_query'])
                logger.info(f"Raw data from SQL query:\n{df}")
                if df.empty:
                    return jsonify({"type": "error", "error": "SQL query returned no results."}), 400

                # Step 2: Preprocess data based on prediction parameters
                algorithm = prediction.get('algorithm')
                parameters = prediction.get('parameters', {})
                target = parameters.get('target')
                features = parameters.get('features', [])
                inflation_rate = parameters.get('inflation_rate', None)
                if inflation_rate is None:
                    logger.warning(f"No inflation rate provided for prediction {prediction_type}, defaulting to 0")
                    inflation_rate = 0
                inflation_rate = float(inflation_rate) / 100  # Convert percentage to decimal
                logger.info(f"Using inflation rate: {inflation_rate}")

                # Standard preprocessing: Handle NaN, convert dates, etc.
                df = df.replace({np.nan: None})  # Replace NaN with None for JSON compatibility
                for col in df.columns:
                    if df[col].dtype == 'datetime64[ns]':
                        df[col] = df[col].astype(str)  # Convert dates to strings for JSON

                # Initialize result_df to store predictions
                result_df = df.copy()

                # Step 3: Apply prediction logic based on algorithm
                if algorithm == 'mean':
                    if not target or target not in df.columns:
                        return jsonify({"type": "error", "error": "Target column missing or invalid."}), 400
                    if prediction_type == 'price_trend':
                        # Custom logic for price trend prediction
                        avg_price_df = df.groupby('item_number', as_index=False)[target].mean()
                        avg_price_df[f'predicted_{target}'] = (avg_price_df[target] * (1 + inflation_rate)).round(2)
                        merged_df = df[['item_number', 'description']].drop_duplicates()
                        result_df = avg_price_df.merge(merged_df, on='item_number')[['description', target, f'predicted_{target}']]
                        result_df = result_df.rename(columns={
                            'description': 'Description',
                            target: target.upper(),
                            f'predicted_{target}': f'Predicted {target.upper()}'
                        })
                    else:
                        # General mean-based prediction (table output)
                        result_df[f'predicted_{target}'] = (df[target] * (1 + inflation_rate)).round(2)

                elif algorithm == 'standard_deviation':
                    if not target or target not in df.columns:
                        return jsonify({"type": "error", "error": "Target column missing or invalid."}), 400
                    std_value = df[target].std()
                    result_df[f'predicted_{target}_std'] = std_value  # Add std as a column

                elif algorithm == 'linear_regression':
                    if not features or not target or not all(f in df.columns for f in features) or target not in df.columns:
                        return jsonify({"type": "error", "error": "Invalid features or target column."}), 400
                    X = df[features]
                    y = df[target]
                    model = LinearRegression()
                    model.fit(X, y)
                    result_df[f'predicted_{target}'] = model.predict(X) * (1 + inflation_rate)

                elif algorithm == 'logistic_regression':
                    if not features or not target or not all(f in df.columns for f in features) or target not in df.columns:
                        return jsonify({"type": "error", "error": "Invalid features or target column."}), 400
                    X = df[features]
                    y = df[target]
                    model = LogisticRegression()
                    model.fit(X, y)
                    result_df[f'predicted_{target}_prob'] = model.predict_proba(X)[:, 1]
                    result_df[f'predicted_{target}'] = (result_df[f'predicted_{target}_prob'] > 0.5).astype(int)

                # Convert DataFrame to list of dicts for JSON response
                result = result_df.to_dict(orient='records')
                return jsonify({"type": "success", "df": result})

            except Exception as e:
                logger.error(f"Error running prediction {prediction_type}: {str(e)}")
                return jsonify({"type": "error", "error": f"Error running prediction: {str(e)}"}), 500
            


             ############################# aiagents ######################################
        

        @self.flask_app.route("/api/v0/get_custom_workspace", methods=["GET"])
        def get_custom_workspace():
            workspace_name = request.args.get("workspace_name")
            if not workspace_name:
                return jsonify({"error": "workspace_name is required"}), 400

            if not hasattr(self, "workspace_collection"):
                return jsonify({"error": "Workspace collection not initialized"}), 500

            try:
                results = self.workspace_collection.get()
                if results and results.get("metadatas"):
                    ids = results.get("ids", [])
                    metadatas = results.get("metadatas", [])
                    
                    for i, meta in enumerate(metadatas):
                        if meta.get("name") == workspace_name:
                            logger.info(f"get_custom_workspace: Found workspace '{workspace_name}' with ID {ids[i]}")
                            return jsonify({"id": ids[i], "name": meta.get("name")})
            
                logger.warning(f"get_custom_workspace: Workspace '{workspace_name}' not found")
                return jsonify({"error": "Workspace not found"}), 404

            except Exception as e:
                logger.error(f"get_custom_workspace error: {str(e)}")
                return jsonify({"error": str(e)}), 500


        @self.flask_app.route("/api/v0/get_agent_config")
        def get_agent_config():
            workspace_id = request.args.get("workspace_id")
            agent_type = request.args.get("agent_type")

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                logger.warning(f"get_agent_config: Workspace {workspace_id} not found")
                return jsonify({"agent_config": None})

            workspace_key = f"agent_config_{agent_type}"

            try:
                import json
                raw = workspace.get(workspace_key, "{}")
                config = json.loads(raw)
                logger.info(f"get_agent_config: Returning config for workspace {workspace_id} / type {agent_type}: {config}")
                return jsonify({"agent_config": config})
            except Exception as e:
                logger.error(f"get_agent_config: Failed to parse config for workspace {workspace_id}: {e}")
                return jsonify({"agent_config": None})

        

        @self.flask_app.route("/api/v0/save_agent_config", methods=["POST"])
        def save_agent_config():
            data = request.json

            workspace_id = data["workspace_id"]
            agent_config = data["agent_config"]
            agent_type = agent_config["agent_type"]

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"success": False, "error": "Workspace not found"}), 404

            try:
                import json

                # Store config using workspace metadata, same structure as predictions
                workspace_key = f"agent_config_{agent_type}"
                workspace[workspace_key] = json.dumps(agent_config)

                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )

                return jsonify({"success": True})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
            


        # def send_alert_email_with_csv(recipients,subject,body,rows,filename="affected_records.csv"):
        #     if not recipients:
        #         raise ValueError("No email recipients provided")

        #     msg = MIMEMultipart()
        #     msg["From"] = SMTP_FROM
        #     msg["To"] = ", ".join(recipients)
        #     msg["Subject"] = subject

        #     # Email body
        #     msg.attach(MIMEText(body, "plain", "utf-8"))

        #     # Attach CSV
        #     csv_data = rows_to_csv(rows)
        #     if csv_data:
        #         part = MIMEBase("application", "octet-stream")
        #         part.set_payload(csv_data.encode("utf-8"))
        #         encoders.encode_base64(part)
        #         part.add_header(
        #             "Content-Disposition",
        #             f'attachment; filename="{filename}"'
        #         )
        #         msg.attach(part)

        #     try:
        #         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
        #             server.starttls()
        #             server.login(SMTP_USER, SMTP_PASS)
        #             server.sendmail(SMTP_FROM, recipients, msg.as_string())

        #         logger.info(f"Alert email sent to {recipients}")
        #         return True

        #     except Exception as e:
        #         logger.error("SMTP send failed", exc_info=True)
        #         raise RuntimeError(f"SMTP send failed: {str(e)}")

        def send_alert_email_with_csv(recipients, subject, body, rows, filename="affected_records.csv", config_path="feedback_config.json"):
            if not recipients:
                raise ValueError("No email recipients provided")

            # cfg = load_email_config(config_path)
            cfg = load_email_config()


            # Resolve SMTP settings defensively from stored config shapes
            provider = cfg.get("email_provider", "gmail")

            SMTP_SERVER = cfg.get("smtp_server") or ("smtp.office365.com" if provider == "outlook" else "smtp.gmail.com")
            SMTP_PORT = int(cfg.get("smtp_port", 587))

            # Sender credentials may be stored at top-level or under provider keys
            SMTP_USER = (
                cfg.get("sender_email")
                or cfg.get("outlook", {}).get("sender_email")
                or cfg.get("gmail", {}).get("sender_email")
                or ""
            )

            SMTP_PASS = (
                cfg.get("sender_password")
                or cfg.get("outlook", {}).get("sender_password")
                or cfg.get("gmail", {}).get("sender_password")
                or ""
            )

            SMTP_FROM = SMTP_USER or cfg.get("sender_email") or cfg.get("outlook", {}).get("sender_email") or cfg.get("gmail", {}).get("sender_email") or ""
            CC = cfg.get("cc", "")

            msg = MIMEMultipart()
            msg["From"] = SMTP_FROM
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            

            # Optional CC
            cc_list = []
            if CC and CC.strip():
                cc_list = [c.strip() for c in CC.split(",") if c.strip()]
                msg["Cc"] = ", ".join(cc_list)

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Convert rows -> CSV
            csv_data = rows_to_csv(rows)
            if csv_data:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(csv_data.encode("utf-8"))
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                msg.attach(part)

            # All recipients (To + CC)
            all_recipients = recipients + cc_list

            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.sendmail(SMTP_FROM, all_recipients, msg.as_string())

                return True

            except Exception as e:
                raise RuntimeError(f"SMTP send failed: {str(e)}")


      
        @self.flask_app.route("/api/v0/test_agent_alert", methods=["POST"])
        def test_agent_alert():
            global vn

            data = request.json
            workspace_id = data.get("workspace_id")
            sql = data.get("sql")
            recipients = data.get("recipients", [])
            scenario_id = data.get("scenario_id", "DEFAULT")

            if not workspace_id or not sql:
                return jsonify({
                    "success": False,
                    "error": "Workspace ID and SQL are required."
                }), 400

            if not recipients:
                return jsonify({
                    "success": False,
                    "error": "No recipients provided."
                }), 400

            try:
                # ✅ SAME initialization flow
                initialized, error = ensure_vanna_initialized(self, workspace_id)
                if not initialized:
                    return jsonify({
                        "success": False,
                        "error": error
                    }), 400

                # ✅ SAME SQL execution
                df = vn.run_sql(sql)
                row_count = len(df) if df is not None else 0
                rows = df.to_dict(orient="records") if row_count > 0 else []

                # 🧠 Scenario-aware messaging
                scenario_cfg = SCENARIO_MESSAGES.get(
                    scenario_id,
                    SCENARIO_MESSAGES["DEFAULT"]
                )

                subject = f"[TEST ALERT] {scenario_cfg['subject']}"

                body = (
                    "⚠️ This is a TEST alert generated by the Agent.\n\n"
                    f"Workspace ID : {workspace_id}\n"
                    f"Scenario     : {scenario_id}\n"
                    f"Affected Rows: {row_count}\n\n"
                    "----------------------------------------\n\n"
                    f"{scenario_cfg['body']}"
                )

                # 📎 Send with CSV attachment (ALL rows)
                # send_alert_email_with_csv(
                #     recipients=recipients,
                #     subject=subject,
                #     body=body,
                #     rows=rows,
                #     filename=f"{scenario_id.lower()}_affected_records.csv"
                # )
                send_alert_email_with_csv(
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    rows=rows,
                    filename=f"{scenario_id.lower()}_affected_records.csv",
                    config_path="feedback_config.json"
                )




                return jsonify({
                    "success": True,
                    "message": f"Test alert sent successfully ({row_count} rows attached)."
                })

            except Exception as e:
                logger.error("Test alert failed", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        



#########################################teams integration ###############################
   


 
 
     


        #save teams without webhook and call back url

        @self.flask_app.route('/save_teams_config', methods=['POST'])
        def save_teams_config():
            try:
                data = request.json
                workspace_id = data.get('workspace_id')
                teams_config = data.get('teams_config')

                if not workspace_id:
                    return jsonify({'error': 'Workspace ID is required'}), 400
                if not teams_config:
                    return jsonify({'error': 'Teams configuration is required'}), 400

                # Disable Teams in all other workspaces
                all_workspaces = self.workspace_collection.get()
                if all_workspaces and all_workspaces.get("ids"):
                    for ws_id, metadata in zip(all_workspaces["ids"], all_workspaces["metadatas"]):
                        if ws_id != workspace_id:
                            updated_metadata = metadata.copy()
                            if "teams_config" in updated_metadata:
                                teams_cfg = json.loads(updated_metadata["teams_config"])
                                teams_cfg["enabled"] = False
                                updated_metadata["teams_config"] = json.dumps(teams_cfg)
                                self.workspace_collection.update(
                                    ids=[ws_id],
                                    metadatas=[updated_metadata],
                                    documents=[f"Workspace: {updated_metadata.get('name', '')}"]
                                )

                # Update current workspace metadata
                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({'error': f'Workspace with ID {workspace_id} not found'}), 404

                metadata = existing["metadatas"][0]
                metadata["teams_config"] = json.dumps(teams_config)

                global vn

                if teams_config.get("enabled", False):
                    llm_config = json.loads(metadata.get("llm_config", "{}"))
                    db_config = json.loads(metadata.get("db_config", "{}"))

                    if not llm_config or not db_config:
                        return jsonify({'error': 'LLM and DB configuration required for Teams integration'}), 400

                    # Initialize Vanna
                    result = initialize_vanna_instance(workspace_id, llm_config, db_config)
                    if not result["success"]:
                        return jsonify({"error": result["error"]}), 500
                else:
                    vn = None

                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[metadata],
                    documents=[f"Workspace: {metadata['name']}"]
                )

                logger.info(f"Saved Teams config for workspace: ID={workspace_id}")
                return jsonify({'message': 'Teams configuration saved successfully'}), 200

            except Exception as e:
                logger.error(f"Error saving Teams config: {str(e)}", exc_info=True)
                return jsonify({'error': 'Failed to save Teams config'}), 500

            


            #getting from the db
 
        @self.flask_app.route("/get_teams_config", methods=["GET"])
        def get_teams_config():
            logger.info("starting getting teams")
            workspace_id = request.args.get("workspace_id")
           
            if not workspace_id:
                return jsonify({"error": "Workspace ID is required"}), 400

            existing = self.workspace_collection.get(ids=[workspace_id])
           
            if not existing or not existing.get("metadatas"):
                return jsonify({"error": f"Workspace with ID {workspace_id} not found"}), 404

            metadata = existing["metadatas"][0]
            teams_config = json.loads(metadata.get("teams_config", "{}"))

            return jsonify({"success": True, "teams_config": teams_config}), 200

#Without follow up 
        def get_active_workspace_name():
            all_workspaces =self.workspace_collection.get()
            if not all_workspaces or not all_workspaces.get("ids"):
                return None

            for ws_id, metadata in zip(all_workspaces["ids"], all_workspaces["metadatas"]):
                teams_config_str = metadata.get("teams_config", "{}")
                try:
                    teams_config = json.loads(teams_config_str)
                    if teams_config.get("enabled", False):
                        # Assuming the workspace name is stored in metadata under the key 'name'
                        return metadata.get("name")
                except json.JSONDecodeError:
                    continue

            return None

        @self.flask_app.route("/api/workspaces", endpoint="list_workspaces")
        def list_workspaces(**kwargs):
            """Return all workspace ids and names from ChromaDB as JSON."""

            all_workspaces = self.workspace_collection.get()

            result = []

            if all_workspaces:
                ids = all_workspaces.get("ids", [])
                metas = all_workspaces.get("metadatas", [])

                for wid, meta in zip(ids, metas):
                    name = meta.get("name")

                    if name:
                        result.append({
                            "id": wid,
                            "name": name
                        })

            return jsonify(result)




        @self.flask_app.route("/superadmin/user_tokens", methods=["GET"])
        @self.requires_role(["superadmin"])
        @self.requires_auth
        def show_token_count(user=None, user_id=None):
            """
            Retrieve total token count and total cost for a user.
            Handles UUID formatting safely.
            """
            # Prefer query param → fallback to passed user_id (from auth/session)
            input_user_id = request.args.get("user_id") or user_id

            if not input_user_id:
                return jsonify({"error": "user_id is required"}), 400

            # Normalize UUID: remove spaces, make lowercase, ensure hyphens if missing
            normalized_user_id = str(input_user_id).strip().lower()
            if is_uuid(normalized_user_id.replace("-", "")):
                # Re-add hyphens if someone sent it without (very common mistake)
                if len(normalized_user_id) == 32 and '-' not in normalized_user_id:
                    normalized_user_id = (
                        normalized_user_id[:8] + '-' +
                        normalized_user_id[8:12] + '-' +
                        normalized_user_id[12:16] + '-' +
                        normalized_user_id[16:20] + '-' +
                        normalized_user_id[20:]
                    )

            logger.info(f"Normalized user_id for query: {normalized_user_id}", extra={"billing": True})

            sql = """
                SELECT
                    ISNULL(SUM(token_count), 0)         AS total_tokens,
                    ISNULL(SUM(cost_usd), 0.0)          AS total_cost
                FROM dbo.users
                WHERE user_id = ?
            """

            conn = None
            try:
                conn = self.cache._get_db_connection()  # assuming this returns a valid connection
                logger.info(
                    f"Connected to DB: {conn.getinfo(pyodbc.SQL_DATABASE_NAME)}",
                    extra={"token_count": True}
                )

                cursor = conn.cursor()
                cursor.execute(sql, (normalized_user_id,))
                row = cursor.fetchone()

                total_tokens = int(row[0]) if row and row[0] is not None else 0
                total_cost   = float(row[1]) if row and row[1] is not None else 0.0

                logger.info(
                    f"User {normalized_user_id} → tokens={total_tokens}, cost=${total_cost:.8f}",
                    extra={"token_count": True, "billing": True}
                )

                return jsonify({
                    "user_id": normalized_user_id,
                    "token_count": total_tokens,
                    "cost_usd": round(total_cost, 8)
                }), 200

            except Exception as e:
                logger.error(
                    f"Error retrieving token & cost for user {normalized_user_id}: {str(e)}",
                    exc_info=True
                )
                return jsonify({"error": "Failed to retrieve token data", "detail": str(e)}), 500

            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

            # finally:
            #     if conn:
            #         conn.close()
        from uuid import UUID

        def is_uuid(val: str) -> bool:
            try:
                UUID(str(val))
                return True
            except Exception:
                return False



        def resolve_workspace_id_by_name(self, workspace_name: str) -> str | None:
            """
            Resolve workspace UUID from workspace display_name.
            """
            rec = self.workspace_collection.get(
                where={"display_name": workspace_name}
                # ❌ do NOT use include=["ids"]
            )

            ids = rec.get("ids") or []
            return ids[0] if ids else None

        def resolve_workspace_id(self, value):

            if not value:
                return None

            value = value.strip()

            # If already UUID → return
            if is_uuid(value):
                return value

            # Else resolve by metadata name
            recs = self.workspace_collection.get(include=["metadatas"])

            ids = recs.get("ids", [])
            metas = recs.get("metadatas", [])

            target = value.lower().replace("_", "-")

            for wid, meta in zip(ids, metas):

                name = (meta.get("name") or "").lower().replace("_", "-")

                if name == target:
                    return wid

            return None


        @self.flask_app.route("/superadmin/prediction_token", methods=["GET"])
        @self.requires_role(["superadmin"])
        @self.requires_auth
        def show_prediction_token_count(user=None, workspace_id=None):

            raw = request.args.get("workspace_id") or workspace_id

            logger.info(f"[Prediction] Raw workspace param: {raw}")

            workspace_id = resolve_workspace_id(self, raw)

            if not workspace_id:
                return jsonify({"error": "Workspace not found"}), 404

            try:
                rec = self.workspace_collection.get(
                    ids=[workspace_id],
                    include=["metadatas"],
                )

                meta = (rec.get("metadatas") or [{}])[0] or {}

                return jsonify({
                    "prediction_total_tokens": meta.get("prediction_total_tokens", 0),
                    "prediction_input_tokens": meta.get("prediction_input_tokens", 0),
                    "prediction_output_tokens": meta.get("prediction_output_tokens", 0),
                    "prediction_cost_usd": meta.get("prediction_cost_usd", 0.0),
                    "prediction_model_name": meta.get("prediction_model_name"),
                }), 200

            except Exception:
                logger.exception(f"Prediction fetch failed for {workspace_id}")
                return jsonify({"error": "Failed to retrieve prediction token count"}), 500


            

        @self.flask_app.route("/superadmin/anomaly_token", methods=["GET"])
        @self.requires_role(["superadmin"])
        @self.requires_auth
        def show_anomaly_token_count(user=None, workspace_id=None):

            raw = request.args.get("workspace_id") or workspace_id

            workspace_id = resolve_workspace_id(self, raw)

            if not workspace_id:
                return jsonify({"error": "Workspace not found"}), 404

            try:
                rec = self.workspace_collection.get(
                    ids=[workspace_id],
                    include=["metadatas"],
                )

                meta = (rec.get("metadatas") or [{}])[0] or {}

                return jsonify({
                    "anomaly_total_tokens": meta.get("anomaly_total_tokens", 0),
                    "anomaly_input_tokens": meta.get("anomaly_input_tokens", 0),
                    "anomaly_output_tokens": meta.get("anomaly_output_tokens", 0),
                    "anomaly_cost_usd": meta.get("anomaly_cost_usd", 0.0),
                    "anomaly_model_name": meta.get("anomaly_model_name"),
                }), 200

            except Exception:
                logger.exception(f"Anomaly fetch failed for {workspace_id}")
                return jsonify({"error": "Failed to retrieve anomaly token count"}), 500


                        
        
        def hash_password(password):
            """Simple password hashing with SHA256 (you can switch to bcrypt for better security)."""
            return hashlib.sha256(password.encode()).hexdigest()
        def clean_metadata(metadata_dict):
            """Ensure no None values — replace with empty string."""
            return {k: ("" if v is None else v) for k, v in metadata_dict.items()}

        @self.flask_app.route("/api/add_user", methods=["POST"])
        @self.requires_auth
        def add_user(user=None):
            """
            Add a user into ChromaDB 'users' collection.
            Accepts: { username, password, workspace [, tables] }
            - Creates 'users' collection if missing.
            - Hashes password (SHA256) before storing.
            - Validates workspace against existing workspace_collection (if available).
            """

            try:
                data = request.get_json() or {}
                username = (data.get("username") or "").strip()
                password = data.get("password") or ""
                workspace = data.get("workspace") or ""
                # tables = data.get("tables", [])  # Uncomment if you want to store table permissions

                if not username or not password:
                    return jsonify({"error": "Username and password are required"}), 400

                # Get or create 'users' collection
                existing_collections = self.client.list_collections()
                if "users" not in existing_collections:
                    users_collection = self.client.create_collection(name="users")
                else:
                    users_collection = self.client.get_collection(name="users")

                # Check duplicate username inside 'users' collection
                existing_user = users_collection.get(where={"username": username})
                if existing_user and existing_user.get("ids"):
                    return jsonify({"error": "Username already exists"}), 400

                # Hash password
                password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                logger.info(f"password user list: {password_hash}")

                # Validate workspace name exists in your workspace_collection (if available)
                workspace_valid = False
                try:
                    if hasattr(self, "workspace_collection") and self.workspace_collection is not None:
                        ws_get = self.workspace_collection.get()
                        if ws_get and ws_get.get("metadatas"):
                            ws_names = [
                                md.get("name")
                                for md in ws_get.get("metadatas")
                                if isinstance(md, dict) and md.get("name")
                            ]
                            if workspace and workspace in ws_names:
                                workspace_valid = True
                except Exception:
                    workspace_valid = False  # Fallback if no workspace collection

                # Add user record
                metadata = {
                    "username": username,
                    "password_hash": password_hash,
                    "workspace": workspace or "",
                    "workspace_valid": bool(workspace_valid),
                    # "tables": tables  # Uncomment if storing table permissions
                }

                users_collection.add(
                    ids=[str(uuid.uuid4())],
                    metadatas=[metadata],
                    documents=["user record"]
                )

                return jsonify({
                    "message": f"User '{username}' added successfully",
                    "workspace_valid": workspace_valid
                }), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 500



        @self.flask_app.route("/api/update_user_config", methods=["POST"])
        @self.requires_auth
        def update_user_config(user=None):
            """
            Update the agent configuration for a user.
            Expected JSON: { "user_id": str, "agent_config": list }
            """
            try:
                # Security check
                current_user_role = user.get("role")
                if current_user_role not in ["admin", "superadmin"]:
                    return jsonify({"error": "Unauthorized"}), 403

                data = request.get_json() or {}
                logger.info(f"update_user_config received payload: {data}")
                
                target_user_id = data.get("user_id")
                agent_config = data.get("agent_config", [])

                if not target_user_id:
                     return jsonify({"error": "user_id is required"}), 400

                if hasattr(self.auth, 'update_user_config'):
                    success = self.auth.update_user_config(target_user_id, agent_config)
                    if success:
                        return jsonify({"message": "Configuration updated successfully"})
                    else:
                        return jsonify({"error": "Failed to update configuration"}), 500
                else:
                     return jsonify({"error": "Auth provider does not support updates"}), 501

            except Exception as e:
                logger.error(f"Error in update_user_config: {e}")
                return jsonify({"error": str(e)}), 500


        @self.flask_app.route('/api/list_users', methods=['GET'])
        def list_users():
            try:
                results = self.users_collection.get()
                if not results or not results.get("ids"):
                    return jsonify({"users": []}), 200

                ids = results.get("ids", [])
                metadatas = results.get("metadatas", [{}] * len(ids))

                user_list = []
                for i, user_id in enumerate(ids):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    user_list.append({
                        "id": user_id,  
                        "username": metadata.get("username", ""),
                        "password_hash": metadata.get("password_hash", ""),
                        "workspace": metadata.get("workspace", "")
                    })
                logger.info(f"Existing user list: {user_list}")
                return jsonify({"users": user_list}), 200

            except Exception as e:
                logger.error(f"Error listing users: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to list users"}), 500




        @self.flask_app.route("/api/delete_user/<user_id>", methods=["DELETE"])
        @self.requires_auth
        def delete_user(user_id, user=None):
            """
            Delete a user from the 'user' collection by ID.
            """
            try:
                # Check if the user exists
                existing_data = self.users_collection.get(ids=[user_id])
                if not existing_data or not existing_data.get("ids"):
                    return jsonify({"error": f"User with ID '{user_id}' not found"}), 404

                # Delete user
                self.users_collection.delete(ids=[user_id])

                return jsonify({"message": f"User '{user_id}' deleted successfully"}), 200

            except Exception as e:
                logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
                return jsonify({"error": f"Failed to delete user {user_id}"}), 500
            
  
        def get_monthly_billing_summary(self, month: str, user_id: str | None = None):
            logger.info(f"[BILLING] Monthly summary for {month}, user_id={user_id}")

            start_dt, end_dt = month_range(month)
            billing = {}
            logger.info(f"[BILLING] Monthly summary for start {start_dt} end {end_dt}", extra={"admin": True})
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.user_mgmt_config['server']},{self.user_mgmt_config['port']};"
                f"DATABASE={self.user_mgmt_config['database']};"
                f"UID={self.user_mgmt_config['username']};"
                f"PWD={self.user_mgmt_config['password']};"
                f"Trusted_Connection=no;"
                f"Connection Timeout=30;"
            )

            conn = pyodbc.connect(conn_str, timeout=30)

            cursor = conn.cursor()

            query = """
            SELECT
                workspace_name,
                SUM(token_count) AS tokens,
                SUM(cost_usd) AS cost
            FROM dbo.users
            WHERE created_at >= ?
            AND created_at < ?
            """

            params = [start_dt, end_dt]
            logger.info(f"[BILLING] User {user_id}", extra={"admin": True})
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " GROUP BY workspace_name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            logger.info(f"[BILLING] User rows: {rows}", extra={"admin": True})

            for ws, tokens, cost in rows:
                ws = ws or "default"
                billing.setdefault(ws, init_ws())
                billing[ws]["user_tokens"] += int(tokens or 0)
                billing[ws]["user_cost"] += float(cost or 0.0)

            cursor.close()
            conn.close()

            # Chroma aggregation stays unchanged
            chroma_records = self.workspace_collection.get(include=["metadatas"])
            for meta in chroma_records.get("metadatas", []):
                ws = meta.get("name")
                if not ws:
                    continue

                billing.setdefault(ws, init_ws())
                billing[ws]["prediction_tokens"] += meta.get("prediction_total_tokens", 0)
                billing[ws]["prediction_cost"] += meta.get("prediction_cost_usd", 0.0)
                billing[ws]["anomaly_tokens"] += meta.get("anomaly_total_tokens", 0)
                billing[ws]["anomaly_cost"] += meta.get("anomaly_cost_usd", 0.0)

            for b in billing.values():
                b["total_tokens"] = (
                    b["user_tokens"] + b["prediction_tokens"] + b["anomaly_tokens"]
                )
                b["total_cost"] = round(
                    b["user_cost"] + b["prediction_cost"] + b["anomaly_cost"], 6
                )

            return billing




        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        def month_range(yyyy_mm: str):
            start = datetime.strptime(yyyy_mm, "%Y-%m")
            end = start + relativedelta(months=1)
            return start, end

        def init_ws():
            return {
                "user_tokens": 0,
                "user_cost": 0.0,
                "prediction_tokens": 0,
                "prediction_cost": 0.0,
                "anomaly_tokens": 0,
                "anomaly_cost": 0.0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }





        @self.flask_app.route("/superadmin/update_user_access", methods=["POST"])
        @self.requires_role(["superadmin"])
        @self.requires_auth
        def update_user_access(user=None, user_id=None, workspace_valid=False):
            """
            Update user access (enable/disable) in the 'users' collection.
            Expects JSON: { "user_id": "...", "workspace_valid": true }
            This version MERGES the workspace_valid flag into existing metadata
            (so we don't wipe out username/password_hash/etc).
            """
            try:
                data = request.get_json(silent=True) or {}
                if not data:
                    return jsonify({"error": "Missing JSON body"}), 400

                user_id = data.get("user_id") or user_id
                if not user_id:
                    return jsonify({"error": "Missing user_id"}), 400

                # Be tolerant with workspace_valid types (string/"true"/1 etc)
                raw_val = data.get("workspace_valid", workspace_valid)
                if isinstance(raw_val, str):
                    workspace_valid_bool = raw_val.lower() in ("1", "true", "yes", "on")
                else:
                    workspace_valid_bool = bool(raw_val)

                logger.info(
                    f"Updating user access for user_id: {user_id} to workspace_valid: {workspace_valid_bool}",
                    extra={"token_count": True}
                )

                # Get existing metadata for the user id
                existing = None
                try:
                    existing = self.users_collection.get(ids=[user_id])
                except Exception as ex:
                    logger.warning(f"users_collection.get failed for id {user_id}: {ex}", exc_info=True)
                    existing = None

                # Extract metadata dict robustly (Chroma returns {'metadatas': [ {...} ], 'ids': [...], ...})
                existing_meta = {}
                if isinstance(existing, dict):
                    metas = existing.get("metadatas") or []
                    if isinstance(metas, list) and len(metas) > 0 and isinstance(metas[0], dict):
                        existing_meta = metas[0].copy()
                else:
                    # safe fallback: try to extract first element if returned as list/other shape
                    try:
                        maybe_first = (existing or [{}])[0]
                        if isinstance(maybe_first, dict):
                            existing_meta = maybe_first.copy()
                    except Exception:
                        existing_meta = {}

                # If we couldn't find the user, return 404
                if not existing_meta and not (isinstance(existing, dict) and existing.get("ids")):
                    logger.info(f"User not found while updating access: {user_id}")
                    return jsonify({"error": "User not found", "user_id": user_id}), 404

                existing_access = bool(existing_meta.get("workspace_valid", False))

                # Merge: preserve all other metadata keys and only update workspace_valid
                updated_meta = existing_meta.copy() if isinstance(existing_meta, dict) else {}
                updated_meta["workspace_valid"] = workspace_valid_bool

                # Update the user in the collection with the merged metadata
                try:
                    self.users_collection.update(
                        ids=[user_id],
                        metadatas=[updated_meta]
                    )
                except Exception as e:
                    logger.error(f"Chroma update failed for user {user_id}: {e}", exc_info=True)
                    return jsonify({"error": "Failed to update user access"}), 500

                logger.info(
                    f"User access updated for user_id: {user_id} from {existing_access} to {workspace_valid_bool}",
                    extra={"token_count": True}
                )

                # Return authoritative value
                return jsonify({"message": "User access updated", "user_id": user_id, "workspace_valid": updated_meta.get("workspace_valid", False)}), 200

            except Exception as e:
                logger.error(f"Error updating user access for user {user_id}: {str(e)}", exc_info=True)
                return jsonify({"error": "Failed to update user access"}), 500


        @self.flask_app.route("/superadmin/billing_summary", methods=["GET"])
        @self.requires_role(["superadmin"])
        @self.requires_auth
        def billing_summary(user=None):
            month = request.args.get("month")
            user_id = request.args.get("user_id")  # 👈 NEW

            if not month:
                return jsonify({"error": "month is required"}), 400

            data = get_monthly_billing_summary(self, month, user_id)

            return jsonify({
                "month": month,
                "user_id": user_id,
                "workspaces": data
            })


        from datetime import datetime, timedelta

        def next_month(yyyy_mm: str) -> str:
            """
            Given 'YYYY-MM', return next month in same format.
            Example: '2025-12' -> '2026-01'
            """
            dt = datetime.strptime(yyyy_mm, "%Y-%m")
            year = dt.year + (dt.month // 12)
            month = (dt.month % 12) + 1
            return f"{year:04d}-{month:02d}"

        def validate_month(yyyy_mm: str):
            try:
                datetime.strptime(yyyy_mm, "%Y-%m")
            except ValueError:
                raise ValueError("Invalid month format, expected YYYY-MM")


        @self.flask_app.route("/superadmin/billing_export")
        def billing_export():
            month = request.args.get("month")
            data = get_monthly_billing_summary(month)

            rows = []
            for ws, b in data.items():
                rows.append({
                    "Workspace": ws,
                    "User Tokens": b["user_tokens"],
                    "Prediction Tokens": b["prediction_tokens"],
                    "Anomaly Tokens": b["anomaly_tokens"],
                    "Total Tokens": b["total_tokens"],
                    "Total Cost (USD)": b["total_cost"],
                })

            return export_to_excel(rows, filename=f"billing_{month}.xlsx")


  
        ###################sop documentations ##############################


        # @self.flask_app.route("/sop-chat")
        # @self.requires_auth
        # def sop_chat(user):
        #         return render_template("sop_chat.html")

        @self.flask_app.route("/sop-chat")
        @self.requires_auth
        def sop_chat(user):
            role = user.get("role", "user")  # admin / user
            return render_template("sop_chat.html", role=role)

            # return render_template(
            #     "sop_chat.html",
            #     role=role
            # )
            

            
         

        
        # @self.flask_app.route("/anomaly-page")
        # def anomaly_page():
        #     return Response(anomaly_template, mimetype='text/html')
        

        #uploading sop files
        # @self.flask_app.route("/api/sop/upload", methods=["POST"])
        # @self.requires_auth
        # def upload_sop(user):
        #     file = request.files.get("file")
        #     if not file:
        #         return {"error": "No file uploaded"}, 400

        #     df = pd.read_csv(file)
        #     doc_id = str(uuid4())

        #     docs, metas, ids = [], [], []

        #     for row in df.itertuples(index=False):
        #         text = " ".join(map(str, row)).strip()
        #         if not text or text.lower() == "nan":
        #             continue

        #         docs.append(text)
        #         metas.append({
        #             "doc_id": doc_id,
        #             "filename": file.filename,
        #             "source": "SOP",
        #             "uploaded_by": user.get("username"),
        #             "uploaded_at": datetime.utcnow().isoformat()
        #         })
        #         ids.append(f"{doc_id}_{len(ids)}")

        #     if not docs:
        #         return {"error": "CSV contains no usable SOP data"}, 400

        #     self.sop_collection.add(
        #         documents=docs,
        #         metadatas=metas,
        #         ids=ids
        #     )

        #     return {"message": "SOP trained successfully", "chunks": len(docs)}

        @self.flask_app.route("/api/sop/upload", methods=["POST"])
        @self.requires_auth
        def upload_sop(user):
            file = request.files.get("file")
            if not file:
                return {"error": "No file uploaded"}, 400

            try:
                # Read CSV
                df = pd.read_csv(file)
                
                # Basic validation: Check if required columns exist (optional but good)
                # if 'Process_Name' not in df.columns: ...
                
                doc_id = str(uuid4())
                docs, metas, ids = [], [], []

                # IMPROVEMENT: Create structured documents instead of raw text
                for _, row in df.iterrows():
                    # Create a dictionary of the row, excluding NaN values
                    row_data = {k: v for k, v in row.items() if pd.notna(v)}
                    
                    if not row_data:
                        continue

                    # Format: "Process: [Name], Purpose: [Text], Prerequisites: [Text]..."
                    # This is much easier for the LLM to understand than a pipe-separated string.
                    formatted_text = ", ".join([f"{k}: {v}" for k, v in row_data.items()])
                    
                    docs.append(formatted_text)
                    metas.append({
                        "doc_id": doc_id,
                        "filename": file.filename,
                        "source": "SOP", # CRITICAL: Ensures querying by source works
                        "uploaded_by": user.get("username"),
                        "uploaded_at": datetime.utcnow().isoformat()
                    })
                    ids.append(f"{doc_id}_{len(ids)}")

                if not docs:
                    return {"error": "CSV contains no usable SOP data"}, 400

                self.sop_collection.add(
                    documents=docs,
                    metadatas=metas,
                    ids=ids
                )

                return {"message": "SOP trained successfully", "chunks": len(docs)}

            except Exception as e:
                print(f"[Upload Error] {e}")
                return {"error": "Failed to process file. Ensure it is a valid CSV."}, 500


        

        #listing sop files
        @self.flask_app.route("/api/sop/list", methods=["GET"])
        @self.requires_auth
        def list_sops(user):
            data = self.sop_collection.get(include=["metadatas"])

            if not data or not data.get("metadatas"):
                return []

            sop_map = {}

            for meta in data["metadatas"]:
                doc_id = meta["doc_id"]

                if doc_id not in sop_map:
                    sop_map[doc_id] = {
                        "doc_id": doc_id,
                        "filename": meta.get("filename"),
                        "uploaded_by": meta.get("uploaded_by"),
                        "uploaded_at": meta.get("uploaded_at"),
                        "chunks": 1
                    }
                else:
                    sop_map[doc_id]["chunks"] += 1

            return list(sop_map.values())




        
        #deleting sop files
        @self.flask_app.route("/api/sop/delete/<doc_id>", methods=["DELETE"])
        @self.requires_auth

        def delete_sop(user,doc_id):
            self.sop_collection.delete(where={"doc_id": doc_id})
            return {"message": "SOP deleted"}
        
        #prompt building
        
        # def build_sop_prompt(contexts, question):
        #     context_text = "\n\n".join(contexts)

        #     return f"""
        #         You are an SOP assistant.
        #         Answer ONLY using the SOP information below.
        #         If the answer is not present, say "This is not covered in the SOP."

        #         SOP Information:
        #         {context_text}

        #         Question:
        #         {question}

        #         Answer:
        #         """
        def build_sop_prompt(contexts, question):
            context_text = "\n\n---\n\n".join(contexts)

            return f"""
                You are a strict Warehouse SOP Assistant. 
                Your task is to answer the user's question based ONLY on the provided SOP context.

                RULES:
                1. If the answer is explicitly in the context, provide it clearly.
                2. If the context states a restriction (e.g., "Cannot do X", "Must be Y"), you must enforce it.
                3. If the information is missing or not mentioned in the context, strictly say: "This is not covered in the SOP."
                4. Do not use outside knowledge.
                5. Keep the answer concise and professional.

                SOP Context:
                {context_text}

                Question:
                {question}

                Answer:
                """

        def generate_with_openai(prompt: str) -> str:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return ""

                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful SOP assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )

                if not response.choices:
                    return ""

                content = response.choices[0].message.content
                if not content:
                    return ""

                return content

            except Exception as e:
                # IMPORTANT: never crash RAG pipeline
                print(f"[OpenAI ERROR] {e}")
                return ""



        
        #querying sop files
        @self.flask_app.route("/api/sop/query", methods=["POST"])
        @self.requires_auth
        def sop_query(user):
            data = request.get_json(silent=True) or {}
            question = data.get("question")

            if not question:
                return {"answer": "Question is required."}, 400

            results = self.sop_collection.query(
                query_texts=[question],
                where={"source": "SOP"},
                n_results=3
            )

            contexts = results.get("documents", [[]])[0]

            if not contexts or not any(c.strip() for c in contexts):
                return {"answer": "This is not covered in the SOP."}

            prompt = build_sop_prompt(contexts, question)

            raw_answer = generate_with_openai(prompt)
            answer = raw_answer.strip() if raw_answer else ""

            if not answer:
                return {"answer": "This is not covered in the SOP."}

            return {"answer": answer}




        # NGROK_URL = "https://2t54g94m-8084.inc1.devtunnels.ms/"
        # @self.flask_app.route("/api/messages", methods=["POST"])
        # async def messages():
        #         body = request.json
        #         logger.info(f"Request body: {body}")
        #         logger.info(f"Activity serviceUrl: {body.get('serviceUrl')}")  # Log incoming serviceUrl
        #         activity = Activity().deserialize(body)
        #         conversation_reference = TurnContext.get_conversation_reference(activity)
        #         logger.info(f"Raw conversation_reference: {conversation_reference.__dict__}")
       
               
 
        #         # Validate and fix service_url
        #         service_url = conversation_reference.service_url
        #         if not service_url or not service_url.startswith(("http://", "https://")):
        #             logger.warning(f"Invalid service_url: {service_url}. Using NGROK_URL: {NGROK_URL}")
        #             conversation_reference.service_url = NGROK_URL
        #             service_url = NGROK_URL
 
        #         # Test service_url accessibility (fixed unawaited coroutine)
        #         async def test_service_url(url):
        #             if aiohttp is None:
        #                 logger.warning("aiohttp not installed, skipping service_url test")
        #                 return None
        #             try:
        #                 async with aiohttp.ClientSession() as session:
        #                     async with session.get(url, timeout=5) as response:
        #                         logger.info(f"Service URL {url} status: {response.status}")
        #                         content_type = response.headers.get('Content-Type', '')
        #                         if content_type.startswith('text/html'):
        #                             response_text = await response.text()
        #                             logger.warning(f"Service URL returned HTML: {response_text[:200]}...")
        #                         return response.status
        #             except Exception as e:
        #                 logger.error(f"Failed to reach service_url {url}: {str(e)}", exc_info=True)
        #                 return None
 
        #         logger.info(f"Testing service_url: {service_url}")
        #         await test_service_url(service_url)
 
        #         # Serialize conversation_reference
        #         try:
        #             serialized_reference = {
        #                 "activity_id": conversation_reference.activity_id,
        #                 "user": {
        #                     "id": conversation_reference.user.id if conversation_reference.user else None,
        #                     "name": conversation_reference.user.name if conversation_reference.user else None
        #                 },
        #                 "bot": {
        #                     "id": conversation_reference.bot.id if conversation_reference.bot else None,
        #                     "name": conversation_reference.bot.name if conversation_reference.bot else None
        #                 },
        #                 "conversation": {
        #                     "id": conversation_reference.conversation.id if conversation_reference.conversation else None,
        #                     "name": conversation_reference.conversation.name if conversation_reference.conversation else None,
        #                     "is_group": conversation_reference.conversation.is_group if conversation_reference.conversation else False
        #                 },
        #                 "channel_id": conversation_reference.channel_id,
        #                 "service_url": conversation_reference.service_url
        #             }
        #             logger.info(f"Serialized conversation_reference: {json.dumps(serialized_reference)}")
                   
        #             reconstructed_reference = ConversationReference(
        #                 activity_id=serialized_reference["activity_id"],
        #                 user=ChannelAccount(id=serialized_reference["user"]["id"], name=serialized_reference["user"]["name"]),
        #                 bot=ChannelAccount(id=serialized_reference["bot"]["id"], name=serialized_reference["bot"]["name"]),
        #                 conversation=ConversationAccount(
        #                     id=serialized_reference["conversation"]["id"],
        #                     name=serialized_reference["conversation"]["name"],
        #                     is_group=serialized_reference["conversation"]["is_group"]
        #                 ),
        #                 channel_id=serialized_reference["channel_id"],
        #                 service_url=serialized_reference["service_url"]
        #             )
        #             conversation_references[activity.from_property.id] = reconstructed_reference
        #         except Exception as e:
        #             logger.error(f"Failed to serialize/reconstruct conversation_reference: {str(e)}", exc_info=True)
        #             return make_response(jsonify({
        #                 "type": "message",
        #                 "text": "Failed to process conversation reference."
        #             }), 200)
 
        #         user_id = activity.from_property.id
        #         user_message = activity.text.strip() if activity.text is not None else ""
        #         logger.info(f"user message: {user_message}")
 
        #         if not user_message:
        #             return make_response(jsonify({
        #                 "type": "message",
        #                 "text": "No question received."
        #             }), 200)


        #         async def process_and_respond():
        #             active_workspace = get_active_workspace_name()
        #             logger.info(f"Fetching workspace id: {active_workspace}")
        #             logger.info(f"Question: {user_message}, Workspace: {active_workspace}")

        #             if not active_workspace:
        #                 return jsonify({"error": "No workspace has Teams integration enabled"}), 400

        #             logger.info("Starting process_and_respond task")
        #             try:
        #                 logger.info(f"Using conversation_reference: {conversation_reference.__dict__}")
        #                 if not conversation_reference.service_url or not conversation_reference.conversation.id:
        #                     logger.error("Invalid conversation_reference: missing service_url or conversation.id")
        #                     return

        #                 sql_gen_start = time.time()
        #                 logger.info(f"Generating SQL and user messages: {user_message}")
        #                 sql = vn.generate_sql(
        #                     question=user_message,
        #                     allow_llm_to_see_data=self.allow_llm_to_see_data,
        #                     workspace=active_workspace
        #                 )
        #                 extracted_sql = vn.extract_sql(sql)
        #                 sql_source = "LLM"
        #                 logger.info(f"Generated SQL: {extracted_sql}")

        #                 reply_text = ""  # Initialize

        #                 if not vn.is_sql_valid(extracted_sql):
        #                     reply_text = "Invalid SQL generated."
        #                     logger.info("Invalid SQL detected")
        #                 else:
        #                     logger.info("Running SQL")
        #                     result_df = pd.DataFrame()  # Initialize

        #                     try:
        #                         result_df = vn.run_sql(extracted_sql)
        #                     except Exception as e:
        #                         error_message = str(e)
        #                         logger.error(f"SQL Execution Error: {error_message}", exc_info=True)

        #                         # Check for missing table or column
        #                         table_match = re.findall(r"Invalid object name '([^']+)'", error_message)
        #                         column_match = re.findall(r"Invalid column name '([^']+)'", error_message)

        #                         if table_match:
        #                             user_friendly_message = f"The query could not be executed because the table '{table_match[0]}' does not exist. Please verify the table name."
        #                         elif column_match:
        #                             user_friendly_message = f"The query could not be executed because the column '{column_match[0]}' does not exist. Please check your database schema."
        #                         else:
        #                             user_friendly_message = "The query could not be executed due to an issue with the database structure. Please verify your query and database schema."

        #                         reply_text = user_friendly_message

        #                     # Only proceed if no exception was raised
        #                     if not reply_text:
        #                         total_rows = len(result_df)
        #                         max_display_rows = 10
        #                         logger.info(f"SQL result rows: {total_rows}")

        #                         summary_text = ""
        #                         if not result_df.empty:
        #                             schema = result_df.dtypes.apply(lambda x: str(x)).to_dict()
        #                             logger.info("Generating summary")
        #                             summary_text = vn.generate_summary(
        #                                 question=user_message,
        #                                 df=result_df,
        #                                 sql=extracted_sql,
        #                                 schema=schema
        #                             )
        #                             logger.info("Summary generated")

        #                         if result_df.empty:
        #                             formatted_result = "No matching records found based on the provided criteria!"
        #                         else:
        #                             markdown_table = (
        #                                 "| " + " | ".join(result_df.columns) + " |\n" +
        #                                 "| " + " | ".join(["---"] * len(result_df.columns)) + " |\n"
        #                             )
        #                             for _, row in result_df.head(max_display_rows).iterrows():
        #                                 markdown_table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        #                             formatted_result = markdown_table

        #                         reply_text = (
        #                             f"**Query Result:**\n\n---\n\n"
        #                             f"**Question:** {user_message}\n\n---\n\n"
        #                             f"**SQL (Source: {sql_source}):** `{extracted_sql}`\n\n---\n\n"
        #                         )

        #                         if summary_text:
        #                             reply_text += f"**Summary:**\n{summary_text}\n\n---\n\n"

        #                         reply_text += formatted_result
        #                         logger.info("Reply text prepared")


             
                    
        #                 async def send_reply(turn_context: TurnContext):
        #                     logger.info("Entered send_reply")
        #                     max_retries =2
        #                     for attempt in range(1, max_retries + 1):
        #                         try:
        #                             logger.info(f"Sending activity to: {conversation_reference.service_url}/v3/conversations/{conversation_reference.conversation.id}/activities (attempt {attempt})")
        #                             logger.info(f"Message: {reply_text[:100]}...")  # Log first 100 chars
        #                             logger.info("Starting send_activity")
        #                             start_time = time.time()
        #                             response = await asyncio.wait_for(
        #                                 turn_context.send_activity(reply_text),
        #                                 timeout=900  # Increased timeout
        #                             )
        #                             logger.info(f"Send activity response: {response}")
        #                             logger.info(f"Send activity took {time.time() - start_time:.2f} seconds")
        #                             return response
        #                         except asyncio.TimeoutError:
        #                             logger.error(f"Timeout while sending activity after {time.time() - start_time:.2f} seconds (attempt {attempt})")
        #                             if attempt == max_retries:
        #                                 raise
        #                         except asyncio.CancelledError:
        #                             logger.error(f"send_activity was cancelled (attempt {attempt})")
        #                             if attempt == max_retries:
        #                                 raise
        #                         except DeserializationError as e:
        #                             logger.error(f"Deserialization error: {str(e)} (attempt {attempt})", exc_info=True)
        #                             if hasattr(e, 'response') and e.response:
        #                                 logger.error(f"Response status: {e.response.status}")
        #                                 logger.error(f"Response headers: {e.response.headers}")
        #                                 response_text = await e.response.text()
        #                                 logger.error(f"Response content: {response_text[:200]}...")
        #                             if attempt == max_retries:
        #                                 raise
        #                         except Exception as e:
        #                             logger.error(f"Exception while sending activity: {str(e)} (attempt {attempt})", exc_info=True)
        #                             if attempt == max_retries:
        #                                 raise
                                
        #                         finally:
        #                             logger.info("Exiting send_reply attempt")
 
                     
                           
        #                     # Fallback to direct HTTP POST (requires aiohttp)
        #                     if aiohttp:
        #                         logger.info("Attempting direct HTTP POST")
        #                         try:
        #                             async with aiohttp.ClientSession() as session:
        #                                 activity = {
        #                                     "type": "message",
        #                                     "text": reply_text,
        #                                     "conversation": {"id": conversation_reference.conversation.id},
        #                                     "from": {"id": conversation_reference.bot.id},
        #                                     "recipient": {"id": conversation_reference.user.id},
        #                                     "channelId": conversation_reference.channel_id
        #                                 }
        #                                 headers = {"Content-Type": "application/json"}
        #                                 async with session.post(
        #                                     f"{conversation_reference.service_url}/v3/conversations/{conversation_reference.conversation.id}/activities",
        #                                     json=activity,
        #                                     headers=headers,
        #                                     timeout=30
        #                                 ) as response:
        #                                     logger.info(f"Direct send response: {response.status}")
        #                                     logger.info(f"Direct send headers: {response.headers}")
        #                                     response_text = await response.text()
        #                                     logger.info(f"Direct send content: {response_text[:200]}...")
        #                                     if response.headers.get('Content-Type', '').startswith('text/html'):
        #                                         logger.warning("Direct send returned HTML response")
        #                                     else:
        #                                         logger.info("Direct send returned JSON response")
        #                                     return response_text
        #                         except Exception as e:
        #                             logger.error(f"Direct send failed: {str(e)}", exc_info=True)
        #                     else:
        #                         logger.error("aiohttp not installed, cannot attempt direct HTTP POST")
 
        #                 logger.info("Continuing conversation")
        #                 try:
        #                     logger.info("Starting continue_conversation")
        #                     await asyncio.wait_for(
        #                         adapter.continue_conversation(
        #                             conversation_reference,
        #                             send_reply,
        #                             bot_id=adapter_settings.app_id
        #                         ),
        #                         timeout=90  # Increased timeout
        #                     )
        #                     logger.info("Conversation continued successfully")
        #                 except asyncio.TimeoutError:
        #                     logger.error("Timeout in continue_conversation")
        #                     raise
        #                 except asyncio.CancelledError:
        #                     logger.error("continue_conversation was cancelled")
        #                     raise
        #                 except Exception as e:
        #                     logger.error(f"Error in continue_conversation: {str(e)}", exc_info=True)
        #                     raise
 
        #             except Exception as e:
        #                 logger.error(f"Error in process_and_respond: {str(e)}", exc_info=True)
        #                 reply_text = f"Error occurred: {str(e)}"
        #                 async def send_reply(turn_context: TurnContext):
        #                     logger.info("Sending error reply")
        #                     try:
        #                         await turn_context.send_activity(reply_text)
        #                     except Exception as e:
        #                         logger.error(f"Failed to send error reply: {str(e)}", exc_info=True)
        #                 try:
        #                     await adapter.continue_conversation(
        #                         conversation_reference,
        #                         send_reply,
        #                         bot_id=adapter_settings.app_id
        #                     )
        #                 except Exception as e:
        #                     logger.error(f"Failed to send error reply: {str(e)}", exc_info=True)
        #             finally:
        #                 logger.info("Finished process_and_respond task")
 
             
 
        #         # Run the async processing and monitor task
        #         task = asyncio.create_task(process_and_respond())
        #         logger.info(f"Created task: {task}")
        #         logger.info(f"Current event loop: {asyncio.get_running_loop()}")
        #         async def check_task_status():
        #             await asyncio.sleep(90)
        #             if not task.done():
        #                 logger.error(f"Task {task} is still running after 90 seconds")
        #             else:
        #                 try:
        #                     logger.info(f"Task {task} completed with result: {task.result()}")
        #                 except Exception as e:
        #                     logger.error(f"Task {task} failed with error: {str(e)}")
        #         asyncio.create_task(check_task_status())
 
        #         # Send immediate acknowledgment
        #         response = make_response(jsonify({
        #             "type": "message",
        #             "text": "Got your question. Working on it..."
        #         }), 200)
        #         logger.info(f"Response headers: {response.headers}")
        #         return response
        
        # Track sent responses to avoid duplicates
        # sent_responses = set()
        NGROK_URL = "https://knn1smh3-8084.inc1.devtunnels.ms/"
        @self.flask_app.route("/api/messages", methods=["POST"])
        async def messages():
                body = request.json
                logger.info(f"Request body: {body}")
                logger.info(f"Activity serviceUrl: {body.get('serviceUrl')}")  # Log incoming serviceUrl
                activity = Activity().deserialize(body)
                conversation_reference = TurnContext.get_conversation_reference(activity)
                logger.info(f"Raw conversation_reference: {conversation_reference.__dict__}")
       
               
 
                # Validate and fix service_url
                service_url = conversation_reference.service_url
                if not service_url or not service_url.startswith(("http://", "https://")):
                    logger.warning(f"Invalid service_url: {service_url}. Using NGROK_URL: {NGROK_URL}")
                    conversation_reference.service_url = NGROK_URL
                    service_url = NGROK_URL
 
                # Test service_url accessibility (fixed unawaited coroutine)
                async def test_service_url(url):
                    if aiohttp is None:
                        logger.warning("aiohttp not installed, skipping service_url test")
                        return None
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url, timeout=5) as response:
                                logger.info(f"Service URL {url} status: {response.status}")
                                content_type = response.headers.get('Content-Type', '')
                                if content_type.startswith('text/html'):
                                    response_text = await response.text()
                                    logger.warning(f"Service URL returned HTML: {response_text[:200]}...")
                                return response.status
                    except Exception as e:
                        logger.error(f"Failed to reach service_url {url}: {str(e)}", exc_info=True)
                        return None
 
                logger.info(f"Testing service_url: {service_url}")
                await test_service_url(service_url)
 
                # Serialize conversation_reference
                try:
                    serialized_reference = {
                        "activity_id": conversation_reference.activity_id,
                        "user": {
                            "id": conversation_reference.user.id if conversation_reference.user else None,
                            "name": conversation_reference.user.name if conversation_reference.user else None
                        },
                        "bot": {
                            "id": conversation_reference.bot.id if conversation_reference.bot else None,
                            "name": conversation_reference.bot.name if conversation_reference.bot else None
                        },
                        "conversation": {
                            "id": conversation_reference.conversation.id if conversation_reference.conversation else None,
                            "name": conversation_reference.conversation.name if conversation_reference.conversation else None,
                            "is_group": conversation_reference.conversation.is_group if conversation_reference.conversation else False
                        },
                        "channel_id": conversation_reference.channel_id,
                        "service_url": conversation_reference.service_url
                    }
                    logger.info(f"Serialized conversation_reference: {json.dumps(serialized_reference)}")
                   
                    reconstructed_reference = ConversationReference(
                        activity_id=serialized_reference["activity_id"],
                        user=ChannelAccount(id=serialized_reference["user"]["id"], name=serialized_reference["user"]["name"]),
                        bot=ChannelAccount(id=serialized_reference["bot"]["id"], name=serialized_reference["bot"]["name"]),
                        conversation=ConversationAccount(
                            id=serialized_reference["conversation"]["id"],
                            name=serialized_reference["conversation"]["name"],
                            is_group=serialized_reference["conversation"]["is_group"]
                        ),
                        channel_id=serialized_reference["channel_id"],
                        service_url=serialized_reference["service_url"]
                    )
                    conversation_references[activity.from_property.id] = reconstructed_reference
                except Exception as e:
                    logger.error(f"Failed to serialize/reconstruct conversation_reference: {str(e)}", exc_info=True)
                    return make_response(jsonify({
                        "type": "message",
                        "text": "Failed to process conversation reference."
                    }), 200)
 
                user_id = activity.from_property.id
                user_message = activity.text.strip() if activity.text is not None else ""
                logger.info(f"user message: {user_message}")
 
                if not user_message:
                    return make_response(jsonify({
                        "type": "message",
                        "text": "No question received."
                    }), 200)
                
                #  # Use conversation ID as a unique key to prevent duplicate responses
                # conversation_key = f"{conversation_reference.conversation.id}:{user_message}"
                # if conversation_key in sent_responses:
                #     logger.info(f"Response already sent for conversation_key: {conversation_key}")
                #     return make_response(jsonify({
                #         "type": "message",
                #         "text": "Response already sent."
                #     }), 200)

                async def process_and_respond():
                    active_workspace = get_active_workspace_name()
                    logger.info(f"Fetching workspace id: {active_workspace}", extra={"admin": True})
                    logger.info(f"Question: {user_message}, Workspace: {active_workspace}", extra={"admin": True})

                    if not active_workspace:
                        return jsonify({"error": "No workspace has Teams integration enabled"}), 400

                    logger.info("Starting process_and_respond task")
                    try:
                        logger.info(f"Using conversation_reference: {conversation_reference.__dict__}", extra={"admin": True})
                        if not conversation_reference.service_url or not conversation_reference.conversation.id:
                            logger.error("Invalid conversation_reference: missing service_url or conversation.id", extra={"admin": True})
                            return

                        # sql_gen_start = time.time()
                        logger.info(f"Generating SQL and user messages: {user_message}", extra={"admin": True})
                        sql = vn.generate_sql(
                            question=user_message,
                            allow_llm_to_see_data=self.allow_llm_to_see_data,
                            workspace=active_workspace
                        )
                        extracted_sql = vn.extract_sql(sql)
                        sql_source = "LLM"
                        logger.info(f"Generated SQL: {extracted_sql}", extra={"admin": True})

                        reply_text = ""  # Initialize

                        if not vn.is_sql_valid(extracted_sql):
                            reply_text = "Insufficient data."
                            logger.info("Invalid SQL detected", extra={"admin": True})
                        else:
                            logger.info("Running SQL", extra={"admin": True})
                            result_df = pd.DataFrame()  # Initialize

                            try:
                                result_df = vn.run_sql(extracted_sql)
                            except Exception as e:
                                error_message = str(e)
                                logger.error(f"SQL Execution Error: {error_message}", exc_info=True, extra={"admin": True})

                                # Check for missing table or column
                                table_match = re.findall(r"Invalid object name '([^']+)'", error_message)
                                column_match = re.findall(r"Invalid column name '([^']+)'", error_message)

                                if table_match:
                                    user_friendly_message = f"The query could not be executed because the table '{table_match[0]}' does not exist. Please verify the table name."
                                elif column_match:
                                    user_friendly_message = f"The query could not be executed because the column '{column_match[0]}' does not exist. Please check your database schema."
                                else:
                                    # Surface the actual database error instead of a generic message
                                    # that hides what really went wrong.
                                    sql_server_match = re.search(r"\[SQL Server\](.+?)(?:\s*\(\d+\)\s*\(SQL\w*\)|$)", error_message)
                                    detail = sql_server_match.group(1).strip() if sql_server_match else error_message[:300]
                                    user_friendly_message = f"The query could not be executed: {detail}"

                                reply_text = user_friendly_message

                            # Only proceed if no exception was raised
                            if not reply_text:
                                total_rows = len(result_df)
                                max_display_rows = 10
                                logger.info(f"SQL result rows: {total_rows}", extra={"admin": True})

                                summary_text = ""
                                if not result_df.empty:
                                    schema = result_df.dtypes.apply(lambda x: str(x)).to_dict()
                                    logger.info("Generating summary", extra={"admin": True})
                                    summary_text = vn.generate_summary(
                                        question=user_message,
                                        df=result_df,
                                        sql=extracted_sql,
                                        schema=schema
                                    )
                                    logger.info("Summary generated", extra={"admin": True})

                                if result_df.empty:
                                    formatted_result = "No data available for your request.!"
                                else:
                                    markdown_table = (
                                        "| " + " | ".join(result_df.columns) + " |\n" +
                                        "| " + " | ".join(["---"] * len(result_df.columns)) + " |\n"
                                    )
                                    for _, row in result_df.head(max_display_rows).iterrows():
                                        markdown_table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
                                    formatted_result = markdown_table

                                # reply_text = (
                                #     f"**Query Result:**\n\n---\n\n"
                                #     f"**Question:** {user_message}\n\n---\n\n"
                                #     f"**SQL (Source: {sql_source}):** `{extracted_sql}`\n\n---\n\n"
                                # )
                            
                               


                                if summary_text:
                                    reply_text += f"**Summary:**\n{summary_text}\n\n---\n\n"

                                reply_text += formatted_result
                                logger.info("Reply text prepared", extra={"admin": True})


                        
        
                        async def send_reply(turn_context: TurnContext):
                            logger.info("Entered send_reply", extra={"admin": True})
                            max_retries = 2
                            for attempt in range(1, max_retries + 1):
                                try:
                                    logger.info(f"Sending activity (attempt {attempt})", extra={"admin": True})
                                    start_time = time.time()
                                    response = await asyncio.wait_for(
                                        turn_context.send_activity(reply_text),
                                        timeout=90
                                    )
                                    logger.info(f"Send activity took {time.time() - start_time:.2f} seconds", extra={"admin": True})
                                    # sent_responses.add(conversation_key)  # Mark as sent
                                    return response
                                except asyncio.TimeoutError:
                                    logger.error(f"Timeout while sending activity (attempt {attempt})", extra={"admin": True})
                                    if attempt == max_retries:
                                        raise
                                except Exception as e:
                                    logger.error(f"Exception while sending activity: {str(e)} (attempt {attempt})", exc_info=True, extra={"admin": True})
                                    if attempt == max_retries:
                                        raise

                        logger.info("Starting continue_conversation")
                        await asyncio.wait_for(
                            adapter.continue_conversation(
                                conversation_reference,
                                send_reply,
                                bot_id=adapter_settings.app_id
                            ),
                            timeout=90
                        )
                        logger.info("Conversation continued successfully")

                    except Exception as e:
                        logger.error(f"Error in process_and_respond: {str(e)}", exc_info=True)
                        reply_text = f"Error occurred: {str(e)}"
                        async def send_reply(turn_context: TurnContext):
                            logger.info("Sending error reply")
                            try:
                                await turn_context.send_activity(reply_text)
                                # sent_responses.add(conversation_key)  # Mark as sent
                            except Exception as e:
                                logger.error(f"Failed to send error reply: {str(e)}", exc_info=True)
                        await adapter.continue_conversation(
                            conversation_reference,
                            send_reply,
                            bot_id=adapter_settings.app_id
                        )

                # Run the async processing
                await process_and_respond()

                # Send immediate acknowledgment
                return make_response(jsonify({
                    "type": "message",
                    "text": "Got your question. Working on it..."
                }), 200)


        # Reset Devices Agent (relocation wizard) — TX1: atomically move inventory
        # between two locations. Replaces the old free-form execute_update endpoint:
        # parameterized queries, single transaction across all three tables, auth + role gated.
        @self.flask_app.route('/api/v0/reset_wizard/relocate', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def reset_wizard_relocate(user=None):
            """Atomically relocate inventory (t_stored_item, t_hu_master, t_hu_detail)
            between two locations for the Reset Devices Agent wizard (TX1)."""
            data = request.get_json() or {}
            workspace_id = request.args.get('workspace_id') or data.get('workspace_id')
            wh_id = str(data.get('wh_id', '')).strip()
            source_location_id = str(data.get('source_location_id', '')).strip()
            dest_location_id = str(data.get('dest_location_id', '')).strip()

            logger.info(
                f"reset_wizard_relocate for workspace_id {workspace_id}: "
                f"wh_id={wh_id} {source_location_id} -> {dest_location_id}",
                extra={"admin": True},
            )

            if not workspace_id or not wh_id or not source_location_id or not dest_location_id:
                return jsonify({
                    "type": "error",
                    "error": "workspace_id, wh_id, source_location_id and dest_location_id are required."
                }), 400

            conn = None
            try:
                workspace = get_workspace_metadata(self, workspace_id)
                if not workspace:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404

                db_config = json.loads(workspace.get("db_config", "{}"))
                if not db_config:
                    return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

                conn = self.get_db_connection_from_config(db_config)
                conn.autocommit = False
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE t_stored_item SET location_id = ? WHERE location_id = ? AND wh_id = ?",
                    (dest_location_id, source_location_id, wh_id),
                )
                stored_item_rows = cursor.rowcount

                cursor.execute(
                    "UPDATE t_hu_master SET location_id = ? WHERE location_id = ? AND wh_id = ?",
                    (dest_location_id, source_location_id, wh_id),
                )
                hu_master_rows = cursor.rowcount

                cursor.execute(
                    "UPDATE t_hu_detail SET location_id = ? WHERE location_id = ? AND wh_id = ?",
                    (dest_location_id, source_location_id, wh_id),
                )
                hu_detail_rows = cursor.rowcount

                conn.commit()
                cursor.close()

                user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
                logger.info(
                    f"reset_wizard_relocate committed. workspace={workspace_id} user={user_id} "
                    f"rows: t_stored_item={stored_item_rows} t_hu_master={hu_master_rows} t_hu_detail={hu_detail_rows}",
                    extra={"admin": True},
                )

                return jsonify({
                    "type": "success",
                    "message": "Relocation completed successfully",
                    "rows": {
                        "t_stored_item": stored_item_rows,
                        "t_hu_master": hu_master_rows,
                        "t_hu_detail": hu_detail_rows,
                    },
                })

            except Exception as e:
                logger.error(f"reset_wizard_relocate failed: {str(e)}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                return jsonify({
                    "type": "error",
                    "error": str(e),
                    "message": f"Relocation failed: {str(e)}",
                }), 200  # 200 so the frontend can handle the error payload gracefully

            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        # Reset Devices Agent (relocation wizard) — TX2: atomically clear an employee's
        # device assignment and reset their fork location status.
        @self.flask_app.route('/api/v0/reset_wizard/logout_clear', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def reset_wizard_logout_clear(user=None):
            """Atomically clear employee device + reset fork location status (TX2)."""
            data = request.get_json() or {}
            workspace_id = request.args.get('workspace_id') or data.get('workspace_id')
            wh_id = str(data.get('wh_id', '')).strip()
            employee_id = str(data.get('employee_id', '')).strip()
            location_id = str(data.get('location_id', '')).strip()

            logger.info(
                f"reset_wizard_logout_clear for workspace_id {workspace_id}: "
                f"wh_id={wh_id} employee_id={employee_id} location_id={location_id}",
                extra={"admin": True},
            )

            if not workspace_id or not wh_id or not employee_id or not location_id:
                return jsonify({
                    "type": "error",
                    "error": "workspace_id, wh_id, employee_id and location_id are required."
                }), 400

            conn = None
            try:
                workspace = get_workspace_metadata(self, workspace_id)
                if not workspace:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404

                db_config = json.loads(workspace.get("db_config", "{}"))
                if not db_config:
                    return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

                conn = self.get_db_connection_from_config(db_config)
                conn.autocommit = False
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE t_employee SET device = NULL WHERE id = ? AND wh_id = ?",
                    (employee_id, wh_id),
                )
                employee_rows = cursor.rowcount

                cursor.execute(
                    "UPDATE t_location SET c1 = NULL, status = 'E' WHERE location_id = ? AND wh_id = ?",
                    (location_id, wh_id),
                )
                location_rows = cursor.rowcount

                conn.commit()
                cursor.close()

                user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
                logger.info(
                    f"reset_wizard_logout_clear committed. workspace={workspace_id} user={user_id} "
                    f"rows: t_employee={employee_rows} t_location={location_rows}",
                    extra={"admin": True},
                )

                return jsonify({
                    "type": "success",
                    "message": "Logout and clear completed successfully",
                    "rows": {"t_employee": employee_rows, "t_location": location_rows},
                })

            except Exception as e:
                logger.error(f"reset_wizard_logout_clear failed: {str(e)}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                return jsonify({
                    "type": "error",
                    "error": str(e),
                    "message": f"Logout/clear failed: {str(e)}",
                }), 200

            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        @self.flask_app.route('/api/v0/device_reset_logs', methods=['GET'])
        @self.requires_auth
        def device_reset_logs(user=None):
            """Return the in-memory automated device reset log buffer as JSON."""
            with _stuck_device_log_lock:
                entries = list(_stuck_device_log)
            return jsonify({"logs": entries})

        @self.flask_app.route('/api/v0/device_reset_logs/download', methods=['GET'])
        @self.requires_auth
        def device_reset_logs_download(user=None):
            """Download the automated device reset logs as CSV or plain text."""
            fmt = request.args.get('format', 'csv').lower()
            with _stuck_device_log_lock:
                entries = list(_stuck_device_log)

            if fmt == 'txt':
                lines = [
                    "Automated Device Reset Logs",
                    "=" * 70,
                    f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    f"Total entries: {len(entries)}",
                    "",
                ]
                current_run = None
                for e in entries:
                    if e["run_id"] != current_run:
                        current_run = e["run_id"]
                        lines.append("")
                        lines.append(f"Run: {current_run}")
                        lines.append("-" * 50)
                    device_part = f"  Device: {e['device_id']}  |  " if e["device_id"] else "  "
                    lines.append(f"  [{e['timestamp']}]  {e['level']:<9}{device_part}{e['message']}")
                lines.append("")
                content = "\n".join(lines)
                return Response(
                    content,
                    mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=device_reset_logs.txt"},
                )
            else:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Run ID", "Timestamp", "Level", "Device ID", "Message"])
                for e in entries:
                    writer.writerow([e["run_id"], e["timestamp"], e["level"], e["device_id"], e["message"]])
                return Response(
                    output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=device_reset_logs.csv"},
                )


        # ============================================================
        # SCHEDULER CONTROL ROUTES — Device Reset Agent
        # ============================================================

        def _scheduler_job_info(scheduler, job_id):
            """Return a dict with running/paused/next_run/interval_hours for a job."""
            if scheduler is None or not scheduler.running:
                return {"running": False, "paused": True, "next_run": None, "interval_hours": 2}
            job = scheduler.get_job(job_id)
            if not job:
                return {"running": scheduler.running, "paused": True, "next_run": None, "interval_hours": 2}
            paused = job.next_run_time is None
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
            try:
                interval_hours = job.trigger.interval.total_seconds() / 3600
            except AttributeError:
                interval_hours = 2
            return {"running": scheduler.running, "paused": paused, "next_run": next_run, "interval_hours": interval_hours}

        @self.flask_app.route('/api/v0/device_reset_agent/scheduler_status', methods=['GET'])
        @self.requires_auth
        def device_reset_scheduler_status(user=None):
            return jsonify(_scheduler_job_info(_stuck_device_scheduler, "identify_stuck_device"))

        @self.flask_app.route('/api/v0/device_reset_agent/scheduler_toggle', methods=['POST'])
        @self.requires_auth
        def device_reset_scheduler_toggle(user=None):
            if _stuck_device_scheduler is None:
                return jsonify({"type": "error", "error": "Scheduler not initialized"}), 400
            job = _stuck_device_scheduler.get_job("identify_stuck_device")
            if not job:
                return jsonify({"type": "error", "error": "Job not found"}), 400
            if job.next_run_time is None:
                _stuck_device_scheduler.resume_job("identify_stuck_device")
                action = "resumed"
            else:
                _stuck_device_scheduler.pause_job("identify_stuck_device")
                action = "paused"
            return jsonify({"type": "success", "action": action})

        @self.flask_app.route('/api/v0/device_reset_agent/scheduler_interval', methods=['POST'])
        @self.requires_auth
        def device_reset_scheduler_interval(user=None):
            if _stuck_device_scheduler is None:
                return jsonify({"type": "error", "error": "Scheduler not initialized"}), 400
            data = request.get_json()
            try:
                hours = float(data.get('hours', 0))
                if hours < 0.25 or hours > 168:
                    raise ValueError()
            except (TypeError, ValueError, AttributeError):
                return jsonify({"type": "error", "error": "hours must be a number between 0.25 and 168"}), 400
            _stuck_device_scheduler.reschedule_job("identify_stuck_device", trigger='interval', hours=hours)
            return jsonify({"type": "success", "hours": hours})

        # ============================================================
        # SCHEDULER CONTROL ROUTES — Unpick Agent
        # ============================================================

        @self.flask_app.route('/api/v0/unpick_agent/scheduler_status', methods=['GET'])
        @self.requires_auth
        def unpick_scheduler_status(user=None):
            return jsonify(_scheduler_job_info(_auto_unpick_scheduler, "auto_unpick"))

        @self.flask_app.route('/api/v0/unpick_agent/scheduler_toggle', methods=['POST'])
        @self.requires_auth
        def unpick_scheduler_toggle(user=None):
            if _auto_unpick_scheduler is None:
                return jsonify({"type": "error", "error": "Scheduler not initialized"}), 400
            job = _auto_unpick_scheduler.get_job("auto_unpick")
            if not job:
                return jsonify({"type": "error", "error": "Job not found"}), 400
            if job.next_run_time is None:
                _auto_unpick_scheduler.resume_job("auto_unpick")
                action = "resumed"
            else:
                _auto_unpick_scheduler.pause_job("auto_unpick")
                action = "paused"
            return jsonify({"type": "success", "action": action})

        @self.flask_app.route('/api/v0/unpick_agent/scheduler_interval', methods=['POST'])
        @self.requires_auth
        def unpick_scheduler_interval(user=None):
            if _auto_unpick_scheduler is None:
                return jsonify({"type": "error", "error": "Scheduler not initialized"}), 400
            data = request.get_json()
            try:
                hours = float(data.get('hours', 0))
                if hours < 0.25 or hours > 168:
                    raise ValueError()
            except (TypeError, ValueError, AttributeError):
                return jsonify({"type": "error", "error": "hours must be a number between 0.25 and 168"}), 400
            _auto_unpick_scheduler.reschedule_job("auto_unpick", trigger='interval', hours=hours)
            return jsonify({"type": "success", "hours": hours})

        # ============================================================
        # UNPICK AGENT ROUTES
        # ============================================================

        @self.flask_app.route('/api/v0/unpick_agent/auto_scan', methods=['POST'])
        @self.requires_auth
        def unpick_agent_auto_scan(user=None):
            """Run the automatic detection query to find pick records that need to be reverted."""
            data = request.get_json()
            workspace_id = data.get('workspace_id') if data else None
            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found"}), 404

            db_config = json.loads(workspace.get("db_config", "{}"))
            if not db_config:
                return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

            AUTO_SCAN_SQL = """
            SELECT DISTINCT
                  TL.control_number AS order_number
                , TL.wh_id
                , TL.item_number
            FROM t_tran_log TL WITH(NOLOCK)

            LEFT JOIN t_pick_detail PD
                ON PD.order_number = TL.control_number
                AND PD.wh_id = TL.wh_id
                AND PD.item_number = TL.item_number
                AND PD.line_number = TL.line_number

            LEFT JOIN t_stored_item SI
                ON SI.wh_id = TL.wh_id
                AND SI.item_number = TL.item_number
                AND SI.type = TL.control_number

            LEFT JOIN t_hu_master HM
                ON HM.wh_id = TL.wh_id
                AND HM.hu_id = TL.hu_id

            LEFT JOIN t_hu_detail HD
                ON HD.wh_id = TL.wh_id
                AND HD.hu_id = TL.hu_id
                AND HD.item_number = TL.item_number

            LEFT JOIN t_work_q WQ
                ON WQ.wh_id = TL.wh_id
                AND WQ.pick_ref_number = TL.control_number
                AND WQ.item_number = TL.item_number

            WHERE TL.tran_type = '391'
            AND TL.description = 'Unload/Unpick (pick)'

            AND NOT EXISTS (
                SELECT 1
                FROM t_tran_log TL2
                WHERE TL2.control_number = TL.control_number
                AND TL2.wh_id = TL.wh_id
                AND TL2.item_number = TL.item_number
                AND TL2.tran_type = '301'
                AND TL2.description = 'Picking (pick)'
                AND (
                    CAST(TL2.start_tran_date AS DATETIME) + CAST(TL2.start_tran_time AS DATETIME)
                    > CAST(TL.start_tran_date AS DATETIME) + CAST(TL.start_tran_time AS DATETIME)
                )
            )

            AND (
                ISNULL(PD.picked_quantity, 0) <> 0
                OR ISNULL(PD.staged_quantity, 0) <> 0
                OR PD.status <> 'RELEASED'
                OR SI.type <> 'STORAGE'
                OR SI.location_id <> (
                    SELECT TOP 1 TL_PICK.location_id
                    FROM t_tran_log TL_PICK
                    WHERE TL_PICK.control_number = TL.control_number
                    AND TL_PICK.wh_id = TL.wh_id
                    AND TL_PICK.item_number = TL.item_number
                    AND TL_PICK.tran_type = '301'
                    ORDER BY TL_PICK.start_tran_date DESC, TL_PICK.start_tran_time DESC
                )
                OR HM.control_number IS NOT NULL
                OR HM.type <> 'IV'
                OR HD.storage_type IS NOT NULL
                OR WQ.work_status <> 'U'
            )
            """

            conn = None
            try:
                conn = self.get_db_connection_from_config(db_config)
                cursor = conn.cursor()
                cursor.execute(AUTO_SCAN_SQL)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                logger.info(f"Unpick auto-scan returned {len(rows)} record(s)", extra={"admin": True})
                return jsonify({"type": "success", "records": rows, "count": len(rows)})
            except Exception as e:
                logger.error(f"Unpick auto-scan failed: {e}", exc_info=True)
                return jsonify({"type": "error", "error": str(e)}), 200
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass


        @self.flask_app.route('/api/v0/unpick_agent/execute', methods=['POST'])
        @self.requires_auth
        def unpick_agent_execute(user=None):
            """Execute the 3-step unpick for a list of (wh_id, order_number, item_number) records.
            Each record is processed in its own atomic transaction — failure rolls back only that record."""
            global _current_unpick_run_id

            data = request.get_json()
            workspace_id = data.get('workspace_id') if data else None
            records = data.get('records', []) if data else []

            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400
            if not records:
                return jsonify({"type": "error", "error": "No records provided"}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found"}), 404

            db_config = json.loads(workspace.get("db_config", "{}"))
            if not db_config:
                return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

            run_id = _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            _current_unpick_run_id = run_id
            _log_unpick("INFO", f"Unpick agent run started. Processing {len(records)} record(s).", run_id=run_id)

            results = []

            for rec in records:
                wh_id        = str(rec.get('wh_id', '')).strip()
                order_number = str(rec.get('order_number', '')).strip()
                item_number  = str(rec.get('item_number', '')).strip()

                if not wh_id or not order_number or not item_number:
                    msg = f"Skipped — missing required field(s). wh_id='{wh_id}' order_number='{order_number}' item_number='{item_number}'"
                    _log_unpick("WARNING", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    results.append({"wh_id": wh_id, "order_number": order_number, "item_number": item_number, "status": "WARNING", "message": msg})
                    continue

                _log_unpick("INFO", "Processing started.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                conn = None
                try:
                    conn = self.get_db_connection_from_config(db_config)
                    conn.autocommit = False
                    cursor = conn.cursor()

                    # ── Resolve pick_location (column-existence check + tran_log fallback) ──
                    cursor.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('t_pick_detail') AND name = 'pick_location'")
                    col_chk = cursor.fetchone()
                    pick_location = None
                    if col_chk:
                        _log_unpick("INFO", "pick_location column EXISTS in t_pick_detail — reading value.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        cursor.execute("SELECT pick_location FROM t_pick_detail WHERE wh_id = ? AND order_number = ? AND item_number = ?", (wh_id, order_number, item_number))
                        row = cursor.fetchone()
                        if not row:
                            _log_unpick("WARNING", "No t_pick_detail row found for this wh_id/order/item — falling back to t_tran_log.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        else:
                            pick_location = row[0]
                            _log_unpick("INFO", f"t_pick_detail.pick_location = {repr(pick_location)}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        if not pick_location:
                            cursor.execute("SELECT TOP 1 location_id FROM t_tran_log WHERE wh_id = ? AND tran_type = '301' AND item_number = ? AND control_number = ? ORDER BY start_tran_date DESC, start_tran_time DESC", (wh_id, item_number, order_number))
                            row2 = cursor.fetchone()
                            pick_location = row2[0] if row2 else None
                            _log_unpick("INFO", f"t_tran_log (tran_type=301) fallback → location_id = {repr(pick_location)}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    else:
                        _log_unpick("INFO", "pick_location column NOT found in t_pick_detail — using t_tran_log.source_location_id.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        cursor.execute("SELECT TOP 1 source_location_id FROM t_tran_log WHERE wh_id = ? AND tran_type = '301' AND item_number = ? AND control_number = ? ORDER BY start_tran_date DESC, start_tran_time DESC", (wh_id, item_number, order_number))
                        row = cursor.fetchone()
                        pick_location = row[0] if row else None
                        _log_unpick("INFO", f"t_tran_log.source_location_id = {repr(pick_location)}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    if not pick_location:
                        # Show how many tran_log rows exist for this record to help diagnose
                        cursor.execute("SELECT COUNT(*) FROM t_tran_log WHERE wh_id = ? AND item_number = ? AND control_number = ?", (wh_id, item_number, order_number))
                        tl_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM t_tran_log WHERE wh_id = ? AND item_number = ? AND control_number = ? AND tran_type = '301'", (wh_id, item_number, order_number))
                        tl_301_count = cursor.fetchone()[0]
                        msg = (f"Could not resolve pick_location — skipping. "
                               f"[t_tran_log rows for this order/item: {tl_count} total, {tl_301_count} with tran_type=301]")
                        _log_unpick("WARNING", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        results.append({"wh_id": wh_id, "order_number": order_number, "item_number": item_number, "status": "WARNING", "message": msg})
                        cursor.close(); conn.rollback(); conn.close()
                        continue
                    _log_unpick("INFO", f"pick_location resolved = {pick_location}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    # ── Step 1: Full unstage — set quantities to zero ──────────────
                    cursor.execute("""
                        UPDATE t_pick_detail
                        SET staged_quantity = 0, picked_quantity = 0, status = 'RELEASED'
                        WHERE wh_id = ? AND order_number = ? AND item_number = ?
                    """, (wh_id, order_number, item_number))
                    _log_unpick("INFO", f"Step 1: t_pick_detail fully unstaged. Rows: {cursor.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    # ── Step 2: Location type + inventory revert ───────────────────
                    cursor.execute("SELECT item_hu_indicator FROM t_location WHERE wh_id = ? AND location_id = ?", (wh_id, pick_location))
                    row = cursor.fetchone()
                    item_hu_indicator = row[0] if row else None
                    _log_unpick("INFO", f"Step 2: item_hu_indicator = '{item_hu_indicator}'.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    def _restore_si_full_cursor(case_label):
                        cursor.execute("SELECT 1 FROM t_stored_item WHERE wh_id = ? AND item_number = ? AND type = 'STORAGE' AND location_id = ?", (wh_id, item_number, pick_location))
                        if cursor.fetchone():
                            cursor.execute("""
                                UPDATE S SET S.actual_qty = S.actual_qty + O.actual_qty
                                FROM t_stored_item S
                                JOIN t_stored_item O ON O.wh_id = S.wh_id AND O.item_number = S.item_number
                                WHERE S.wh_id = ? AND S.item_number = ? AND S.type = 'STORAGE'
                                  AND S.location_id = ? AND O.type = ?
                            """, (wh_id, item_number, pick_location, order_number))
                            cursor.execute("DELETE FROM t_stored_item WHERE wh_id = ? AND item_number = ? AND type = ?", (wh_id, item_number, order_number))
                            _log_unpick("INFO", f"Step 2 ({case_label}): Merged qty into STORAGE and deleted order-type row.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        else:
                            cursor.execute("UPDATE t_stored_item SET type = 'STORAGE', location_id = ? WHERE wh_id = ? AND item_number = ? AND type = ?", (pick_location, wh_id, item_number, order_number))
                            _log_unpick("INFO", f"Step 2 ({case_label}): Renamed order-type row to STORAGE.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    if item_hu_indicator == 'I':
                        cursor.execute("SELECT TOP 1 hu_id FROM t_hu_detail WHERE wh_id = ? AND item_number = ? AND storage_type = ?", (wh_id, item_number, order_number))
                        row = cursor.fetchone()
                        picked_hu_id = row[0] if row else None
                        _restore_si_full_cursor("Case I")
                        if picked_hu_id:
                            cursor.execute("DELETE FROM t_hu_detail WHERE wh_id = ? AND hu_id = ? AND item_number = ? AND storage_type = ?", (wh_id, picked_hu_id, item_number, order_number))
                            cursor.execute("SELECT 1 FROM t_hu_detail WHERE wh_id = ? AND hu_id = ?", (wh_id, picked_hu_id))
                            if not cursor.fetchone():
                                cursor.execute("DELETE FROM t_hu_master WHERE wh_id = ? AND hu_id = ?", (wh_id, picked_hu_id))
                        _log_unpick("INFO", "Step 2 (Case I): Item-controlled location updates done.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    elif item_hu_indicator == 'H':
                        cursor.execute("SELECT TOP 1 hu_id FROM t_hu_detail WHERE wh_id = ? AND item_number = ? AND storage_type = ?", (wh_id, item_number, order_number))
                        row = cursor.fetchone()
                        picked_hu_id = row[0] if row else None
                        if picked_hu_id:
                            cursor.execute("SELECT COUNT(DISTINCT item_number) FROM t_hu_detail WHERE wh_id = ? AND hu_id = ?", (wh_id, picked_hu_id))
                            item_count = cursor.fetchone()[0]
                            if item_count == 1:
                                cursor.execute("DELETE FROM t_hu_detail WHERE wh_id = ? AND hu_id = ? AND item_number = ? AND storage_type = ?", (wh_id, picked_hu_id, item_number, order_number))
                                cursor.execute("SELECT 1 FROM t_hu_detail WHERE wh_id = ? AND hu_id = ?", (wh_id, picked_hu_id))
                                if not cursor.fetchone():
                                    cursor.execute("DELETE FROM t_hu_master WHERE wh_id = ? AND hu_id = ?", (wh_id, picked_hu_id))
                                _restore_si_full_cursor("Case 2A")
                                _log_unpick("INFO", "Step 2 (Case 2A): Single-item LP updates done.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                            else:
                                cursor.execute("SELECT 'UP' + RIGHT('00000000' + CAST(ABS(CHECKSUM(NEWID())) % 100000000 AS VARCHAR), 8)")
                                new_hu_id = cursor.fetchone()[0]
                                cursor.execute("INSERT INTO t_hu_master (hu_id, type, control_number, location_id, status, wh_id) VALUES (?, 'LP', NULL, ?, 'A', ?)", (new_hu_id, pick_location, wh_id))
                                cursor.execute("UPDATE t_hu_detail SET hu_id = ?, location_id = ?, storage_type = NULL WHERE wh_id = ? AND hu_id = ? AND item_number = ?", (new_hu_id, pick_location, wh_id, picked_hu_id, item_number))
                                _restore_si_full_cursor("Case 2B")
                                _log_unpick("INFO", f"Step 2 (Case 2B): Multi-item LP split to new HU {new_hu_id}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                        else:
                            _log_unpick("WARNING", "Step 2 (Case H): No HU detail found — skipping HU updates.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                            _restore_si_full_cursor("Case H/no HU")
                    else:
                        _log_unpick("WARNING", f"Step 2: Unknown item_hu_indicator='{item_hu_indicator}' — skipping HU updates.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    # ── Step 3: Release work queue (full unpick → always 'U') ──────
                    cursor.execute("""
                        UPDATE t_work_q SET work_status = 'U'
                        WHERE wh_id = ? AND pick_ref_number = ?
                        AND work_q_id IN (
                            SELECT work_q_id FROM t_pick_detail
                            WHERE order_number = ? AND wh_id = ? AND item_number = ?
                        )
                    """, (wh_id, order_number, order_number, wh_id, item_number))
                    _log_unpick("INFO", f"Step 3: t_work_q updated. Rows: {cursor.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                    conn.commit()
                    cursor.close()
                    _log_unpick("INFO", "All steps completed successfully. Transaction committed.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    results.append({"wh_id": wh_id, "order_number": order_number, "item_number": item_number, "status": "SUCCESS", "message": "Unpick completed successfully."})

                except Exception as exc:
                    if conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    msg = f"All changes rolled back. Error: {exc}"
                    logger.exception("Unpick agent failed for order=%s item=%s wh=%s: %s", order_number, item_number, wh_id, exc)
                    _log_unpick("ERROR", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    results.append({"wh_id": wh_id, "order_number": order_number, "item_number": item_number, "status": "ERROR", "message": msg})

                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass

            _log_unpick("INFO", f"Unpick agent run completed. {len(results)} record(s) processed.", run_id=run_id)
            return jsonify({"type": "success", "results": results, "run_id": run_id})


        @self.flask_app.route('/api/v0/unpick_agent/partial_unpick', methods=['POST'])
        @self.requires_auth
        def unpick_agent_partial_unpick(user=None):
            """Scenario 3 — partial unpick by user-supplied quantity.
            Inputs: workspace_id, wh_id, order_number, item_number, unpick_qty."""
            global _current_unpick_run_id
            data = request.get_json()
            workspace_id = data.get('workspace_id') if data else None
            wh_id        = str(data.get('wh_id', '')).strip() if data else ''
            order_number = str(data.get('order_number', '')).strip() if data else ''
            item_number  = str(data.get('item_number', '')).strip() if data else ''
            unpick_qty_raw = data.get('unpick_qty') if data else None

            # Validate
            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400
            if not wh_id or not order_number or not item_number:
                return jsonify({"type": "error", "error": "wh_id, order_number, and item_number are required"}), 400
            try:
                unpick_qty = float(unpick_qty_raw)
                if unpick_qty <= 0:
                    raise ValueError()
            except (TypeError, ValueError):
                return jsonify({"type": "error", "error": "unpick_qty must be a positive number"}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found"}), 404
            db_config = json.loads(workspace.get("db_config", "{}"))
            if not db_config:
                return jsonify({"type": "error", "error": "Database configuration not found for workspace"}), 400

            run_id = _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            _current_unpick_run_id = run_id
            _log_unpick("INFO", f"Partial unpick started. qty={unpick_qty}", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

            conn = None
            try:
                conn = self.get_db_connection_from_config(db_config)
                conn.autocommit = False
                cursor = conn.cursor()

                # Stage 0: Validate unpick_qty against current picked_quantity
                cursor.execute("SELECT picked_quantity FROM t_pick_detail WHERE wh_id = ? AND order_number = ? AND item_number = ?", (wh_id, order_number, item_number))
                qty_row = cursor.fetchone()
                if not qty_row or not qty_row[0] or float(qty_row[0]) <= 0:
                    msg = "Stage 0: picked_quantity is 0 or NULL — nothing to unpick."
                    _log_unpick("WARNING", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    cursor.close(); conn.rollback(); conn.close()
                    return jsonify({"type": "warning", "message": msg})
                if unpick_qty > float(qty_row[0]):
                    msg = f"Stage 0: unpick_qty ({unpick_qty}) exceeds picked_quantity ({qty_row[0]})."
                    _log_unpick("WARNING", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    cursor.close(); conn.rollback(); conn.close()
                    return jsonify({"type": "warning", "message": msg})
                _log_unpick("INFO", f"Stage 0: validated unpick_qty={unpick_qty}, picked_qty={qty_row[0]}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                # Resolve pick_location
                cursor.execute("SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('t_pick_detail') AND name = 'pick_location'")
                col_chk = cursor.fetchone()
                if col_chk:
                    cursor.execute("SELECT pick_location FROM t_pick_detail WHERE wh_id = ? AND order_number = ? AND item_number = ?", (wh_id, order_number, item_number))
                    row = cursor.fetchone()
                    pick_location = row[0] if row else None
                    if not pick_location:
                        cursor.execute("SELECT TOP 1 location_id FROM t_tran_log WHERE wh_id = ? AND tran_type = '301' AND item_number = ? AND control_number = ? ORDER BY start_tran_date DESC, start_tran_time DESC", (wh_id, item_number, order_number))
                        row2 = cursor.fetchone()
                        pick_location = row2[0] if row2 else None
                else:
                    cursor.execute("SELECT TOP 1 source_location_id FROM t_tran_log WHERE wh_id = ? AND tran_type = '301' AND item_number = ? AND control_number = ? ORDER BY start_tran_date DESC, start_tran_time DESC", (wh_id, item_number, order_number))
                    row = cursor.fetchone()
                    pick_location = row[0] if row else None
                if not pick_location:
                    msg = "Could not resolve pick_location — skipping."
                    _log_unpick("WARNING", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                    cursor.close(); conn.rollback(); conn.close()
                    return jsonify({"type": "warning", "message": msg})

                # Step 1: Reduce by unpick_qty
                cursor.execute("""
                    UPDATE t_pick_detail
                    SET staged_quantity = CASE WHEN staged_quantity >= ? THEN staged_quantity - ? ELSE 0 END,
                        picked_quantity = picked_quantity - ?,
                        status = CASE WHEN picked_quantity - ? > 0 THEN 'PICKED' ELSE 'RELEASED' END
                    WHERE wh_id = ? AND order_number = ? AND item_number = ?
                """, (unpick_qty, unpick_qty, unpick_qty, unpick_qty, wh_id, order_number, item_number))
                _log_unpick("INFO", f"Step 1: t_pick_detail reduced by {unpick_qty}. Rows: {cursor.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                # Step 2: Location type + partial inventory revert
                cursor.execute("SELECT item_hu_indicator FROM t_location WHERE wh_id = ? AND location_id = ?", (wh_id, pick_location))
                row = cursor.fetchone()
                item_hu_indicator = row[0] if row else None
                _log_unpick("INFO", f"Step 2: item_hu_indicator = '{item_hu_indicator}'.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                def _partial_restore_si(case_label):
                    cursor.execute("SELECT 1 FROM t_stored_item WHERE wh_id = ? AND item_number = ? AND type = 'STORAGE' AND location_id = ?", (wh_id, item_number, pick_location))
                    if cursor.fetchone():
                        cursor.execute("UPDATE t_stored_item SET actual_qty = actual_qty + ? WHERE wh_id = ? AND item_number = ? AND type = 'STORAGE' AND location_id = ?", (unpick_qty, wh_id, item_number, pick_location))
                    else:
                        cursor.execute("UPDATE t_stored_item SET type = 'STORAGE', location_id = ?, actual_qty = ? WHERE wh_id = ? AND item_number = ? AND type = ?", (pick_location, unpick_qty, wh_id, item_number, order_number))
                    cursor.execute("UPDATE t_stored_item SET actual_qty = actual_qty - ? WHERE wh_id = ? AND item_number = ? AND type = ?", (unpick_qty, wh_id, item_number, order_number))
                    cursor.execute("DELETE FROM t_stored_item WHERE wh_id = ? AND item_number = ? AND type = ? AND actual_qty <= 0", (wh_id, item_number, order_number))
                    _log_unpick("INFO", f"Step 2 ({case_label}): t_stored_item partially reverted.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                def _partial_cleanup_hu(hu_id_val):
                    cursor.execute("UPDATE t_hu_detail SET actual_qty = actual_qty - ? WHERE wh_id = ? AND hu_id = ? AND item_number = ? AND storage_type = ?", (unpick_qty, wh_id, hu_id_val, item_number, order_number))
                    cursor.execute("DELETE FROM t_hu_detail WHERE wh_id = ? AND hu_id = ? AND item_number = ? AND storage_type = ? AND actual_qty <= 0", (wh_id, hu_id_val, item_number, order_number))
                    cursor.execute("SELECT 1 FROM t_hu_detail WHERE wh_id = ? AND hu_id = ?", (wh_id, hu_id_val))
                    if not cursor.fetchone():
                        cursor.execute("DELETE FROM t_hu_master WHERE wh_id = ? AND hu_id = ?", (wh_id, hu_id_val))
                        _log_unpick("INFO", "Step 2: t_hu_master deleted (HU now empty).", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                if item_hu_indicator in ('I', 'H'):
                    cursor.execute("SELECT TOP 1 hu_id FROM t_hu_detail WHERE wh_id = ? AND item_number = ? AND storage_type = ?", (wh_id, item_number, order_number))
                    row = cursor.fetchone()
                    picked_hu_id = row[0] if row else None
                    _partial_restore_si(f"Case {item_hu_indicator}")
                    if picked_hu_id:
                        _partial_cleanup_hu(picked_hu_id)
                    _log_unpick("INFO", f"Step 2 (Case {item_hu_indicator}): Partial inventory revert done.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                else:
                    _log_unpick("WARNING", f"Step 2: Unknown item_hu_indicator='{item_hu_indicator}' — skipping HU updates.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                # Step 3: Conditional work queue (C if still fully picked, else U)
                cursor.execute("""
                    UPDATE t_work_q
                    SET work_status = CASE
                        WHEN EXISTS (SELECT 1 FROM t_pick_detail pd WHERE pd.work_q_id = t_work_q.work_q_id AND pd.picked_quantity >= pd.planned_quantity)
                        THEN 'C' ELSE 'U' END
                    WHERE wh_id = ? AND pick_ref_number = ?
                    AND work_q_id IN (SELECT work_q_id FROM t_pick_detail WHERE order_number = ? AND wh_id = ? AND item_number = ?)
                """, (wh_id, order_number, order_number, wh_id, item_number))
                _log_unpick("INFO", f"Step 3: t_work_q updated. Rows: {cursor.rowcount}.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)

                conn.commit()
                cursor.close()
                _log_unpick("INFO", "Partial unpick committed.", order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                return jsonify({"type": "success", "message": f"Partial unpick of {unpick_qty} unit(s) completed.", "run_id": run_id})

            except Exception as exc:
                if conn:
                    try: conn.rollback()
                    except Exception: pass
                msg = f"All changes rolled back. Error: {exc}"
                logger.exception("Partial unpick failed: %s", exc)
                _log_unpick("ERROR", msg, order_number=order_number, item_number=item_number, wh_id=wh_id, run_id=run_id)
                return jsonify({"type": "error", "message": msg}), 500
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass


        @self.flask_app.route('/api/v0/unpick_agent/logs', methods=['GET'])
        @self.requires_auth
        def unpick_agent_logs(user=None):
            """Return the in-memory unpick agent log buffer as JSON."""
            with _unpick_log_lock:
                entries = list(_unpick_log)
            return jsonify({"logs": entries})


        @self.flask_app.route('/api/v0/unpick_agent/logs/download', methods=['GET'])
        @self.requires_auth
        def unpick_agent_logs_download(user=None):
            """Download the unpick agent logs as CSV or plain text."""
            fmt = request.args.get('format', 'csv').lower()
            with _unpick_log_lock:
                entries = list(_unpick_log)

            if fmt == 'txt':
                lines = [
                    "Unpick Agent Logs",
                    "=" * 70,
                    f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    f"Total entries: {len(entries)}",
                    "",
                ]
                current_run = None
                for e in entries:
                    if e["run_id"] != current_run:
                        current_run = e["run_id"]
                        lines.append("")
                        lines.append(f"Run: {current_run}")
                        lines.append("-" * 50)
                    record_part = f"  [{e['wh_id']}] {e['order_number']} / {e['item_number']}  |  " if e.get("order_number") else "  "
                    lines.append(f"  [{e['timestamp']}]  {e['level']:<9}{record_part}{e['message']}")
                lines.append("")
                content = "\n".join(lines)
                return Response(
                    content,
                    mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=unpick_agent_logs.txt"},
                )
            else:
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Run ID", "Timestamp", "Level", "WH ID", "Order Number", "Item Number", "Message"])
                for e in entries:
                    writer.writerow([e["run_id"], e["timestamp"], e["level"], e["wh_id"], e["order_number"], e["item_number"], e["message"]])
                return Response(
                    output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=unpick_agent_logs.csv"},
                )


    def get_db_connection_from_config(self, db_config):
        """Create a direct database connection from workspace db_config"""
        server = db_config.get('serverName')
        port = db_config.get('port')
        database = db_config.get('databaseName')
        username = db_config.get('username')
        password = db_config.get('password')

        # Build connection string
        if port:
            conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}'
        else:
            conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

        logger.info(f"Creating DB connection to {database}")
        return pyodbc.connect(conn_str)


    def _df_to_parquet_bytes(self, df: pd.DataFrame, compression: str = "snappy", preserve_index: bool = False) -> bytes:
        logger.info(f"_df_to_paraquet_bytes", extra={"flow":True})
        """
        Fast serialize DataFrame to parquet bytes using pyarrow.
        preserve_index=False by default for smaller output and speed.
        """
        table = pa.Table.from_pandas(df, preserve_index=preserve_index)
        out = io.BytesIO()
        pq.write_table(table, out, compression=compression)
        return out.getvalue()
                
    def _apply_ai_options_to_config(self, workspace_id, ai_options: dict):
        """
        Dynamically apply workspace-level AI options to the app config.
        This ensures that when toggles are updated, they take effect immediately.
        """
        try:
            # Apply to global config (for currently active workspace)
            for key, value in ai_options.items():
                if key in self.config:
                    self.config[key] = bool(value)
 
            logger.info(f"[Workspace {workspace_id}] Updated AI options: {ai_options}")
        except Exception as e:
            logger.error(f"Error applying AI options to config for {workspace_id}: {e}", exc_info=True)
 
 
 
 
    def _broadcast_config_change(self, workspace_id, ai_options: dict):
        """
        Broadcast updated AI options to connected browsers (optional WebSocket hook).
        """
        try:
            # If you use SocketIO or WebSocket integration:
            if hasattr(self, "socketio"):
                self.socketio.emit(
                    "config_updated",
                    {"workspace_id": workspace_id, "ai_options": ai_options},
                    broadcast=True
                )
            else:
                logger.info(f"[Broadcast skipped] No socketio configured for {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast config change: {e}", exc_info=True)
 
  
 
    def _normalize_and_store_ai_options(self, meta, ai_options):
        """Normalize boolean AI options before saving in ChromaDB."""
        try:
            # import json  <-- No need to import here, import at the top
            normalized_ai_options = {k: bool(v) for k, v in ai_options.items()}
            for key, value in normalized_ai_options.items():
                meta[f"ai_{key}"] = bool(value)
            meta["ai_options"] = json.dumps(normalized_ai_options)
            logger.info(f"Normalized AI options metadata: {meta}")
            return meta
        except Exception as e:
            logger.error(f"Error normalizing AI options: {e}", exc_info=True)
            return meta
 
    def migrate_workspace_ai_options(self):
        """Migrate old workspace metadata to new AI options format."""
        try:
            all_ids = self.workspace_collection.get()["ids"]
            for wid in all_ids:
                rec = self.workspace_collection.get(ids=[wid])
                if not rec.get("metadatas"):
                    continue
                meta = rec["metadatas"][0]
                raw = meta.get("ai_options")
                if isinstance(raw, dict):
                    new_meta = self._normalize_and_store_ai_options(meta, raw)
                    self.workspace_collection.update(
                        ids=[wid],
                        metadatas=[new_meta],
                        documents=[f"Workspace: {new_meta.get('name', wid)}"],
                    )
                    logger.info(f"Migrated ai_options for {wid}")
        except Exception as e:
            logger.exception(f"Failed workspace AI migration: {e}")
 
 
    def get_workspace_ai_options(self, workspace_id: str) -> dict:
        """
        Fetch saved AI feature toggles for a workspace from ChromaDB.
        Returns dict like {'sql': True, 'summarization': False, ...}
        """
        try:
            result = self.workspace_collection.get(ids=[workspace_id])
            if not result or not result.get("metadatas"):
                logger.warning(f"No metadata found for workspace {workspace_id}")
                return {}
 
            metadata = result["metadatas"][0]
            ai_options = metadata.get("ai_options")
 
            # Handle if stored as JSON string
            if isinstance(ai_options, str):
                ai_options = json.loads(ai_options)
            elif not isinstance(ai_options, dict):
                ai_options = {}
 
            logger.info(f"Loaded AI options for workspace {workspace_id}: {ai_options}")
            return ai_options
        except Exception as e:
            logger.error(f"Error loading AI options for workspace {workspace_id}: {e}", exc_info=True)
            return {}
 
 
    
    
    def _log_complete_user_activity(self, question, sql_query, summary, workspace_name, user_role, user_id, cache_id):
        logger.info(f"inside _log_complete_user_activity", extra={"flow":True})
        """Helper method to log complete user activity including plot data from cache"""
        try:
            # Get plot data if it exists in cache
            plot_data = None
            try:
                # fig_json = self.cache.get(id=cache_id, field="fig_json")
                # dataframe = self.cache.get(id=cache_id, field="df")
                # df = self._df_to_parquet_bytes(dataframe)
                fig_json = None
                df = None
                # logger.info(f"df-parquet-ed", extra={"cache":True})
                if fig_json:
                    # Extract chart type or other relevant info from the figure
                    # import json
                    # fig_dict = json.loads(fig_json) if isinstance(fig_json, str) else fig_json
                    # chart_type = "unknown"
                    # data_points = 0
                   
                    # if fig_dict and 'data' in fig_dict and len(fig_dict['data']) > 0:
                    #     chart_type = fig_dict['data'][0].get('type', 'unknown')
                    #     # Try to count data points
                    #     if 'x' in fig_dict['data'][0]:
                    #         data_points = len(fig_dict['data'][0]['x'])
                    #     elif 'values' in fig_dict['data'][0]:
                    #         data_points = len(fig_dict['data'][0]['values'])
                   
                    # plot_data = f"Generated {chart_type} chart with {data_points} data points"
                    if isinstance(fig_json, (dict, list)):
                        plot_data = json.dumps(fig_json, ensure_ascii=False)
                    else:
                        # plot_data = str(fig_json)
                        plot_data = None
                else:
                    plot_data = json.dumps({"data": "No chart generated"}, ensure_ascii=False)
                    # plot_data = jsonify({"data":"No chart generated"})
                    # plot_data = {"data":"No chart generated"}
            except Exception as e:
                # plot_data = jsonify({"data":"Chart data unavailable"})
                plot_data = json.dumps({"data": "Chart data unavailable"}, ensure_ascii=False)
                logger.warning(f"Could not retrieve plot data: {str(e)}", extra={"admin":True})
 
            # Call the enhanced logging method
            self.log_user_activity(
                question_id=cache_id,
                question=question,
                sql_query=sql_query,
                summary=summary,
                plot_data=plot_data,
                workspace_name=workspace_name,
                user_role=user_role,
                user_id=user_id,
                df=df
            )
           
        except Exception as log_error:
            logger.error(f"Failed to log complete user activity: {str(log_error)}")
 
 
 
 
 
    # def log_user_activity(self, question_id, question, sql_query, workspace_name, user_role, user_id, df=None, summary=None, plot_data=None):
    #     logger.info(f"log_user_activity", extra={"flow":True})
    #     """Enhanced logging function that updates existing entries instead of creating duplicates"""
       
    #     # Skip logging if credentials are not properly configured
    #     if not self.user_mgmt_config.get('username') or not self.user_mgmt_config.get('password'):
    #         logger.warning("User activity logging skipped - database credentials not configured", extra={'admin':True})
    #         return
       
    #     max_retries = 1
    #     retry_count = 0
       
    #     while retry_count < max_retries:
    #         try:
    #             # Build connection string from config
    #             conn_str = (
    #                 f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    #                 f"SERVER={self.user_mgmt_config['server']},{self.user_mgmt_config['port']};"
    #                 f"DATABASE={self.user_mgmt_config['database']};"
    #                 f"UID={self.user_mgmt_config['username']};"
    #                 f"PWD={self.user_mgmt_config['password']};"
    #                 f"Trusted_Connection=no;"
    #                 f"Connection Timeout=30;"
    #             )
               
    #             conn = pyodbc.connect(conn_str, timeout=30)
    #             cursor = conn.cursor()
               
    #             # Truncate long fields if necessary
    #             question = (question or "")[:4000] if question else None
    #             sql_query = (sql_query or "")[:4000] if sql_query else None
    #             summary = (summary or "") if summary else None
    #             plot_data = (plot_data or "") if plot_data else None
    #             workspace_name = (workspace_name or "")[:255] if workspace_name else None
    #             workspace_id = session.get("workspace_id")
    #             user_role = (user_role or "")[:100] if user_role else None
    #             user_id = user_id if user_id else None
    #             df = df if df else None
    #             current_time = datetime.now()
               
    #             # Check if a similar entry exists within the last 5 minutes
    #             # check_query = """
    #             # SELECT question_id FROM users
    #             # WHERE question = ?
    #             # AND workspace_name = ?
    #             # AND timestamp >= DATEADD(minute, -5, ?)
    #             # ORDER BY timestamp DESC
    #             # """
    #             # check_query = """
    #             # SELECT question_id FROM users
    #             # WHERE question = ?
    #             # AND workspace_name = ?
    #             # AND timestamp >= DATEADD(minute, -5, ?)
    #             # ORDER BY timestamp DESC
    #             # """
    #             check_query = """
    #             SELECT question_id FROM users
    #             WHERE question = ?
    #             AND workspace_name = ?
    #             AND timestamp >= DATEADD(minute, -5, ?)
    #             ORDER BY timestamp DESC
    #             """
               
    #             cursor.execute(check_query, (question, workspace_name, current_time))
    #             existing_record = cursor.fetchone()
               
    #             if existing_record:
    #                 # Update existing record with complete data
    #                 # update_query = """
    #                 # UPDATE users
    #                 # SET sql_query = ?,
    #                 #     summary = ?,
    #                 #     plot_data = ?,
    #                 #     timestamp = ?,
    #                 #     user_role = ?,
    #                 #     user_id = ?,
    #                 #     df = ?
    #                 # WHERE question_id = ?
    #                 # """
                   
    #                 # cursor.execute(update_query, (
    #                 #     sql_query, summary, plot_data, current_time, user_role, user_id, df, existing_record[0]
    #                 # ))
    #                 # update_query = """
    #                 # UPDATE users
    #                 # SET sql_query = ?,
    #                 #     summary = ?,
    #                 #     timestamp = ?,
    #                 #     user_role = ?,
    #                 #     user_id = ?
    #                 # WHERE question_id = ?
    #                 # """
                   
    #                 # cursor.execute(update_query, (
    #                 #     sql_query, summary, current_time, user_role, user_id, existing_record[0]
    #                 # ))
                   
    #                 # logger.info(f"Updated existing user activity record (ID: {existing_record[0]}) for workspace: {workspace_name}")
                    
    #                 # update_query = """
    #                 # UPDATE users
    #                 # SET sql_query = ?,
    #                 #     timestamp = ?,
    #                 #     user_role = ?,
    #                 #     user_id = ?
    #                 # WHERE question_id = ?
    #                 # """
    #                 update_query = """
    #                 UPDATE users
    #                 SET sql_query = ?,
    #                     timestamp = ?,
    #                     user_role = ?,
    #                     user_id = ?
    #                 WHERE question_id = ?
    #                 """
                   
    #                 cursor.execute(update_query, (
    #                     sql_query, current_time, user_role, user_id, existing_record[0]
    #                 ))
                   
    #                 logger.info(f"Updated existing user activity record (ID: {existing_record[0]}) for workspace: {workspace_name}")
                   
    #             else:
    #                 # Insert new record only if no recent similar entry exists
    #                 # insert_query = """
    #                 # INSERT INTO users
    #                 # (question_id, question, sql_query, summary, plot_data, workspace_name, workspace_id, timestamp, user_role, user_id, df)
    #                 # VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #                 # """
                   
    #                 # cursor.execute(insert_query, (
    #                 #     question_id, question, sql_query, summary, plot_data,
    #                 #     workspace_name, workspace_id, current_time, user_role, user_id, df
    #                 # ))
                    
    #                 # insert_query = """
    #                 # INSERT INTO users
    #                 # (question_id, question, sql_query, summary, workspace_id, workspace_name, timestamp, user_id, user_role)
    #                 # VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #                 # """
                   
    #                 # cursor.execute(insert_query, (
    #                 #     question_id, question, sql_query, summary, workspace_id,
    #                 #     workspace_name, current_time, user_id, user_role 
    #                 # ))
                    
    #                 # insert_query = """
    #                 # INSERT INTO users
    #                 # (question_id, question, sql_query, workspace_id, workspace_name, timestamp, user_id, user_role)
    #                 # VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #                 # """
    #                 insert_query = """
    #                 INSERT INTO users
    #                 (question_id, question, sql_query, workspace_id, workspace_name, timestamp, user_id, user_role)
    #                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #                 """
                   
    #                 cursor.execute(insert_query, (
    #                     question_id, question, sql_query, workspace_id,
    #                     workspace_name, current_time, user_id, user_role 
    #                 ))
                   
    #                 logger.info(f"Inserted new user activity record for workspace: {workspace_name}")
               
    #             conn.commit()
    #             cursor.close()
    #             conn.close()
               
    #             logger.info(f"User activity logged successfully for workspace: {workspace_name}")
    #             break  # Success, exit retry loop
               
    #         except Exception as e:
    #             retry_count += 1
    #             logger.error(f"Failed to log user activity (attempt {retry_count}/{max_retries}): {str(e)}")
               
    #             if retry_count >= max_retries:
    #                 logger.error("Maximum retries reached. User activity logging failed permanently.")
    #                 # Fallback to file logging
    #                 try:
    #                     # with open("user_activity_log_backup.txt", "a") as f:
    #                     #     f.write(f"{datetime.now()}: {question_id} {question}, {sql_query}, {summary}, {plot_data}, {workspace_name}, {workspace_id}, {user_role}, {user_id}, {df}\n")
                        
    #                     # with open("user_activity_log_backup.txt", "a") as f:
    #                     #     f.write(f"{datetime.now()}: {question_id}, {question}, {sql_query}, {summary}, {workspace_name}, {workspace_id}, {user_role}, {user_id}\n")
                        
    #                     with open("user_activity_log_backup.txt", "a") as f:
    #                         f.write(f"{datetime.now()}: {question_id}, {question}, {sql_query}, {workspace_name}, {workspace_id}, {user_role}, {user_id}\n")
    #                 except:
    #                     pass  # Even backup logging failed
    #                 break
    def normalize_model_name(self, model_name: str) -> str:
        if not model_name:
            return "unknown"

        name = model_name.lower()

        # Strip version suffixes
        if name.startswith("o3"):
            return "o3"

        if name.startswith("o1"):
            return "o1"

        if name.startswith("gpt-5.1"):
            return "gpt-5.1"

        if name.startswith("gpt-4.1"):
            return "gpt-4.1"

        return name

    def log_user_activity(
        self,
        question_id: str,
        question: str,
        sql_query: str,
        workspace_name: str,
        user_role: str = None,
        user_id: str = None,
        detected_language: str = "en",
        token_count: int = 0,
        input_tokens: int = None,
        output_tokens: int = None,
        model_name: str = None,
        cached_input_tokens: int = 0,
        cost_usd: float = None,
        df=None,           # optional — not stored
        summary: str = None,
        plot_data: str = None
    ):
        """
        Logs or updates user activity in the 'users' table using question_id as the primary key.
        - Always checks by question_id first (prevents PK violation)
        - Updates if exists, inserts if not
        - Safe retry + transaction handling
        - Fallback to file logging on complete failure
        """
        logger.info("log_user_activity called", extra={"flow": True})

        # Skip if DB credentials missing
        if not self.user_mgmt_config.get('username') or not self.user_mgmt_config.get('password'):
            logger.warning("User activity logging skipped - DB credentials missing", extra={"admin": True})
            return

        # Safe truncation & normalization
        question       = (question or "")[:4000]
        sql_query      = (sql_query or "")[:4000]
        summary        = (summary or "")[:4000] if summary else None
        plot_data      = (plot_data or "")[:4000] if plot_data else None
        workspace_name = (workspace_name or "")[:255]
        user_role      = (user_role or "")[:100]
        model_name     = (model_name or "")[:100]
        user_id        = user_id or None
        detected_language = detected_language or "en"

        token_count         = int(token_count or 0)
        input_tokens        = int(input_tokens or 0)
        output_tokens       = int(output_tokens or 0)
        cached_input_tokens = int(cached_input_tokens or 0)
        cost_usd            = float(cost_usd) if cost_usd is not None else None

        workspace_id = session.get("workspace_id")
        current_time = datetime.now()

        max_retries = 2
        retry_count = 0
        conn = None
        cursor = None

        while retry_count < max_retries:
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.user_mgmt_config['server']},{self.user_mgmt_config['port']};"
                    f"DATABASE={self.user_mgmt_config['database']};"
                    f"UID={self.user_mgmt_config['username']};"
                    f"PWD={self.user_mgmt_config['password']};"
                    f"Trusted_Connection=no;"
                    f"Connection Timeout=30;"
                )

                conn = pyodbc.connect(conn_str, timeout=30)
                conn.autocommit = False  # Enable transaction control
                cursor = conn.cursor()

                # ────────────────────────────────────────────────
                # Check if record already exists using PRIMARY KEY (question_id)
                # ────────────────────────────────────────────────
                check_query = "SELECT 1 FROM dbo.users WHERE question_id = ?"
                cursor.execute(check_query, (question_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    # UPDATE existing record
                    update_query = """
                        UPDATE dbo.users
                        SET
                            question            = ?,
                            sql_query           = ?,
                            summary             = ?,
                            plot_data           = ?,
                            workspace_name      = ?,
                            workspace_id        = ?,
                            timestamp           = ?,
                            user_role           = ?,
                            user_id             = ?,
                            detected_language   = ?,
                            token_count         = ?,
                            input_tokens        = ?,
                            output_tokens       = ?,
                            cached_input_tokens = ?,
                            cost_usd            = ?,
                            model_name          = ?
                        WHERE question_id = ?
                    """
                    cursor.execute(update_query, (
                        question,
                        sql_query,
                        summary,
                        plot_data,
                        workspace_name,
                        workspace_id,
                        current_time,
                        user_role,
                        user_id,
                        detected_language,
                        token_count,
                        input_tokens,
                        output_tokens,
                        cached_input_tokens,
                        cost_usd,
                        model_name,
                        question_id
                    ))
                    logger.info(f"Updated existing user activity record for question_id={question_id}", extra={"admin": True})

                else:
                    # INSERT new record
                    insert_query = """
                        INSERT INTO dbo.users (
                            question_id, question, sql_query, summary, plot_data,
                            workspace_name, workspace_id, timestamp,
                            user_role, user_id, detected_language,
                            token_count, input_tokens, output_tokens,
                            cached_input_tokens, cost_usd, model_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (
                        question_id,
                        question,
                        sql_query,
                        summary,
                        plot_data,
                        workspace_name,
                        workspace_id,
                        current_time,
                        user_role,
                        user_id,
                        detected_language,
                        token_count,
                        input_tokens,
                        output_tokens,
                        cached_input_tokens,
                        cost_usd,
                        model_name
                    ))
                    logger.info(f"Inserted new user activity record for question_id={question_id}", extra={"admin": True})

                conn.commit()
                logger.info("User activity logged successfully", extra={"flow": True})
                break  # Success → exit retry loop

            except pyodbc.IntegrityError as ie:
                # Catch PK violation specifically (should not happen anymore with new logic)
                retry_count += 1
                logger.error(f"PK violation caught (attempt {retry_count}): {str(ie)}", exc_info=True)
                if conn:
                    conn.rollback()

            except Exception as e:
                retry_count += 1
                logger.error(f"Logging failed (attempt {retry_count}/{max_retries}): {str(e)}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass

                if retry_count >= max_retries:
                    # Final fallback: write to file
                    try:
                        with open("user_activity_log_backup.txt", "a", encoding="utf-8") as f:
                            f.write(
                                f"[{datetime.now()}] qid={question_id} | "
                                f"question='{question[:120]}...' | sql='{sql_query[:80]}...' | "
                                f"ws={workspace_name} | user={user_id} | lang={detected_language} | "
                                f"tokens={token_count} (in={input_tokens}, out={output_tokens}) | "
                                f"model={model_name} | cost={cost_usd}\n"
                            )
                        logger.info("Fallback file logging succeeded")
                    except Exception as backup_err:
                        logger.error(f"Backup logging also failed: {backup_err}")

            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                if conn:
                    try:
                        conn.close()
                    except:
                        pass


    def log_token_count(
        self,
        question_id: str,
        total_tokens: int,
        input_tokens: int,
        output_tokens: int,
        model_name: str,
        cached_input_tokens: int = 0,
        user_id: str = None  # kept for future use if you add it to WHERE
    ):
        logger.info("log_token_count (billing)", extra={"flow": True})

        # Normalize model
        try:
            normalized_model = self.normalize_model_name(model_name)
        except Exception:
            normalized_model = model_name or "unknown"

        # Pricing (update as needed when new models arrive)
        MODEL_PRICING = {
            "gpt-4.1": {"input": 5.00, "output": 15.00},
            "gpt-4.1-mini": {"input": 0.60, "output": 2.40},
            "gpt-4.1-preview": {"input": 3.00, "output": 10.00},
            "o3": {"input": 1.00, "output": 3.00},
            "o1": {"input": 6.00, "output": 18.00},
            "o1-preview": {"input": 6.00, "output": 18.00},
            "gpt-5.1": {"input": 1.25, "output": 10.00},
            # add more as needed
        }

        price_in = MODEL_PRICING.get(normalized_model, {}).get("input", 0.0)
        price_out = MODEL_PRICING.get(normalized_model, {}).get("output", 0.0)

        billable_input = max(0, input_tokens - cached_input_tokens)
        cost_usd = round(
            (billable_input / 1_000_000) * price_in +
            (output_tokens / 1_000_000) * price_out,
            8
        )

        conn = None
        cursor = None

        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.user_mgmt_config['server']},{self.user_mgmt_config['port']};"
                f"DATABASE={self.user_mgmt_config['database']};"
                f"UID={self.user_mgmt_config['username']};"
                f"PWD={self.user_mgmt_config['password']};"
                f"Trusted_Connection=no;"
                f"Connection Timeout=30;"
            )

            conn = pyodbc.connect(conn_str, timeout=30)
            cursor = conn.cursor()

            # Ensure row exists
            cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE question_id = ?)
                BEGIN
                    INSERT INTO dbo.users (question_id, token_count, user_id)
                    VALUES (?, 0, ?)
                END
                """,
                (question_id, question_id, user_id)  # user_id optional, can be NULL
            )

            # Accumulative update
            update_query = """
                UPDATE dbo.users
                SET
                    model_name = ?,
                    input_tokens = ISNULL(input_tokens, 0) + ?,
                    output_tokens = ISNULL(output_tokens, 0) + ?,
                    cached_input_tokens = ISNULL(cached_input_tokens, 0) + ?,
                    cost_usd = ISNULL(cost_usd, 0) + ?,
                    token_count = ISNULL(token_count, 0) + ?
                WHERE question_id = ?
            """

            cursor.execute(update_query, (
                normalized_model,
                input_tokens,           # no need for int() if already int
                output_tokens,
                cached_input_tokens,
                cost_usd,
                total_tokens,
                question_id
            ))

            conn.commit()

            logger.info(
                f"[BILLING OK] qid={question_id} | model={normalized_model} | "
                f"in={input_tokens} | out={output_tokens} | cached={cached_input_tokens} | "
                f"total={total_tokens} | cost=${cost_usd:.8f}",
                extra={"billing": True}
            )

            return cost_usd

        except Exception as e:
            logger.error(
                f"[BILLING FAILED] question_id={question_id}: {str(e)}",
                exc_info=True
            )
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return 0.0  # or None if you prefer

        finally:
            for obj in (cursor, conn):
                if obj:
                    try:
                        obj.close()
                    except:
                        pass

###########################################################################################################
 
 
####getting ws metadata
def get_workspace_metadata(self, workspace_id):
            try:
                results = self.workspace_collection.get(ids=[str(workspace_id)])
                if not results.get("metadatas"):
                    return None
                return results["metadatas"][0]
            except Exception as e:
                logger.error(f"Error fetching workspace metadata: {str(e)}", exc_info=True)
                return None
 

def get_base_url():
    """
    Determines the base URL of the Flask app.
    - If running locally, it checks if ngrok is active and uses the public URL.
    - If already hosted, it uses the request's base URL.
    """
    host = request.host_url.rstrip('/')  # Get the request base URL

    # If running locally (127.0.0.1 or localhost), check for ngrok tunnel
    if "127.0.0.1" in host or "localhost" in host:
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels")  # ngrok API
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":  # Use HTTPS tunnel
                    return tunnel["public_url"]
        except requests.RequestException:
            pass  # If ngrok is not running, fallback to localhost

    return host  # Return request URL if not using ngrok

############################################


def process_request(user_message, vn):
    try:
        sql_gen_start = time.time()
        sql_gen_time = 0
        summary_gen_time = 0
        
        # Step 1: Check Training Data for an Exact Match
        sql_from_training = vn.get_similar_question_sql(user_message)
        if sql_from_training:
            extracted_sql = sql_from_training[0]["sql"]
            sql_source = "Training Data"
            sql_gen_time = time.time() - sql_gen_start
            logger.info(f"SQL from training data took {sql_gen_time:.2f} seconds", extra={"admin": True})
        else:
            # Step 2: Generate SQL Using LLM
            sql = vn.generate_sql(user_message)
            extracted_sql = vn.extract_sql(sql)
            sql_source = "LLM (Language Model)"
            sql_gen_time = time.time() - sql_gen_start
            logger.info(f"SQL generation took {sql_gen_time:.2f} seconds", extra={"admin": True})

        # Step 3: Validate SQL
        if not vn.is_sql_valid(extracted_sql):
            payload = {"text": "Invalid SQL generated."}
            requests.post(INCOMING_WEBHOOK_URL, json=payload)
            return

        # Step 4: Execute the Query
        result_df = vn.run_sql(extracted_sql)
        total_rows = len(result_df)
        max_display_rows = 10

        # Step 5: Generate Summary (only if result_df is not empty)
        summary_text = ""
        if not result_df.empty:
            try:
                logger.info("Starting summary generation", extra={"admin": True})
                summary_start = time.time()
               
                # Schema from DataFrame (column: dtype)
                schema = result_df.dtypes.apply(lambda x: str(x)).to_dict()

                summary_text = vn.generate_summary(
                    question=user_message,
                    df=result_df,
                    sql=extracted_sql,
                    schema=schema
                )
                summary_gen_time = time.time() - summary_start
                logger.info(f"Summary generation took {summary_gen_time:.2f} seconds", extra={"admin": True})
                logger.info(f"summary is {summary_text}", extra={"admin": True})
            except Exception as summary_error:
                summary_text = f"_Summary generation failed: {str(summary_error)}_"

        # Step 6: Format the Result
        if result_df.empty:
            formatted_result = "No results found."
            file_link = ""
        elif total_rows > max_display_rows:
            os.makedirs("static", exist_ok=True)
            file_id = str(uuid.uuid4())[:8]
            file_path = f"static/query_result_{file_id}.csv"
            result_df.to_csv(file_path, index=False)

            markdown_table = (
                "| " + " | ".join(result_df.columns) + " |\n" +
                "| " + " | ".join(["---"] * len(result_df.columns)) + " |\n"
            )
            for _, row in result_df.head(max_display_rows).iterrows():
                markdown_table += "| " + " | ".join(str(cell) for cell in row) + " |\n"

            formatted_result = markdown_table
            file_link = f"\n\n[Download Full Results](/{file_path})"
        else:
            markdown_table = (
                "| " + " | ".join(result_df.columns) + " |\n" +
                "| " + " | ".join(["---"] * len(result_df.columns)) + " |\n"
            )
            for _, row in result_df.iterrows():
                markdown_table += "| " + " | ".join(str(cell) for cell in row) + " |\n"

            formatted_result = markdown_table
            file_link = ""

        # Step 7: Final Response Text
        response_text = (
            f"**Query Result:**\n\n"
            f"**Question:** {user_message}\n\n"
            f"****\n"
            f"**SQL (Source: {sql_source}):** {extracted_sql}\n\n\n"
            f"****\n"
            f"{formatted_result}{file_link}"
            f"****\n"
        )

        if summary_text:
            response_text += f"\n\n**Summary:**\n{summary_text}"

        # Post final response to incoming webhook
        payload = {"text": response_text}
        requests.post(INCOMING_WEBHOOK_URL, json=payload)


    except Exception as e:
        error_text = f"Error: {str(e)}"
        payload = {"text": error_text}
        requests.post(INCOMING_WEBHOOK_URL, json=payload)










# def load_email_config():
#     load_dotenv(override=True)

#     return {
#         "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
#         "smtp_port": int(os.getenv("SMTP_PORT", "587")),
#         "sender": os.getenv("SENDER_EMAIL"),
#         "password": os.getenv("SENDER_PASSWORD"),
#         "recipients": os.getenv("RECIPIENTS", "").split(","),
#         "cc": os.getenv("CC_EMAILS", ""),
#         "subject": os.getenv("EMAIL_SUBJECT", "Low Rating Feedback Alert"),
#         "body": os.getenv("EMAIL_BODY", ""),
#         "include_sent": os.getenv("INCLUDE_SENT", "False") == "True",
#     }



# def load_email_config():
#     cfg = load_config()

#     return {
#         "smtp_server": cfg.get("smtp_server", "smtp.gmail.com"),
#         "smtp_port": int(cfg.get("smtp_port", 587)),
#         "sender": cfg.get("sender_email"),
#         "password": cfg.get("sender_password"),
#         "recipients": cfg.get("receivers", []),
#         "cc": cfg.get("cc", ""),
#         "subject": cfg.get("subject", "Low Rating Feedback Alert"),
#         "body": cfg.get("body", ""),
#         "include_sent": cfg.get("include_sent", False),
#         "email_interval": int(cfg.get("email_interval", 120)),
#     }




def load_email_config():
    try:
        with _config_lock:
            if not os.path.exists(CONFIG_FILE):
                return {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "",
                    "sender_password": "",
                    "recipients": [],
                    "cc": "",
                    "subject": "Low Rating Feedback Alert",
                    "body": "",
                    "include_sent": False,
                    "email_interval": 120
                }

            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                
                # Set default SMTP settings for Outlook if missing
                provider = cfg.get("email_provider", "gmail")
                if provider == "outlook":
                    if "smtp_server" not in cfg:
                        cfg["smtp_server"] = "smtp.office365.com"
                    if "smtp_port" not in cfg:
                        cfg["smtp_port"] = 587
                elif provider == "gmail":
                    if "smtp_server" not in cfg:
                        cfg["smtp_server"] = "smtp.gmail.com"
                    if "smtp_port" not in cfg:
                        cfg["smtp_port"] = 587
                
                return cfg
    except Exception as e:
        print("Config load error:", e)
        raise







def fetch_low_rating_feedback():
    cfg = load_email_config()

    conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING)
    cursor = conn.cursor()

    if cfg["include_sent"]:
        cursor.execute("""
            SELECT id, workspace_id, question, sql, rating, comment, created_at
            FROM user_feedback
            WHERE rating <= 3
        """)
    else:
        cursor.execute("""
            SELECT id, workspace_id, question, sql, rating, comment, created_at
            FROM user_feedback
            WHERE rating <= 2 AND email_sent = 0
        """)

    rows = cursor.fetchall()
    conn.close()
    return rows









def generate_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "workspace_id",
        "question",
        "sql",
        "rating",
        "comment",
        "created_at"
    ])

    for r in rows:
        writer.writerow([
            r.id,
            r.workspace_id,
            r.question,
            r.sql,
            r.rating,
            r.comment,
            r.created_at
        ])

    output.seek(0)
    return output.getvalue()



def send_email(csv_content):
    cfg = load_email_config()

    # Resolve recipients and sender details defensively
    recipients = cfg.get("recipients") or cfg.get("receivers") or []

    provider = cfg.get("email_provider", "gmail")
    smtp_server = cfg.get("smtp_server") or ("smtp.office365.com" if provider == "outlook" else "smtp.gmail.com")
    smtp_port = int(cfg.get("smtp_port", 587))

    sender_email = (
        cfg.get("sender_email")
        or cfg.get("gmail", {}).get("sender_email")
        or cfg.get("outlook", {}).get("sender_email")
        or ""
    )

    sender_password = (
        cfg.get("sender_password")
        or cfg.get("gmail", {}).get("sender_password")
        or cfg.get("outlook", {}).get("sender_password")
        or ""
    )

    msg = EmailMessage()
    msg["From"] = f"Feedback <{sender_email}>"
    msg["To"] = ", ".join(recipients)
    cc_value = cfg.get("cc", "")
    if cc_value:
        msg["Cc"] = cc_value
    msg["Subject"] = cfg.get("subject", "Low Rating Feedback Alert")
    msg["Reply-To"] = sender_email

    msg.set_content(cfg.get("body", ""))

    filename = f"user_feedback_low_rating_{datetime.now():%Y%m%d_%H%M%S}.csv"

    msg.add_attachment(
        csv_content.encode("utf-8"),
        maintype="text",
        subtype="csv",
        filename=filename
    )

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)







def feedback_email_job():
    cfg = load_email_config()

    rows = fetch_low_rating_feedback()
    if not rows:
        print("No low-rating feedback.")
        return

    csv_content = generate_csv(rows)
    send_email(csv_content)

    # ✅ Mark only when not including already-sent
    if not cfg["include_sent"]:
        mark_feedback_as_emailed()

    print("Email sent successfully.")



def mark_feedback_as_emailed():
    conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE user_feedback
        SET email_sent = 1
        WHERE rating <= 3 AND email_sent = 0
    """)

    conn.commit()
    conn.close()






####################agents###############
SCENARIO_MESSAGES = {

    # 1️⃣ Order created but item not present in inventory
    "S1_MISSING_ITEM_MASTER": {
        "subject": "Stock Alert: Orders Created with Missing Inventory Items",
        "body": (
            "Hello Team,\n\n"
            "We identified one or more orders containing items that are currently "
            "not present in the inventory records.\n\n"
            "This may indicate that the item master or inventory setup "
            "has not yet been completed.\n\n"
            "Kindly review the affected orders to avoid fulfillment delays.\n\n"
            "The complete list of impacted records is attached as a CSV file.\n"
        )
    },

    # 2️⃣ Ordered quantity exceeds available inventory
    "S2_ORDER_QTY_EXCEEDS_STOCK": {
        "subject": "Stock Alert: Order Quantity Exceeds Available Inventory",
        "body": (
            "Hello Team,\n\n"
            "Some orders have requested quantities that exceed the "
            "currently available inventory levels.\n\n"
            "This may lead to partial fulfillment or picking issues "
            "during wave execution.\n\n"
            "Please review inventory availability or adjust order quantities as needed.\n\n"
            "Full details are available in the attached CSV file.\n"
        )
    },

    # 3️⃣ Inventory depleted during picking (multiple orders competing)
    "S3_INVENTORY_DEPLETED_DURING_PICK": {
        "subject": "Stock Alert: Inventory Depleted During Picking",
        "body": (
            "Hello Team,\n\n"
            "During picking activity, inventory for certain items was found "
            "to be depleted after allocation to earlier orders.\n\n"
            "As a result, subsequent orders could not be picked completely.\n\n"
            "We recommend reviewing inventory allocation and replenishment status.\n\n"
            "Please refer to the attached CSV for detailed information.\n"
        )
    },

    # 4️⃣ Pick task not created during wave release due to zero inventory
    "S4_PICK_TASK_NOT_CREATED": {
        "subject": "Stock Alert: Pick Task Not Created Due to Inventory Shortage",
        "body": (
            "Hello Team,\n\n"
            "During wave release, pick tasks could not be created for certain items "
            "due to insufficient or zero inventory.\n\n"
            "This may delay order processing until inventory is replenished.\n\n"
            "Kindly review the inventory status and take appropriate action.\n\n"
            "The affected records are provided in the attached CSV file.\n"
        )
    },

    # 5️⃣ Inventory became insufficient due to concurrent picks
    "S5_INVENTORY_CONSUMED_BY_OTHER_ORDER": {
        "subject": "Stock Alert: Inventory Consumed by Concurrent Order Processing",
        "body": (
            "Hello Team,\n\n"
            "Inventory for certain items was consumed by other orders "
            "during active processing.\n\n"
            "As a result, remaining orders could not be fulfilled as expected.\n\n"
            "Please review order prioritization and replenishment plans.\n\n"
            "Detailed records are available in the attached CSV file.\n"
        )
    },

    # 6️⃣ Inventory exists but is not in available status
    "S6_INVENTORY_NOT_AVAILABLE_STATUS": {
        "subject": "Stock Alert: Inventory Exists but Is Not Available for Allocation",
        "body": (
            "Hello Team,\n\n"
            "Some items exist in inventory but are currently not in an "
            "available status (for example, on hold or unavailable).\n\n"
            "This may prevent allocation or picking for active orders.\n\n"
            "Kindly review the inventory status and take corrective action if required.\n\n"
            "Please see the attached CSV for affected records.\n"
        )
    },

    # 7️⃣ Cycle count adjustment reduced inventory to zero
    "S7_CYCLE_COUNT_ADJUSTED_TO_ZERO": {
        "subject": "Inventory Alert: Cycle Count Adjustment Reduced Quantity to Zero",
        "body": (
            "Hello Team,\n\n"
            "A recent cycle count adjustment has reduced the inventory quantity "
            "of certain items to zero.\n\n"
            "This may impact existing or upcoming orders.\n\n"
            "Please review the adjustment details and validate physical inventory.\n\n"
            "Refer to the attached CSV for more information.\n"
        )
    },

    # 8️⃣ System shows inventory but physical stock is missing
    "S8_SYSTEM_PHYSICAL_MISMATCH": {
        "subject": "Inventory Alert: System Inventory Available but Physical Stock Missing",
        "body": (
            "Hello Team,\n\n"
            "Inventory adjustments indicate a mismatch between system inventory "
            "and physical stock availability.\n\n"
            "Although the system reflects availability, physical inventory "
            "may not be present.\n\n"
            "We recommend validating physical stock and correcting discrepancies.\n\n"
            "Detailed records are attached for review.\n"
        )
    },

    # 9️⃣ Expired inventory linked to orders
    "S9_EXPIRED_INVENTORY": {
        "subject": "Inventory Alert: Orders Linked to Expired Inventory",
        "body": (
            "Hello Team,\n\n"
            "Some orders are associated with inventory that has passed "
            "its expiration date.\n\n"
            "To ensure quality and compliance, please review these orders "
            "before further processing.\n\n"
            "The complete list of affected orders is attached as a CSV file.\n"
        )
    },

    # 🔟 Order items not yet received into warehouse (ASN missing)
    "S10_ITEM_NOT_RECEIVED": {
        "subject": "Order Alert: Items Ordered but Not Yet Received into Warehouse",
        "body": (
            "Hello Team,\n\n"
            "Orders have been identified with items that have not yet "
            "been received into the warehouse.\n\n"
            "This may be due to pending ASN receipts or upstream delays.\n\n"
            "Please review inbound receipts and take appropriate action.\n\n"
            "Affected records are attached for reference.\n"
        )
    },

    # 1️⃣1️⃣ Manual inventory adjustment detected
    "S11_MANUAL_INVENTORY_ADJUSTMENT": {
        "subject": "Inventory Alert: Manual Inventory Adjustment Detected",
        "body": (
            "Hello Team,\n\n"
            "Manual inventory adjustments have been detected for items "
            "associated with active orders.\n\n"
            "Such adjustments may impact inventory accuracy "
            "and order fulfillment.\n\n"
            "Please review the adjustment details for validation.\n\n"
            "The full data set is attached for your reference.\n"
        )
    },

    "DEFAULT": {
    "subject": "Stock Alert: Inventory Exception Detected",
    "body": (
        "Hello Team,\n\n"
        "An inventory-related exception has been detected in the system.\n\n"
        "This alert was generated because the scenario type was not explicitly "
        "mapped in the alert configuration.\n\n"
        "Please review the attached records and take appropriate action.\n\n"
        "The complete data set is provided as a CSV attachment.\n"
    )
}


}


def rows_to_csv(rows):
    """
    Convert list[dict] → CSV string (in memory)
    """
    if not rows:
        return None

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()




###########

SCENARIO_SQL_MAP = {
    "S1_MISSING_ITEM_MASTER": """
        SELECT order_number 
        FROM t_order_detail 
        WHERE item_number NOT IN (SELECT item_number FROM t_stored_item)
    """,
    
    "S2_ORDER_QTY_EXCEEDS_STOCK": """
        SELECT 
            ord.order_number,
            ord.item_number,
            ord.qty AS ordered_qty,
            sto.actual_qty AS stored_qty
        FROM t_order_detail ord
        JOIN t_stored_item sto ON ord.item_number = sto.item_number
        WHERE ord.qty > sto.actual_qty
    """,
    
    "S3_INVENTORY_DEPLETED_DURING_PICK": """
        SELECT * FROM t_stored_item WHERE actual_qty <= '0'
    """,
    
    "S4_PICK_TASK_NOT_CREATED": """
        SELECT 
            ord.order_number,
            ord.item_number,
            ord.qty AS required_qty,
            sto.actual_qty AS available_qty
        FROM t_order_detail ord
        JOIN t_stored_item sto ON ord.item_number = sto.item_number
        WHERE sto.actual_qty <= 0
    """,
    
    "S5_INVENTORY_CONSUMED_BY_OTHER_ORDER": """
        SELECT 
            ord.order_number,
            ord.item_number,
            ord.qty AS required_qty,
            ISNULL(sto.actual_qty, 0) AS available_qty
        FROM t_order_detail ord
        LEFT JOIN t_stored_item sto ON ord.item_number = sto.item_number
        WHERE ISNULL(sto.actual_qty, 0) <= 0
           OR ord.qty > ISNULL(sto.actual_qty, 0)
    """,
    
    "S6_INVENTORY_NOT_AVAILABLE_STATUS": """
        SELECT order_number 
        FROM t_order_detail 
        WHERE item_number NOT IN (
            SELECT item_number FROM t_stored_item WHERE status<>'A'
        )
    """,
    
    "S7_CYCLE_COUNT_ADJUSTED_TO_ZERO": """
        SELECT 
            cc.trigger_id,
            cc.wh_id,
            cc.item_number,
            cc.location_id,
            cc.reason,
            cc.triggered_during,
            cc.trigger_date,
            sto.actual_qty
        FROM t_cycle_count_trigger cc
        JOIN t_stored_item sto ON cc.item_number = sto.item_number
        WHERE cc.triggered_during LIKE '%Inventory Adj%'
          AND sto.actual_qty = 0
    """,
    
    "S8_SYSTEM_PHYSICAL_MISMATCH": """
        SELECT DISTINCT
            tl.item_number,
            sto.actual_qty AS system_qty,
            tl.description
        FROM t_tran_log tl
        JOIN t_stored_item sto ON tl.item_number = sto.item_number
        WHERE tl.description LIKE '%Adjust%'
          AND sto.actual_qty = 0
    """,
    
    "S9_EXPIRED_INVENTORY": """
        SELECT DISTINCT ord.order_number 
        FROM t_order_detail ord 
        JOIN t_stored_item sto ON ord.item_number = sto.item_number
        WHERE sto.expiration_date < GETDATE()
    """,
    
    "S10_ITEM_NOT_RECEIVED": """
        SELECT 
            ord.order_number,
            ord.item_number
        FROM t_order_detail ord
        WHERE NOT EXISTS (
            SELECT 1
            FROM t_aht_receipt rcp
            WHERE rcp.item_number = ord.item_number
        )
    """,
    
    "S11_MANUAL_INVENTORY_ADJUSTMENT": """
        SELECT DISTINCT
            ord.order_number,
            ord.item_number,
            sto.actual_qty
        FROM t_order_detail ord
        JOIN t_stored_item sto ON ord.item_number = sto.item_number
        JOIN t_tran_log tl ON ord.item_number = tl.item_number
        WHERE tl.description LIKE '%Inventory Adjust%'
    """
}


#data integrity for agents

DATA_INTEGRITY_SQL_MAP = {
    "duplicate_approval": """
    SELECT *
    FROM (
        SELECT *,
               COUNT(*) OVER (
                   PARTITION BY work_q_id, location_id, item_number, hu_id
               ) AS duplicate_approvals
        FROM t_cycle_count_approval WITH(NOLOCK)
        WHERE approval_status = 'Open'
    ) t
    WHERE duplicate_approvals > 1
    """,

    "duplicate_cycle_transaction": """
    SELECT *
FROM (
    SELECT *,
           COUNT(*) OVER (
               PARTITION BY
                   control_number,
                   location_id,
                   item_number,
                   hu_id,
                   tran_qty
           ) AS duplicate_count,
           CAST(start_tran_date AS DATETIME)
           + CAST(end_tran_time AS DATETIME) AS tran_datetime
    FROM t_tran_log WITH(NOLOCK)
    WHERE tran_type = '800'
      AND location_id IS NOT NULL
      AND tran_qty IS NOT NULL
) duplicate_transactions
WHERE duplicate_count > 1
  AND tran_datetime >= DATEADD(HOUR, 7, CAST(CAST(GETDATE()-1 AS DATE) AS DATETIME))
  AND tran_datetime <  DATEADD(HOUR, 7, CAST(CAST(GETDATE()   AS DATE) AS DATETIME))
ORDER BY tran_datetime DESC;
    """,

    "duplicate_adjustment": """
    SELECT *
    FROM (
        SELECT *,
               COUNT(*) OVER (
                   PARTITION BY transaction_code, item_number,
                                quantity_before, quantity_after,
                                quantity_change, hu_id,
                                from_location_id, to_location_id,
                                user_id, reason_code
               ) AS duplicate_count
        FROM t_al_host_inventory_adjustment WITH(NOLOCK)
    ) t
    WHERE duplicate_count > 1
    """
}


DATA_INTEGRITY_MESSAGES = {
    "duplicate_approval": {
        "subject": "Duplicate Approval Records Detected",
        "body": "Duplicate open cycle count approvals detected."
    },
    "duplicate_cycle_transaction": {
        "subject": "Duplicate Cycle Count Transactions Found",
        "body": "Duplicate cycle count transactions found."
    },
    "duplicate_adjustment": {
        "subject": "Duplicate Adjustment Records Found",
        "body": "Duplicate inventory adjustments detected."
    }
}














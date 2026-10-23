import json
import logging
import asyncio
import ast
import os
import re
import html as html_escape_lib
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
from werkzeug.security import generate_password_hash
from dateutil.relativedelta import relativedelta
from collections import deque as _deque
import openai
from openai import OpenAI
from openai import OpenAIError
# HTTP/Network
import requests

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

# Custom/Project-Specific (Based on your listed imports)
from ..base import VannaBase
from ..base.base import DELIVERY_CUES
from ..ollama import Ollama
from ..openai import OpenAI_Chat
from ..chromadb import ChromaDB_VectorStore
from .assets import css_content, html_content, js_content
from .auth import AuthInterface, NoAuth, BasicAuth
from .config import index_template
from .prediction_page import prediction_template
from .anomaly_page import anomaly_template
from .vn_registry import VannaRegistry, VnRouter
from .chat_context import ChatContext, friendly_sql_error
from .access_control import install_access_control, ADMIN_ROLES, _wants_json, normalize_role
from ..warehouse_perf import create_warehouse_perf

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
import asyncio


from threading import Thread
from flask import request, jsonify, make_response
from urllib.parse import urlparse



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
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from zoneinfo import ZoneInfo
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

# Scheduling/condition requests that are missing one piece of information (what
# to send, or which registered recipient) — keyed by "{workspace_id}:{username}",
# one open clarification per user per workspace at a time. Consumed and merged
# with the user's next message in _handle_schedule_message instead of hard-
# erroring on the first ambiguous message.
_pending_schedule_clarifications = {}
_pending_schedule_clarifications_lock = None   # initialised after Lock is imported below
_PENDING_CLARIFICATION_TTL_SECONDS = 600
_MAX_CLARIFICATION_ATTEMPTS = 3

# A freshly-LLM-generated (not yet saved) prediction/anomaly config that chat
# already ran and answered, waiting on the user's next message to say whether
# to keep it as a reusable named check — same shape/rationale as
# _pending_schedule_clarifications above: keyed by "{workspace_id}:{username}",
# consumed by the next message rather than auto-saving unreviewed configs.
_pending_analysis_confirmations = {}
_pending_analysis_confirmations_lock = None   # initialised after Lock is imported below
_PENDING_ANALYSIS_CONFIRMATION_TTL_SECONDS = 600

# The prediction/anomaly check behind each user's latest prediction answer,
# keyed like the dicts above. "send this to X" right after a prediction refers
# to that answer, which has no SQL of its own: the schedule stores this check
# and re-runs it at fire time instead of asking what to send.
_last_analysis_runs = {}
_LAST_ANALYSIS_RUN_TTL_SECONDS = 3600

# "How is this calculated?" / "how does this work?" / "what's the formula?" —
# a methodology question about a performance-check answer, never itself a new
# data question. Left to fall through to generate_sql, this produced either a
# clarifying question or hallucinated SQL, since "how is it calculated" names
# no table or column generate_sql could ground itself in. Cheap regex gate
# first (same rationale as _ROUTE_CUES in base.py) — most messages have no
# methodology cue at all, so this never costs an LLM round trip for them.
_METHODOLOGY_CUE = re.compile(
    r"\bhow\b.{0,30}\b(calculat|comput|deriv|measur|formula|work(s|ed|ing)?|done|arriv|determin)"
    r"|\b(what('?s| is)) the (formula|methodology|logic)\b"
    r"|\bwhere does (this|that|the) (number|data|figure|value) come from\b",
    re.IGNORECASE,
)

# An ordinary data question that generate_sql couldn't answer (its own
# anti-hallucination guard fired — no trained example/documentation covers
# this shape of question, so it returned the literal "Insufficient data for
# query." instead of guessing at columns) — previously just dead-ended the
# user there. Same shape/rationale as _pending_schedule_clarifications above:
# keyed by "{workspace_id}:{username}", the next message is treated as the
# answer to the clarifying question rather than a brand-new query, merged
# with the original question and retried through the normal generate_sql path.
_pending_query_clarifications = {}
_pending_query_clarifications_lock = None   # initialised after Lock is imported below
_PENDING_QUERY_CLARIFICATION_TTL_SECONDS = 600
_MAX_QUERY_CLARIFICATION_ATTEMPTS = 1

# Hard cap on consecutive clarifying questions shown to one user in one
# workspace, independent of _MAX_QUERY_CLARIFICATION_ATTEMPTS above. That
# per-thread counter only increments when a reply is judged to MERGE with
# the prior clarification — but is_fresh_topic_change (the judgment call
# that decides merge-vs-new) can misjudge a loosely-phrased real answer as
# a "new question", which resets the per-thread counter to 0 and lets the
# cap be bypassed indefinitely, one misjudged reset at a time. This streak
# counter tracks "how many clarifying questions in a row has this user been
# asked, regardless of how each one was classified" and is the backstop
# that actually guarantees the conversation can't loop forever — reset to 0
# only by an actual answer (a real "sql" response), not by any judgment
# call about merging.
_clarification_streaks = {}   # key -> {"count": int, "last_at": float}
_CLARIFICATION_STREAK_WINDOW_SECONDS = 300
_MAX_CLARIFICATION_STREAK = 2


def _clarification_streak_count(key):
    """Current consecutive-clarification count for this user/workspace, 0 if
    none yet or the window since the last one has expired."""
    with _clarification_streaks_lock:
        entry = _clarification_streaks.get(key)
    if not entry or time.time() - entry.get("last_at", 0) > _CLARIFICATION_STREAK_WINDOW_SECONDS:
        return 0
    return entry.get("count", 0)


def _clarification_streak_increment(key):
    with _clarification_streaks_lock:
        entry = _clarification_streaks.get(key)
        count = (
            entry.get("count", 0)
            if entry and time.time() - entry.get("last_at", 0) <= _CLARIFICATION_STREAK_WINDOW_SECONDS
            else 0
        )
        _clarification_streaks[key] = {"count": count + 1, "last_at": time.time()}


def _clarification_streak_reset(key):
    with _clarification_streaks_lock:
        _clarification_streaks.pop(key, None)

# A prediction/anomaly config's SQL query is written by an LLM (or, worse,
# generated on the fly with no human review yet) and can come back unaggregated
# against a large table — seen live: a 1.17M-row full-table pull that hung the
# request indefinitely in the sklearn/pandas processing and the final
# to_dict(orient="records") conversion. Cap rows right after fetch so a bad
# query degrades to a truncated-but-fast answer instead of hanging a worker
# thread; a real analysis is expected to aggregate/filter, not need 1M+ rows.
_MAX_ANALYSIS_ROWS = 20000

# Per-workspace lock guarding the scheduled_questions read-modify-write cycle
# (_get_schedule_records -> mutate in memory -> _save_schedule_records writes the
# WHOLE list back, no per-field atomicity). Without this, two schedules firing
# concurrently in the same workspace — or a fire racing a /stop, resume, delete,
# or the chat inbox poll — is a lost-update race: whichever save happens last
# silently clobbers the other's changes (e.g. a conditional agent's matched_keys
# update, or a chat_inbox notification, vanishing). RLock (not Lock) since some
# callers are nested inside other locked sections of this same module.
_schedule_records_locks = {}
_schedule_records_locks_guard = None   # initialised after Lock is imported below


class _ScheduleRequestError(Exception):
    """Carries an early-return (body, status) out of a schedule-creation
    validation loop so the whole read-modify-write cycle can be wrapped in a
    single `with _get_schedule_records_lock(...):` without re-indenting every
    line of it — a validation failure partway through just raises this instead
    of returning, and the caller turns it back into the usual response tuple."""
    def __init__(self, body, status):
        self.body = body
        self.status = status





# ENV_PATH = ".env"
# load_dotenv(ENV_PATH)
import os
import json
from threading import Lock, RLock

CONFIG_FILE = "feedback_config.json"
_config_lock = Lock()
_stuck_device_log_lock = Lock()
_unpick_log_lock = Lock()
_pending_writes_lock = Lock()
_pending_schedule_clarifications_lock = Lock()
_pending_analysis_confirmations_lock = Lock()
_last_analysis_runs_lock = Lock()
_pending_query_clarifications_lock = Lock()
_clarification_streaks_lock = Lock()
_schedule_records_locks_guard = Lock()


def _get_schedule_records_lock(workspace_id):
    """Lazily creates (once) and returns the RLock for this workspace's
    scheduled_questions read-modify-write cycle. See _schedule_records_locks
    above for why this exists."""
    key = str(workspace_id)
    with _schedule_records_locks_guard:
        lock = _schedule_records_locks.get(key)
        if lock is None:
            lock = RLock()
            _schedule_records_locks[key] = lock
        return lock


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

# Feedback DB connection — every field must come from the environment; no
# hardcoded server/database/username fallbacks (a misconfigured deployment
# should fail loudly, not silently connect to some other real box).
USER_FEEDBACK_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('FEEDBACK_DB_SERVER', '')};"
    f"DATABASE={os.getenv('FEEDBACK_DB_NAME', '')};"
    f"UID={os.getenv('FEEDBACK_DB_USER', '')};"
    f"PWD={os.getenv('FEEDBACK_DB_PASSWORD', '')};"
)


def _ensure_feedback_schema(user_mgmt_config):
    """
    Best-effort, idempotent auto-provisioning for the feedback/user-activity
    database on a fresh deployment — creates the database (if missing) and the
    'users'/'user_feedback' tables (if missing) so a new environment doesn't
    need manual DBA setup before feedback/activity logging works. Never raises:
    on any failure (unconfigured, unreachable, or the SQL login lacking
    CREATE DATABASE rights) this logs a clear warning and lets startup
    continue, the same "never raises" contract _sync_linked_server uses —
    every write against this DB already degrades gracefully (file-fallback
    logging) if the schema still isn't there.
    """
    server = user_mgmt_config.get('server')
    port = user_mgmt_config.get('port')
    database = user_mgmt_config.get('database')
    username = user_mgmt_config.get('username')
    password = user_mgmt_config.get('password')

    if not (server and database and username):
        logger.info("Feedback DB not configured — skipping schema auto-provisioning.", extra={"admin": True})
        return

    server_part = f"{server},{port}" if port else server

    try:
        # CREATE DATABASE cannot run inside a transaction, and the target
        # database may not exist yet — connect to master first, autocommit on.
        master_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server_part};DATABASE=master;UID={username};PWD={password};"
        )
        # A database name can't be a bind parameter — it's an identifier, so it has
        # to be interpolated. Constrain it to a plain identifier first: the value is
        # operator-supplied config rather than user input, but nothing downstream
        # would stop a name containing "]" from closing the brackets and appending
        # its own statement.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", database or ""):
            logger.warning(
                f"Feedback DB schema auto-provisioning skipped: {database!r} is not a plain "
                "identifier (letters, digits and underscore only).",
                extra={"admin": True},
            )
            return

        with pyodbc.connect(master_conn_str, timeout=15, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"IF DB_ID(N'{database}') IS NULL CREATE DATABASE [{database}]")
        logger.info(f"Feedback DB '{database}' confirmed/created.", extra={"admin": True})

        db_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server_part};DATABASE={database};UID={username};PWD={password};"
        )
        with pyodbc.connect(db_conn_str, timeout=15, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                IF OBJECT_ID('dbo.users', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.users (
                        -- UNIQUEIDENTIFIER, not VARCHAR(100): existing deployments
                        -- have this column as uniqueidentifier, and the mismatch is
                        -- what let SQL Server error 8169 ("conversion from a
                        -- character string to uniqueidentifier failed") reach
                        -- production unnoticed — a freshly provisioned VARCHAR
                        -- database accepted the bad value and never reproduced it.
                        -- Every writer already supplies str(uuid.uuid4()).
                        question_id         UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
                        question             NVARCHAR(4000) NULL,
                        sql_query            NVARCHAR(4000) NULL,
                        summary              NVARCHAR(4000) NULL,
                        plot_data            NVARCHAR(4000) NULL,
                        workspace_name       NVARCHAR(255)  NULL,
                        workspace_id         NVARCHAR(100)  NULL,
                        timestamp            DATETIME       NULL,
                        user_role            NVARCHAR(100)  NULL,
                        user_id              NVARCHAR(100)  NULL,
                        detected_language    NVARCHAR(20)   NULL,
                        token_count          INT            NULL,
                        input_tokens         INT            NULL,
                        output_tokens        INT            NULL,
                        cached_input_tokens  INT            NULL,
                        cost_usd             FLOAT          NULL,
                        model_name           NVARCHAR(100)  NULL,
                        parent_question_id   NVARCHAR(100)  NULL
                    )
                END
            """)
            # log_user_activity writes parent_question_id and the history query
            # reads it, but tables created before it existed don't have it — every
            # insert then failed and fell back to user_activity_log_backup.txt.
            cursor.execute("""
                IF COL_LENGTH('dbo.users', 'parent_question_id') IS NULL
                    ALTER TABLE dbo.users ADD parent_question_id NVARCHAR(100) NULL
            """)
            cursor.execute("""
                IF OBJECT_ID('dbo.user_feedback', 'U') IS NULL
                BEGIN
                    CREATE TABLE dbo.user_feedback (
                        id            INT IDENTITY(1,1) PRIMARY KEY,
                        workspace_id  NVARCHAR(100)  NULL,
                        question_id   NVARCHAR(100)  NULL,
                        question      NVARCHAR(4000) NULL,
                        sql           NVARCHAR(4000) NULL,
                        rating        INT            NULL,
                        comment       NVARCHAR(2000) NULL,
                        created_at    DATETIME       NULL,
                        email_sent    BIT            NOT NULL DEFAULT 0
                    )
                END
            """)
        logger.info("Feedback DB tables 'users'/'user_feedback' confirmed/created.", extra={"admin": True})
    except Exception as e:
        logger.warning(
            f"Feedback DB schema auto-provisioning skipped (best-effort): {e}",
            extra={"admin": True},
        )


# USD per 1M tokens: OpenAI standard-tier list prices. One table for every cost
# calculation — billing and the agent-suggestion token counter each used to
# keep their own copy, both well above list price. Keys are matched as the
# longest prefix of the reported model (dated snapshots like
# "gpt-4.1-mini-2025-04-14" resolve to "gpt-4.1-mini"). Re-check against
# https://openai.com/api/pricing when adding a model or if your contract differs.
MODEL_PRICING = {
    "gpt-4.1":      {"input": 2.00,  "cached_input": 0.50,   "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40,  "cached_input": 0.10,   "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10,  "cached_input": 0.025,  "output": 0.40},
    "gpt-4o":       {"input": 2.50,  "cached_input": 1.25,   "output": 10.00},
    "gpt-4o-mini":  {"input": 0.15,  "cached_input": 0.075,  "output": 0.60},
    "gpt-5":        {"input": 1.25,  "cached_input": 0.125,  "output": 10.00},
    "gpt-5-mini":   {"input": 0.25,  "cached_input": 0.025,  "output": 2.00},
    "gpt-5-nano":   {"input": 0.05,  "cached_input": 0.005,  "output": 0.40},
    "gpt-5.1":      {"input": 1.25,  "cached_input": 0.125,  "output": 10.00},
    "o3":           {"input": 2.00,  "cached_input": 0.50,   "output": 8.00},
    "o3-mini":      {"input": 1.10,  "cached_input": 0.55,   "output": 4.40},
    "o4-mini":      {"input": 1.10,  "cached_input": 0.275,  "output": 4.40},
    "o1":           {"input": 15.00, "cached_input": 7.50,   "output": 60.00},
}


def compute_cost_usd(normalized_model, input_tokens, output_tokens, cached_input_tokens=0):
    """Cost of one call. Cached input is billed at its discounted rate, not free;
    an unknown model costs 0 (logged by the caller's model name, not guessed)."""
    price = MODEL_PRICING.get(normalized_model)
    if not price:
        return 0.0
    cached = max(0, min(cached_input_tokens or 0, input_tokens or 0))
    uncached = max(0, (input_tokens or 0) - cached)
    return round(
        uncached / 1_000_000 * price["input"]
        + cached / 1_000_000 * price["cached_input"]
        + (output_tokens or 0) / 1_000_000 * price["output"],
        8,
    )


def session_cookie_settings(env):
    """(Flask config to apply, whether the Teams tab is on without a Secure
    cookie, whether SESSION_COOKIE_SECURE was left unconfigured entirely).

    SESSION_COOKIE_SECURE decides explicitly; unset, it follows TEAMS_TAB_ENABLED.
    See the call site in VannaFlaskApp.__init__ for why the two are separate.
    """
    def _flag(name):
        return str(env.get(name, "")).strip().lower()

    teams_tab_enabled = _flag("TEAMS_TAB_ENABLED") in ("1", "true", "yes")
    secure_env = _flag("SESSION_COOKIE_SECURE")
    secure_unconfigured = secure_env not in ("0", "false", "no", "1", "true", "yes")
    if secure_env in ("0", "false", "no"):
        use_secure = False
    elif secure_env in ("1", "true", "yes"):
        use_secure = True
    else:
        use_secure = teams_tab_enabled

    if use_secure:
        config = {
            "SESSION_COOKIE_SAMESITE": "None",
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_PARTITIONED": True,
        }
    else:
        # SameSite is set explicitly even on the non-Secure path — this used to
        # be left to Flask's own (version-dependent) default, so a Flask
        # upgrade could silently change actual browser behavior here.
        config = {"SESSION_COOKIE_SAMESITE": "Lax"}
    return config, (teams_tab_enabled and not use_secure), (secure_unconfigured and not use_secure)


TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")






# One Vanna instance per workspace, and a proxy standing in for the old
# single shared global — see vn_registry.py. Every existing `vn.<attr>` call
# resolves to the instance for the current caller's workspace.
_vanna_registry = VannaRegistry()
vn = VnRouter(_vanna_registry)


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
        # Every field falls back through the FEEDBACK_DB_* env vars, then to an
        # empty string — never a hardcoded real server/database/username. A
        # deployment with nothing configured must fail loudly, not silently
        # connect to some other real box.
        self.user_mgmt_config = {
            'server': os.environ.get('USER_MGMT_SERVER', os.environ.get('FEEDBACK_DB_SERVER', '')),
            'port': os.environ.get('USER_MGMT_PORT', os.environ.get('FEEDBACK_DB_PORT', '')),
            'database': os.environ.get('USER_MGMT_DATABASE', os.environ.get('FEEDBACK_DB_NAME', '')),
            'username': os.environ.get('USER_MGMT_USERNAME', os.environ.get('FEEDBACK_DB_USER', '')),
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
            f"SERVER={cfg['server']}{',' + cfg['port'] if cfg['port'] else ''};"
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
    def fetch_user_documents_for_user(self, user_id, workspace_id) -> Dict[str, Dict[str, Any]]:
            logger.info(f"fetch_user_documents_for_user", extra={"flow":True})
            if user_id is None or workspace_id is None:
                return {}


            sql = """
            SELECT question_id, question, sql_query, workspace_name, detected_language, parent_question_id
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
                        "detected_language": row[4],
                        "parent_question_id": row[5]
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

    # UPDATED set() for consistent anonymous handling:
    def set(self, id, field, value, user_id: Optional[str] = None, workspace_id: Optional[str] = None):
        logger.info(f"set - {field}", extra={"flow": True})
        uid, wid = self._resolve_user_workspace(user_id, workspace_id)
        
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


    # UPDATED get() method with better error handling:
    def get(self, id, field, user_id: Optional[str] = None, workspace_id: Optional[str] = None):
        global vn

        logger.info(f"get for field: {field}", extra={"flow": True})
        uid, wid = self._resolve_user_workspace(user_id, workspace_id)
        
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

    # UPDATED get_all() to update access times:
    def get_all(self, field_list, user_id: Optional[str] = None, workspace_id: Optional[str] = None) -> list:
        uid, wid = self._resolve_user_workspace(user_id, workspace_id)
        
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

    # UPDATED delete() for consistent handling:
    def delete(self, id, user_id: Optional[str] = None, workspace_id: Optional[str] = None):
        uid, wid = self._resolve_user_workspace(user_id, workspace_id)
        
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
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _csv_safe_value(value):
    """
    Prefixes a leading '=' / '+' / '-' / '@' with a single quote — Excel's own
    "treat as text" escape — so a cell sourced from warehouse data (a customer
    name, address, free-text comment, anything not typed by this app) can
    never be opened as a live formula ("CSV injection"/"formula injection").
    Only touches strings; numbers/dates/None pass through unchanged.
    """
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


def _rows_to_csv(rows):
    if not rows: return None
    out = io.StringIO()
    safe_rows = [{k: _csv_safe_value(v) for k, v in row.items()} for row in rows]
    w = csv.DictWriter(out, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(safe_rows)
    return out.getvalue()

# Send email using SMTP (e.g., Gmail)
def _send_email_smtp(recipients, subject, body, rows, filename, cfg, html=None, inline_images=None, extra_attachments=None):
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
    if html:
        # multipart/related( multipart/alternative(plain, html), inline images by Content-ID )
        from email.mime.image import MIMEImage
        related = MIMEMultipart("related")
        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(body, "plain", "utf-8"))
        alternative.attach(MIMEText(html, "html", "utf-8"))
        related.attach(alternative)
        for cid, data in inline_images or []:
            img = MIMEImage(data, _subtype="png")
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=f"{cid}.png")
            related.attach(img)
        msg.attach(related)
    else:
        msg.attach(MIMEText(body, "plain", "utf-8"))
    for att_name, att_mime, att_data in extra_attachments or []:
        maintype, _, subtype = (att_mime or "application/octet-stream").partition("/")
        extra_part = MIMEBase(maintype, subtype or "octet-stream")
        extra_part.set_payload(att_data)
        encoders.encode_base64(extra_part)
        extra_part.add_header("Content-Disposition", f'attachment; filename="{att_name}"')
        msg.attach(extra_part)

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
def _send_email_outlook_graph(recipients, subject, body, rows, filename, cfg, html=None, inline_images=None, extra_attachments=None):
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

    for cid, data in inline_images or []:
        attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": f"{cid}.png",
            "contentType": "image/png",
            "contentBytes": base64.b64encode(data).decode("utf-8"),
            "isInline": True,
            "contentId": cid,
        })
    for att_name, att_mime, att_data in extra_attachments or []:
        attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": att_name,
            "contentType": att_mime or "application/octet-stream",
            "contentBytes": base64.b64encode(att_data).decode("utf-8"),
        })

    # 3) Build mail payload
    mail = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if html else "Text",
                "content": html if html else body
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
def _send_email(recipients, subject, body, rows, filename, html=None, inline_images=None, extra_attachments=None):
    # html / inline_images [(content_id, png_bytes)] / extra_attachments [(name, mime, bytes)]
    # are optional; every existing caller passes none of them and gets the old plain-text email.
    if not recipients:
        return False

    cfg = load_email_config()

    if not cfg.get("send_email_enabled", True):
        print("Email sending disabled (kill switch)")
        return False

    provider = cfg.get("email_provider", "gmail")

    if provider == "gmail":
        # smtp_server/smtp_port/sender_email/sender_password are flat top-level
        # keys on cfg (set by save_feedback_config) — _send_email_smtp expects
        # them there, not inside the nested cfg["gmail"] sub-object.
        return _send_email_smtp(
            recipients, subject, body, rows, filename, cfg,
            html=html, inline_images=inline_images, extra_attachments=extra_attachments
        )

    if provider == "outlook":
        return _send_email_outlook_graph(
            recipients, subject, body, rows, filename, cfg,
            html=html, inline_images=inline_images, extra_attachments=extra_attachments
        )

    raise ValueError(f"Unsupported email provider: {provider}")

class _OpenAIVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


class _OllamaVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


def _build_bare_vanna():
    """No LLM client and no DB connection — only the ChromaDB side, for
    training-data operations when no workspace is connected."""
    return _OpenAIVanna(config={'allow_llm_to_see_data': 'True'})


def build_vanna_instance(llm_details, db_details, db_details_b=None):
    """Build a connected Vanna instance from a workspace's LLM + DB config.
    Raises ValueError with a user-facing reason for missing/unsupported config."""
    llm_details = llm_details or {}
    model_type = llm_details.get('model_type')
    if model_type == 'openai':
        if not llm_details.get('api_key'):
            logger.warning("API key missing for OpenAI model", extra={"admin": True})
            raise ValueError("API key is required for OpenAI models")
        instance = _OpenAIVanna(config={
            'api_key': llm_details['api_key'],
            'model': llm_details.get('model_name'),
            'allow_llm_to_see_data': True
        })
    elif model_type == 'ollama':
        instance = _OllamaVanna(config={
            'model': llm_details.get('model_name'),
            'allow_llm_to_see_data': True
        })
    else:
        raise ValueError("Unsupported or missing LLM model type — configure an AI provider for this workspace.")

    if not db_details or not all(db_details.get(k) for k in ("serverName", "port", "databaseName", "username", "password")):
        raise ValueError("Incomplete database connection details — configure the workspace DB connection.")

    odbc_conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={db_details['serverName']},{db_details['port']};"
        f"DATABASE={db_details['databaseName']};"
        f"UID={db_details['username']};"
        f"PWD={db_details['password']};"
    )
    logger.info(f"Connecting to MSSQL database {db_details['databaseName']} on {db_details['serverName']}", extra={"admin": True})
    instance.connect_to_mssql(odbc_conn_str=odbc_conn_str)

    # Record primary/secondary DB aliases for cross-DB SQL qualification
    # (see get_sql_prompt). No live connection to the secondary DB — it's
    # reached either via same-instance three-part naming (if both databases
    # share the same server+port) or a linked server (if genuinely separate
    # servers) — get_sql_prompt picks the right form using same_instance.
    # strip(): an alias typed with a stray space ("secondarydb ") never matched
    # the db tags in table_relevance/query_mapping.
    instance.primary_db_alias = (db_details.get("db_alias") or "").strip() or "PRIMARY"
    instance.primary_db_name = db_details.get("databaseName")
    if db_details_b and db_details_b.get("databaseName"):
        instance.secondary_db_alias = (db_details_b.get("db_alias") or "").strip() or "SECONDARY"
        instance.secondary_db_name = db_details_b.get("databaseName")
        instance.same_instance = (
            str(db_details_b.get("serverName") or "").strip().lower()
                == str(db_details.get("serverName") or "").strip().lower()
            and str(db_details_b.get("port") or "").strip()
                == str(db_details.get("port") or "").strip()
        )
    else:
        instance.secondary_db_alias = None
        instance.secondary_db_name = None
        instance.same_instance = False
    return instance


def initialize_vanna_instance(workspace_id, llm_details, db_details, db_details_b=None):
    """Build an instance from explicit details, register it for workspace_id
    and bind it to the current thread/request. Returns {"success", ...}."""
    try:
        instance = build_vanna_instance(llm_details, db_details, db_details_b)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Failed to initialize Vanna: {str(e)}", exc_info=True, extra={"admin": True})
        return {"success": False, "error": f"Failed to initialize Vanna: {str(e)}"}
    _vanna_registry.put(workspace_id, instance)
    vn.bind_instance(instance)
    logger.info(f"Vanna initialized for workspace {workspace_id}", extra={"admin": True})
    return {"success": True, "message": "Vanna initialized successfully."}


_initialize_vanna_instance_module = initialize_vanna_instance
_vanna_registry.configure(bare_factory=_build_bare_vanna)



class VannaFlaskAPI:
    flask_app = None

    def _build_vanna_for_workspace(self, workspace_id):
        """Vanna registry loader: build workspace_id's instance from its saved
        LLM + DB config. Raises ValueError with a user-facing reason."""
        workspace = get_workspace_metadata(self, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        llm_config = json.loads(workspace.get("llm_config") or "{}")
        db_config = json.loads(workspace.get("db_config") or "{}")
        db_config_b = json.loads(workspace.get("db_config_b") or "{}")
        return build_vanna_instance(
            llm_config, db_config, db_config_b if db_config_b.get("databaseName") else None
        )

    def ensure_vanna_initialized(self, workspace_id, refresh=False):
        """Make workspace_id's instance the one `vn` resolves to on this thread —
        for the rest of this request, or for this background job. Reuses the
        cached instance unless refresh=True (config saves invalidate the cache)."""
        instance, err = _vanna_registry.get_or_build(workspace_id, refresh=refresh)
        if instance is None:
            return False, err
        vn.bind_instance(instance)
        self.vn = vn
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
                # API callers (fetch/XHR) can't follow a redirect to an HTML login
                # page — they'd parse it as a broken response. Same rule the
                # access-control layer uses: JSON 401 for them, redirect for pages.
                if _wants_json(request.path):
                    return jsonify({"type": "error", "error": "Authentication required"}), 401
                return redirect(url_for("login"))

            # Put user into kwargs only if not present
            if "user" not in kwargs:
                kwargs["user"] = user

            return f(*args, **kwargs)
        return decorated


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
                    if _wants_json(request.path):  # see requires_auth
                        return jsonify({"type": "error", "error": "Authentication required"}), 401
                    return redirect(url_for("login"))

                # Prefer role from kwargs/session/user
                role = normalize_role(
                    kwargs.get("role") or session.get("role") or getattr(user, "role", None) or user.get("role", None)
                )

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
        cache: Cache = None,
        auth: AuthInterface = None,
        debug=False,
        allow_llm_to_see_data=False,
        chart=True,
    ):
        global vn
        # Defaults are built here, not in the signature: a default argument is
        # evaluated once at import, so merely importing this module started a
        # cache-eviction thread and (for BasicAuth) wrote users into ChromaDB.
        cache = cache if cache is not None else MemoryCache()
        auth = auth if auth is not None else NoAuth()
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

        # login.html/admin.html/superadmin.html/user.html live in a project-root
        # "templates" folder (separate from engine/flask/templates, which holds a
        # different set) — resolved against the working directory, which main.py
        # sets to the project root.
        self.flask_app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "templates"))

        # A request that ensured a specific workspace binds its Vanna instance
        # to the serving thread — Waitress reuses threads, so drop the binding
        # when the request ends rather than leaking it into the next one.
        @self.flask_app.teardown_request
        def _unbind_vanna_instance(_exc):
            vn.unbind_instance()

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

        def _run_performance_configs_and_summarize(configs, question_en, workspace_name):
            """
            Runs one or more admin-curated performance-check configs (see
            match_performance_config / the Performance Checks admin panel),
            merges their results, applies any named-entity filter the
            question implies (see match_entity_filter — e.g. "...in
            Manhattan" when no such entity exists), and summarizes for a
            management audience (see generate_performance_summary).

            Single source of truth for this, shared by the live chat answer,
            "send this" re-runs (_run_analysis_check's "performance" kind),
            and conditional scheduled-agent polls — one metric or several
            merged are handled identically everywhere, so a question like
            "what's our storage occupancy?" and "how is the warehouse
            performing?" get the same bulleted, percentage-led treatment
            instead of the single-metric case looking like a different,
            less-finished feature.

            Returns (summary_text_with_any_disclaimer, combined_df, ran_types)
            — combined_df is None (and summary_text a plain explanation) if
            nothing could be run.
            """
            combined_df = None
            ran_types = []
            for cfg in configs:
                is_safe, reason = vn.is_select_only_sql(cfg.get("sql_query") or "")
                if not is_safe:
                    logger.warning(f"Performance config '{cfg.get('type')}' failed SQL validation: {reason}")
                    continue
                try:
                    cfg_df = vn.run_sql(cfg["sql_query"])
                except Exception as run_exc:
                    logger.warning(f"Performance config '{cfg.get('type')}' failed to run: {run_exc}")
                    continue
                if cfg_df is None or cfg_df.empty:
                    continue
                # SQL Server's DECIMAL columns (every _pct column these
                # configs compute) come back from the DB driver as Python
                # decimal.Decimal objects, which pandas stores as dtype
                # "object" — invisible to pd.api.types.is_numeric_dtype().
                # Found live: this silently dropped every percentage column
                # from match_entity_filter's and extract_numeric_condition's
                # numeric-column detection, so a condition like "occupied
                # location PERCENTAGE above 90" could only ever match a raw
                # count column instead, a wrong-but-plausible-looking answer.
                # pd.to_numeric safely converts Decimal (and numeric strings)
                # to float; a genuinely non-numeric column (warehouse_id)
                # raises and is left untouched (errors="ignore" was removed
                # in pandas 3.x — "invalid error value specified" — so a
                # plain try/except is the only way to do this that works
                # across pandas versions).
                for col in cfg_df.columns:
                    if cfg_df[col].dtype == object:
                        try:
                            cfg_df[col] = pd.to_numeric(cfg_df[col])
                        except (ValueError, TypeError):
                            pass
                ran_types.append(cfg.get("type"))
                if combined_df is None:
                    combined_df = cfg_df
                elif "warehouse_id" in cfg_df.columns and "warehouse_id" in combined_df.columns:
                    combined_df = combined_df.merge(
                        cfg_df, on="warehouse_id", how="outer", suffixes=("", f"_{cfg.get('type')}")
                    )
                else:
                    combined_df = pd.concat([combined_df, cfg_df], axis=1)

            if combined_df is None or combined_df.empty:
                return "None of the matched performance checks returned any data.", None, []

            entity_filter = {"mentioned": False}
            try:
                entity_filter = vn.match_entity_filter(question_en, combined_df)
            except Exception as ef_exc:
                logger.warning(f"match_entity_filter failed: {ef_exc}")

            disclaimer = ""
            if entity_filter.get("mentioned") and not entity_filter.get("column"):
                term = entity_filter.get("mentioned_term") or "that"
                disclaimer = (
                    f"I don't have anything in this data specifically labeled '{term}' — "
                    "here's the full breakdown in case one of these matches what you mean:\n\n"
                )
            if entity_filter.get("column"):
                combined_df = combined_df[
                    combined_df[entity_filter["column"]].astype(str) == entity_filter["matched_value"]
                ]

            try:
                summary_text = vn.generate_performance_summary(question=question_en, df=combined_df)
            except Exception as summary_exc:
                logger.warning(f"Performance summary generation failed: {summary_exc}")
                summary_text = None
            if not summary_text:
                summary_text = combined_df.to_string(index=False)

            return disclaimer + summary_text, combined_df, ran_types

        self._run_performance_configs_and_summarize = _run_performance_configs_and_summarize

        def _match_performance_configs(question_en, ws_meta, workspace):
            """
            Matches question_en against this workspace's admin-curated
            performance configs and returns the matched config list, or None
            if nothing matches (or a trained SQL example already covers the
            question — generate_sql should answer those directly rather than
            a performance config stepping in).

            Shared by _try_match_performance_config (chat/route_message,
            which immediately runs+summarizes the match) and
            _handle_schedule_message (which only needs the config list to
            store on the schedule record — _run_analysis_check runs it fresh
            at every fire, same as a remembered "send this" check).
            """
            try:
                enabled_performance = [
                    p for p in json.loads((ws_meta or {}).get("performance", "[]"))
                    if p.get("enabled", True)
                ]
                if not enabled_performance or _is_trained_question(question_en, workspace):
                    return None
                perf_configs = [
                    {"type": p.get("type"), "name": p.get("name") or p.get("type"), "description": p.get("description")}
                    for p in enabled_performance
                ]
                perf_match = vn.match_performance_config(question_en, perf_configs)
                matched_types = perf_match.get("types") or []
                matched_perf_cfgs = [p for p in enabled_performance if p.get("type") in matched_types]
                return matched_perf_cfgs or None
            except Exception as perf_exc:
                logger.warning(f"Performance config matching failed: {perf_exc}")
                return None

        self._match_performance_configs = _match_performance_configs

        def _try_match_performance_config(question_en, workspace, ws_meta, workspace_id, username):
            """
            Checks whether one of this workspace's admin-curated performance
            configs answers question_en outright, runs it, and remembers the
            run for a later "send this"/conditional-alert reference — the
            same unconditional check _handle_query_message always ran before
            generate_sql, pulled out so route_message can run it too.

            Found live: a management question like "are operational
            exceptions trending up or down this month?" — a question a saved
            performance config (exception_trend) answers exactly — was
            classified "prediction" by classify_message_route (it reads
            trend/abnormal-pattern language the same way "any unusual
            inventory movement" does) and went straight to
            _handle_prediction_message, which never looks at performance
            configs at all. It ran its own ad-hoc anomaly analysis against an
            unrelated table ("error message frequency") instead of the
            validated, on-point answer that already existed. Performance
            configs are admin-validated and more specific than an ad-hoc
            LLM-built check, so they should win whenever they match, even on
            a message classify_message_route guessed was "prediction".

            Returns the summary text (str) if a configured check answered
            it, else None — None means "let the normal pipeline handle this",
            never an error.
            """
            try:
                matched_perf_cfgs = _match_performance_configs(question_en, ws_meta, workspace)
                if not matched_perf_cfgs:
                    return None

                summary_text, result_df, ran_types = _run_performance_configs_and_summarize(
                    matched_perf_cfgs, question_en, workspace
                )
                if result_df is None:
                    # Matched config(s) found, but none returned data — let
                    # the caller fall through to its normal pipeline instead
                    # of dead-ending on an empty result.
                    return None

                logger.info(f"Answered performance question '{question_en}' using: {ran_types}")
                if workspace_id and username:
                    _clarification_streak_reset(f"{workspace_id}:{username}")
                    self._remember_analysis_run(
                        f"{workspace_id}:{username}", question_en, "performance", matched_perf_cfgs,
                    )
                return summary_text
            except Exception as perf_exc:
                logger.warning(f"Performance config matching failed: {perf_exc}")
                return None

        self._try_match_performance_config = _try_match_performance_config

        def _try_match_analysis_methodology(question_en, ws_meta, workspace_id, username):
            """
            Counterpart to _try_match_performance_config, for the methodology
            short-circuit's prediction/anomaly branch (see
            generate_analysis_methodology_explanation) — never used to answer
            a question with actual data, only to find which saved check a
            methodology question is asking about. Same priority as the
            performance branch: a check the question explicitly names wins;
            otherwise falls back to whichever one last answered this user.

            Returns (kind, full_config_dict) or (None, None).
            """
            try:
                predictions = [p for p in json.loads((ws_meta or {}).get("predictions", "[]")) if p.get("enabled", True)]
                anomalies = [a for a in json.loads((ws_meta or {}).get("anomalies", "[]")) if a.get("enabled", True)]
                if predictions or anomalies:
                    def _sql_tables(sql):
                        return ", ".join(dict.fromkeys(
                            m.split(".")[-1].strip("[]")
                            for m in re.findall(r"\b(?:FROM|JOIN)\s+([\w.\[\]]+)", sql or "", re.I)
                        )) or None
                    configs = (
                        [{"kind": "prediction", "type": p.get("type"), "name": p.get("prediction_name") or p.get("type"),
                          "table": p.get("table_names") or _sql_tables(p.get("sql_query")),
                          "predicts": (p.get("parameters") or {}).get("target"),
                          "justification": p.get("justification")} for p in predictions]
                        + [{"kind": "anomaly", "type": a.get("type"), "name": a.get("anomaly_name") or a.get("type"),
                            "table": a.get("table_name") or _sql_tables(a.get("sql_query")),
                            "justification": a.get("justification")} for a in anomalies]
                    )
                    # tables=[] — this only ever reads the matched-existing-
                    # check branch of match_analysis_config, which doesn't
                    # need a real table list; skips the extra DB round trip
                    # match_analysis_config's "suggest a new table" branch
                    # would otherwise need.
                    match = vn.match_analysis_config(question_en, configs, [])
                    if match.get("matched"):
                        kind = match["kind"]
                        cfg_type = match["type"]
                        full_cfg = next(
                            (c for c in (predictions if kind == "prediction" else anomalies) if c.get("type") == cfg_type),
                            None,
                        )
                        if full_cfg:
                            return kind, full_cfg
                if workspace_id and username:
                    last_run = self._last_prediction_or_anomaly_run_for(workspace_id, username)
                    if last_run:
                        return last_run["kind"], last_run["config"]
            except Exception as analysis_match_exc:
                logger.warning(f"Analysis methodology matching failed: {analysis_match_exc}")
            return None, None

        self._try_match_analysis_methodology = _try_match_analysis_methodology

        def _handle_query_message(question_raw, previous_sql, workspace, ctx=None, parent_question_id=None):
            """
            Core RAG/text-to-SQL pipeline: validates input, translates, routes read
            vs write (vn.classify_intent), generates SQL, caches, and logs
            billing/activity. Shared by generate_sql (GET, question/sql/workspace
            query params), route_message (POST, natural-language dispatch) and
            run_chat_turn (Teams) so every entry point runs identical logic.

            ctx (ChatContext) supplies identity for callers with no Flask session;
            when None, identity comes from the session as before.

            parent_question_id, when the caller identifies this as a follow-up, is
            stored on the new cache entry so the FAQ/history sidebar can group a
            follow-up under the question it followed up on instead of listing it
            as an independent entry.

            Returns (body_dict, status_code).
            """
            session_user_id = ctx.user_id if ctx else session.get('user_id')
            session_username = ctx.username if ctx else session.get('username', None)
            cache_scope = {"user_id": ctx.user_id, "workspace_id": ctx.workspace_id} if ctx else {}
            # ────────────────────────────────────────────────
            #  Validation
            # ────────────────────────────────────────────────
            if not question_raw:
                return {"type": "error", "error": "No question provided"}, 400

            if not workspace:
                return {"type": "error", "error": "No workspace provided"}, 400

            # ────────────────────────────────────────────────
            # Ensure vn is ready before touching it. vn is a lazily-
            # initialized, process-wide global (not per-session) — found live:
            # both this function and route_message's classifier branch could
            # crash with AttributeError: 'NoneType' object has no attribute
            # '...' when reached before any prior request in this process had
            # initialized vn for this workspace (e.g. a fresh process, or a
            # client that never calls connect-vanna first). _handle_schedule_
            # message/_handle_prediction_message already self-protect this
            # way; this was the one shared entry point missing it.
            # ────────────────────────────────────────────────
            # Teams/voice callers pass ctx and run on a worker thread with no
            # Flask request — touching flask.session there raises "Working
            # outside of request context". Take their workspace from ctx.
            workspace_id_for_init = ctx.workspace_id if ctx else flask.session.get("workspace_id")
            if not workspace_id_for_init and not ctx:
                # No workspace bound in this session yet (fresh login, or a client
                # that never called /connect-vanna). This used to fall through to a
                # process-global default — whichever workspace anyone connected last
                # — and, with none, to an unconfigured instance that crashed with
                # "'_OpenAIVanna' object has no attribute 'client'". Resolve the
                # workspace this request names instead, and remember it.
                workspace_id_for_init = self._workspace_id_from_ref(workspace)
                if not workspace_id_for_init:
                    return {"type": "error", "error": f"Workspace '{workspace}' was not found."}, 404
                user_for_check = self.auth.get_user(flask.request) or {"role": session.get("role")}
                if not self._user_can_access_workspace(user_for_check, workspace_id_for_init):
                    return {"type": "error", "error": "You don't have access to this workspace"}, 403
                session["workspace_id"] = workspace_id_for_init
            if workspace_id_for_init:
                initialized, init_err = self.ensure_vanna_initialized(workspace_id_for_init)
                if not initialized:
                    return {"type": "error", "error": init_err}, 400

            # The trained dataset lives in a collection named after the workspace
            # NAME. Some callers (the prediction pipeline's fallback) pass the
            # workspace ID instead — that searched an empty collection, so every
            # question there missed the dataset and ended in a clarifying question.
            #
            # get_workspace_metadata itself only looks up by ID (workspace_
            # collection.get(ids=[...])) — but the real chat UI's generate_sql
            # call passes the workspace NAME (see its "workspace: workspaceName"
            # fetch param), not the ID. Found live: that silently returned
            # ws_meta=None, which meant performance-config matching below always
            # saw an empty config list and never even attempted a match — a
            # question like "how is warehouse performing" fell all the way
            # through to generate_sql's own clarification loop instead, with no
            # error or warning anywhere to point at why. _workspace_id_from_ref
            # already resolves an id/name/display_name ambiguously for other
            # callers in this file; reuse it here so ws_meta resolves correctly
            # regardless of which form the caller passed.
            ws_meta = get_workspace_metadata(self, self._workspace_id_from_ref(workspace) or workspace)
            if ws_meta and ws_meta.get("name"):
                workspace = ws_meta["name"]

            # ────────────────────────────────────────────────
            # Resume a pending query clarification, if one is open for this
            # user — treat this message as the answer, merged with the
            # original question that generate_sql couldn't ground, rather than
            # a brand-new query on its own (a bare "the pick table" reply
            # wouldn't make sense as a standalone question). Same pattern as
            # _pending_schedule_clarifications: keyed by workspace_id+username,
            # popped (not just peeked) here since this is the actual consumer.
            # ────────────────────────────────────────────────
            clarification_workspace_id = workspace_id_for_init
            clarification_username = session_username  # ctx-aware, see top of function
            query_clarification_attempts = 0
            if clarification_workspace_id and clarification_username:
                clarification_key = f"{clarification_workspace_id}:{clarification_username}"
                with _pending_query_clarifications_lock:
                    pending_clarification = _pending_query_clarifications.pop(clarification_key, None)

                # Defense in depth, mirrors the discard added to
                # _handle_schedule_message/_handle_prediction_message: reaching
                # this function means the message is being treated as a query,
                # so any stale schedule/prediction clarification for this same
                # user shouldn't be left to silently merge into a later message
                # if some future caller ever reaches _handle_query_message
                # without going through the usual pending-state-aware routing
                # in route_message/classify_message_route_endpoint.
                with _pending_schedule_clarifications_lock:
                    _pending_schedule_clarifications.pop(clarification_key, None)
                with _pending_analysis_confirmations_lock:
                    _pending_analysis_confirmations.pop(clarification_key, None)

                # A complete trained question isn't an answer to the clarifying
                # question — it's a new question. Merging it produced things like
                # "what does that means?? Which items are most likely to run out…",
                # which then matched nothing in the dataset.
                # (Short replies like "Warehouse ATH1" are still answers to the
                # clarifying question, even if some trained entry is that bare text.)
                reply = clean_question(question_raw)
                if pending_clarification and len(reply.split()) >= 4 and _is_trained_question(reply, workspace):
                    pending_clarification = None
                # The trained-question check above only catches one narrow case
                # of "this is actually a new question" — any other unrelated
                # fresh question (not verbatim-trained) used to get silently
                # glued onto the stale clarification's text instead. Ask the
                # same question an LLM can answer cheaply: does this reply read
                # like an answer to the specific clarifying question that was
                # asked, or like its own new question? Only checked when the
                # narrow check above didn't already decide, and defaults to
                # "treat as an answer" (False) on any doubt — this can only
                # discard a stale clarification, never create new merge risk.
                if pending_clarification:
                    try:
                        if vn.is_fresh_topic_change(reply, pending_clarification.get("clarifying_question") or ""):
                            logger.info(
                                f"Discarding stale query clarification — '{reply}' reads as a new "
                                f"question, not an answer to '{pending_clarification.get('clarifying_question')}'"
                            )
                            pending_clarification = None
                    except Exception as topic_exc:
                        logger.warning(f"is_fresh_topic_change check failed: {topic_exc}")

                if pending_clarification and time.time() - pending_clarification.get("created_at", 0) <= _PENDING_QUERY_CLARIFICATION_TTL_SECONDS:
                    question_raw = f"{pending_clarification['raw_text']} {question_raw}".strip()
                    query_clarification_attempts = pending_clarification.get("attempts", 0)

                    # The original question was classified "query" before it
                    # ever reached here, but the clarifying reply can reveal
                    # the true intent was actually scheduling/prediction all
                    # along — e.g. "...and notify me whenever that happens"
                    # only shows up in the answer, not the original question.
                    # Re-check the MERGED text rather than blindly trusting
                    # the earlier classification; if it's changed, hand off
                    # to the right pipeline instead of forcing an unrelated
                    # data question through this one.
                    try:
                        reclassified_route = vn.classify_message_route(question_raw)
                    except Exception as reclassify_exc:
                        logger.warning(f"Query clarification re-classification failed: {reclassify_exc}")
                        reclassified_route = "query"
                    if reclassified_route == "schedule":
                        return self._handle_schedule_message(
                            clarification_workspace_id, question_raw, None, clarification_username, previous_sql
                        )
                    if reclassified_route == "prediction":
                        return self._handle_prediction_message(
                            clarification_workspace_id, question_raw, clarification_username
                        )

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
                workspace_id_for_write = ctx.workspace_id if ctx else flask.session.get("workspace_id")
                if not workspace_id_for_write:
                    return {
                        "type": "error",
                        "error": "Workspace is not fully connected (no workspace_id in session) — cannot stage a write.",
                    }, 400
                body, status = self._stage_pending_write(vn, workspace, workspace_id_for_write, question_en, original_question)
                if status == 200 and body.get("type") == "write_confirmation":
                    body["detected_language"] = detected_language
                    body["was_translated"] = was_translated
                    body["translated_question"] = question_en if was_translated else None
                return body, status

            # ────────────────────────────────────────────────
            # Methodology short-circuit: "how is this calculated?" / "what's
            # the formula?" / "how does this work?" following a performance,
            # prediction, or anomaly answer is a question ABOUT the check,
            # not a new data question — generate_sql has no table/column to
            # ground a question like that in and either hallucinates SQL or
            # asks a narrowing clarifying question forever. Checked before
            # the performance-check short-circuit below (a methodology
            # question about "revenue month over month" would otherwise
            # itself get matched as if it were asking for that metric's
            # current value). Prefers a check the question itself names
            # (e.g. "how is revenue month over month calculated?" always
            # explains THAT metric, even right after a different one was
            # just answered); only falls back to whichever check answered
            # this user's last question when the question itself names
            # nothing — a bare "how is it calculated?"/"what's the formula
            # for this?" always means "that answer I'm looking at". Tries
            # performance configs first, then prediction/anomaly — a
            # methodology question has no way to say which KIND of check it
            # means, so whichever actually matches (by name, or by being the
            # last thing answered) wins; it's extremely unlikely for both to
            # match the same question at once.
            # ────────────────────────────────────────────────
            try:
                if _METHODOLOGY_CUE.search(question_en):
                    methodology_configs = None
                    enabled_performance = [
                        p for p in json.loads((ws_meta or {}).get("performance", "[]"))
                        if p.get("enabled", True)
                    ]
                    if enabled_performance:
                        perf_configs = [
                            {"type": p.get("type"), "name": p.get("name") or p.get("type"), "description": p.get("description")}
                            for p in enabled_performance
                        ]
                        perf_match = vn.match_performance_config(question_en, perf_configs)
                        matched_types = perf_match.get("types") or []
                        methodology_configs = [p for p in enabled_performance if p.get("type") in matched_types] or None
                    if not methodology_configs and clarification_workspace_id and clarification_username:
                        last_perf_run = self._last_performance_run_for(
                            clarification_workspace_id, clarification_username
                        )
                        if last_perf_run:
                            methodology_configs = last_perf_run.get("config")
                    if methodology_configs:
                        explanation = vn.generate_performance_methodology_explanation(question_en, methodology_configs)
                        if explanation:
                            return {
                                "type": "text",
                                "text": explanation,
                                "detected_language": detected_language,
                                "was_translated": was_translated,
                            }, 200

                    analysis_kind, analysis_config = _try_match_analysis_methodology(
                        question_en, ws_meta, clarification_workspace_id, clarification_username
                    )
                    if analysis_config:
                        explanation = vn.generate_analysis_methodology_explanation(
                            question_en, analysis_kind, analysis_config
                        )
                        if explanation:
                            return {
                                "type": "text",
                                "text": explanation,
                                "detected_language": detected_language,
                                "was_translated": was_translated,
                            }, 200
            except Exception as methodology_exc:
                logger.warning(f"Methodology explanation failed: {methodology_exc}")

            # ────────────────────────────────────────────────
            # Performance-check short-circuit: before deciding follow-up vs.
            # fresh SQL generation, see if one of this workspace's admin-
            # curated performance configs (validated SQL for a specific
            # operational metric — e.g. warehouse storage occupancy, order
            # cycle time, order execution time) already answers this question
            # outright. Checked unconditionally on the new message text
            # (question_en), REGARDLESS of whether a previous_sql/follow-up
            # context is attached — a self-contained, answerable question
            # like "how is the warehouse performing?" means exactly the same
            # thing whether it's the first message of a chat or the tenth.
            # Originally this only ran in the fresh-question branch, on the
            # theory that a wrong match mid-conversation would be worse than
            # no match — but in practice, most real chat messages DO carry a
            # previous_sql (any ongoing thread), so performance questions
            # almost never reached this check at all, and instead fell into
            # generate_sql's follow-up interpretation, which has no concept
            # of these configs and just kept asking narrowing clarifying
            # questions indefinitely. match_performance_config is still an
            # LLM judgment call with "no match" as its safe default, so this
            # can only skip SQL generation — never block or alter it.
            # ────────────────────────────────────────────────
            perf_summary_text = _try_match_performance_config(
                question_en, workspace, ws_meta, clarification_workspace_id, clarification_username
            )
            if perf_summary_text is not None:
                return {
                    "type": "text",
                    "text": perf_summary_text,
                    "detected_language": detected_language,
                    "was_translated": was_translated,
                }, 200

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
            self.cache.set(id=cache_id, field="question",           value=original_question, **cache_scope)
            self.cache.set(id=cache_id, field="translated_question", value=question_en, **cache_scope)
            self.cache.set(id=cache_id, field="sql",                value=sql, **cache_scope)
            self.cache.set(id=cache_id, field="workspace",          value=workspace, **cache_scope)
            self.cache.set(id=cache_id, field="detected_language",  value=detected_language, **cache_scope)
            self.cache.set(id=cache_id, field="was_translated",     value=was_translated, **cache_scope)
            self.cache.set(id=cache_id, field="parent_question_id", value=parent_question_id, **cache_scope)

            # Token-related fields (for UI/debugging/billing)
            self.cache.set(id=cache_id, field="token_total",   value=total_tokens, **cache_scope)
            self.cache.set(id=cache_id, field="token_input",   value=input_tokens, **cache_scope)
            self.cache.set(id=cache_id, field="token_output",  value=output_tokens, **cache_scope)
            self.cache.set(id=cache_id, field="model_name",    value=model_name, **cache_scope)

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
                    user_id=session_user_id
                )
            except Exception as e:
                logger.error(f"Billing calculation failed: {e}")

            try:
                self.log_user_activity(
                    question_id=cache_id,
                    question=original_question,
                    sql_query=sql,
                    workspace_name=workspace,
                    user_role=session_username,
                    user_id=session_user_id,
                    token_count=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_name=model_name,
                    cached_input_tokens=0,
                    cost_usd=cost_usd,
                    detected_language=detected_language,
                    workspace_id=ctx.workspace_id if ctx else None,
                    parent_question_id=parent_question_id,
                )
            except Exception as e:
                logger.error(f"User activity logging failed: {e}")

            # ────────────────────────────────────────────────
            # Response
            # ────────────────────────────────────────────────
            # Extract SQL text if tuple
            sql_text = sql[0] if isinstance(sql, tuple) else sql

            response_type = "sql" if vn.is_sql_valid(sql=sql_text) else "text"

            # A real answer resets the clarification streak — the user got
            # unstuck, so the next dead-end (if any) starts counting fresh
            # rather than inheriting frustration from an unrelated earlier
            # exchange.
            if response_type == "sql" and clarification_workspace_id and clarification_username:
                _clarification_streak_reset(f"{clarification_workspace_id}:{clarification_username}")

            # generate_sql's own anti-hallucination guard fires when no trained
            # example/documentation covers this question's shape — sometimes as
            # the exact literal "Insufficient data for query.", but observed
            # live to also come back as a free-form explanation ("the database
            # tables listed do not appear to contain X data..."), so match on
            # "any non-SQL text response" rather than that one exact phrase.
            # The one explicit exclusion is the DDL/DML write-refusal message —
            # a write request slipping past classify_intent isn't a data-
            # availability problem a clarifying question could fix. Previously
            # every other case just dead-ended the user with the raw text. Try
            # turning it into a clarifying question instead (same idea as the
            # scheduling clarification flow), capped at a few attempts so a
            # genuinely untrained area of the schema doesn't loop forever.
            _write_refusal_text = "cannot perform ddl or dml functions"
            if response_type == "text" and (sql_text or "").strip().rstrip(".").lower() != _write_refusal_text:
                streak_key = (
                    f"{clarification_workspace_id}:{clarification_username}"
                    if clarification_workspace_id and clarification_username else None
                )
                # The per-thread attempt counter (query_clarification_attempts)
                # only increments when a reply is judged to MERGE with the
                # prior clarification — is_fresh_topic_change can misjudge a
                # loosely-phrased real answer as "a new question", which
                # resets that counter to 0 and would otherwise let the cap be
                # bypassed one misjudged reset at a time. The streak count
                # below is the backstop: it counts every clarifying question
                # asked in a row regardless of how each reply was classified,
                # and is only cleared by an actual answer (see the "sql"
                # reset above) — so the conversation can't loop forever even
                # if the merge/fresh judgment keeps getting it wrong.
                streak_count = _clarification_streak_count(streak_key) if streak_key else 0
                if (
                    clarification_workspace_id and clarification_username
                    and query_clarification_attempts < _MAX_QUERY_CLARIFICATION_ATTEMPTS
                    and streak_count < _MAX_CLARIFICATION_STREAK
                ):
                    try:
                        tables_df = vn.run_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
                        real_tables = tables_df["TABLE_NAME"].tolist() if tables_df is not None and not tables_df.empty else []
                    except Exception as table_exc:
                        logger.warning(f"Could not list tables for query clarification: {table_exc}")
                        real_tables = []
                    suggestion = vn.suggest_query_clarification(question_en, real_tables)
                    if suggestion.get("ask_user") and suggestion.get("clarifying_question"):
                        with _pending_query_clarifications_lock:
                            _pending_query_clarifications[streak_key] = {
                                "raw_text": original_question,
                                "created_at": time.time(),
                                "attempts": query_clarification_attempts + 1,
                                "clarifying_question": suggestion["clarifying_question"],
                            }
                        _clarification_streak_increment(streak_key)
                        sql_text = suggestion["clarifying_question"]
                    else:
                        sql_text = suggestion.get("reason") or sql_text
                elif clarification_workspace_id and clarification_username and (
                    query_clarification_attempts >= _MAX_QUERY_CLARIFICATION_ATTEMPTS
                    or streak_count >= _MAX_CLARIFICATION_STREAK
                ):
                    # Already asked enough times without landing on something
                    # answerable — stop looping and say so plainly instead of
                    # surfacing generate_sql's raw (sometimes blunt, sometimes
                    # LLM-variable) refusal text.
                    sql_text = (
                        "I still don't have enough to answer that — it may need a trained "
                        "example added, or try rephrasing the whole question in one message."
                    )

            return {
                "type":               response_type,
                "id":                 cache_id,
                "text":               sql_text,   # send only SQL string
                "original_question":  original_question,
                "detected_language":  detected_language,
                "was_translated":     was_translated,
                "translated_question": question_en if was_translated else None,
            }, 200

        # Exposed on self so VannaFlaskApp's __init__ (a separate closure/scope
        # from this one, though it runs on the same instance via super().__init__)
        # can reach it — e.g. route_message's NL "query" branch.
        self._handle_query_message = _handle_query_message

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
            parent_question_id = flask.request.args.get("parent_question_id")
            body, status = _handle_query_message(question_raw, previous_sql, workspace, parent_question_id=parent_question_id)
            return jsonify(body), status

        # Published so routes defined in VannaFlaskApp.__init__ (route_message,
        # run_chat_turn) can reach it — a nested function here isn't in their scope.
        self._handle_query_message = _handle_query_message

        @self.flask_app.route("/api/get_user/<username>", methods=["GET"])
        @self.requires_auth
        def get_user_config(user: any, username: str):
            """
            Get the user configuration including enabled agent scenarios.
            """
            # Security check: ensure requesting user matches username or is admin.
            # Compare against ADMIN_ROLES — a bare != "admin" also locked out
            # superadmins, who outrank admins everywhere else in the app.
            current_user = user # from requires_auth
            if (current_user.get("username") != username
                    and str(current_user.get("role") or "").lower() not in ADMIN_ROLES):
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

            # Bind this request to the target workspace's instance.
            if target_workspace_id:
                success, err = self.ensure_vanna_initialized(target_workspace_id)
                if not success:
                    logger.error(f"run_agent_query: Auto-init failed: {err}")
                    return jsonify({"type": "error", "error": f"Auto-init failed: {err}"}), 500
            elif not getattr(vn, "run_sql_is_set", False):
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

            # --- Bind this request to the target workspace's instance ---
            if target_workspace_id:
                self.ensure_vanna_initialized(target_workspace_id)

            if not getattr(vn, "run_sql_is_set", False):
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



        @self.flask_app.route("/api/v0/orderfulfillmenttimeprediction", methods=["GET"])
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
                # If chart_instructions is not set then attempt to retrieve the spec from the cache.
                # The cached value here used to be raw Python ("plotly code") executed via exec() —
                # now it's a JSON-encoded chart spec (see generate_chart_spec/render_chart_figure).
                # A stale/legacy cache entry (or one written by the saved-"function" flow a few
                # lines up, which still populates this same field) that isn't valid JSON just
                # yields spec=None, which render_chart_figure already treats as "no spec" and
                # falls back to its dtype-based heuristic — never passed anywhere it could be exec'd.
                if chart_instructions is None or len(chart_instructions) == 0:
                    cached_spec = self.cache.get(id=id, field="plotly_code")
                    try:
                        spec = json.loads(cached_spec) if cached_spec else None
                    except (TypeError, ValueError):
                        spec = None
                else:
                    question = f"{question}. When generating the chart, use these special instructions: {chart_instructions}"
                    spec = vn.generate_chart_spec(
                        question=question,
                        sql=sql,
                        df_metadata=f"Running df.dtypes gives:\n {df.dtypes}",
                    )
                    self.cache.set(id=id, field="plotly_code", value=json.dumps(spec))

                fig = vn.render_chart_figure(spec=spec, df=df, dark_mode=False)
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
        @self.requires_role(list(ADMIN_ROLES))  # on the route too, not only in access_control's list
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
            body = flask.request.get_json(silent=True) or {}
            id = body.get("id")

            if id is None:
                return jsonify({"type": "error", "error": "No id provided"})

            # SQL/doc entries live in the per-workspace collection, so without a
            # workspace the vector store can only fail them (-ddl is global).
            # Take it from the body, else the caller's session workspace (stored
            # as an id; the collection is keyed by the workspace's name).
            workspace = body.get("workspace") or body.get("workspace_name")
            if not workspace and session.get("workspace_id"):
                meta = get_workspace_metadata(self, session["workspace_id"]) or {}
                workspace = meta.get("name")
            if workspace and not self._user_can_access_workspace(user, workspace):
                return jsonify({"type": "error", "error": "You don't have access to this workspace"}), 403

            if vn.remove_training_data(id=id, workspace=workspace):
                return jsonify({"success": True})
            else:
                return jsonify(
                    {"type": "error", "error": "Couldn't remove training data"}
                )

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

            cost_usd = compute_cost_usd(normalized_model, input_tokens, output_tokens, cached_input_tokens)

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
                    "questions": cache.get_all(field_list=["question", "parent_question_id"]),
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






        @self.flask_app.route('/api/v0/save_feedback', methods=['POST'])
        def save_feedback():
            data = request.json or {}
            workspace_id = data.get('workspace_id')
            question_id = data.get('question_id')
            question = data.get('question')
            sql = data.get('sql', '')  # allow empty
            rating = data.get('rating')
            comment = data.get('comment')

            if not workspace_id or not question_id:
                return jsonify({"status": "error", "error": "workspace_id and question_id are required"}), 400

            question_id = _canonical_question_id(question_id)
            if question_id is None:
                return jsonify({"status": "error", "error": "question_id is not a valid id"}), 400

            if rating is not None:
                try:
                    rating = int(rating)
                except (TypeError, ValueError):
                    return jsonify({"status": "error", "error": f"rating must be a number, got {rating!r}"}), 400

            try:
                conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
            except Exception as e:
                logger.error(f"save_feedback: DB connection failed: {e}")
                return jsonify({"status": "error", "error": "Could not reach the feedback database"}), 500

            try:
                cursor = conn.cursor()
                # Fix: Use SELECT COUNT(*) to check existence, include all keys
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
                return jsonify({"status": "success"})
            except Exception as e:
                logger.error(f"save_feedback: failed for workspace_id={workspace_id} question_id={question_id}: {e}")
                return jsonify({"status": "error", "error": "Could not save feedback"}), 500
            finally:
                conn.close()
            


        @self.flask_app.route('/api/v0/get_feedback', methods=['GET'])
        def get_feedback():
            workspace_id = request.args.get('workspace_id')
            question_id  = request.args.get('question_id')
            sql          = request.args.get('sql')

            if not workspace_id or not question_id:
                return jsonify({"exists": False})

            question_id = _canonical_question_id(question_id)
            if question_id is None:
                return jsonify({"exists": False})

            try:
                conn = pyodbc.connect(USER_FEEDBACK_CONNECTION_STRING, timeout=30)
            except Exception as e:
                logger.error(f"get_feedback: DB connection failed: {e}")
                return jsonify({"exists": False, "error": "Could not reach the feedback database"}), 500

            try:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT TOP 1 rating, comment
                    FROM user_feedback
                    WHERE workspace_id = ? AND question_id = ?
                    ORDER BY created_at DESC
                """, workspace_id, question_id)

                row = cursor.fetchone()

                if row:
                    return jsonify({
                        "exists": True,
                        "rating": row.rating,
                        "comment": row.comment
                    })

                return jsonify({"exists": False})
            except Exception as e:
                logger.error(f"get_feedback: failed for workspace_id={workspace_id} question_id={question_id}: {e}")
                return jsonify({"exists": False, "error": "Could not read feedback"}), 500
            finally:
                conn.close()
        


        @self.flask_app.route("/api/get_feedback_config", methods=["GET"])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def get_feedback_config(user=None):
            cfg = load_email_config()
            # Never echo the credential back to the client once it's saved —
            # the UI only needs to know one is already set, not its value.
            safe_cfg = dict(cfg)
            if safe_cfg.get("sender_password"):
                safe_cfg["sender_password"] = ""
                safe_cfg["sender_password_set"] = True
            if isinstance(safe_cfg.get("gmail"), dict) and safe_cfg["gmail"].get("sender_password"):
                safe_cfg["gmail"] = {**safe_cfg["gmail"], "sender_password": ""}
            if isinstance(safe_cfg.get("outlook"), dict) and safe_cfg["outlook"].get("client_secret"):
                safe_cfg["outlook"] = {**safe_cfg["outlook"], "client_secret": ""}
                safe_cfg["outlook_client_secret_set"] = True

            return jsonify(safe_cfg)


        @self.flask_app.route("/api/save_feedback_config", methods=["POST"])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def save_feedback_config(user=None):

            data = request.json or {}
            existing_cfg = load_email_config()

            cfg = {}

            # Common settings — preserve whatever was already saved for fields this
            # form doesn't send (e.g. the unrelated Low Rating Feedback Alert fields),
            # rather than silently resetting them to defaults on every sender save.
            cfg.update({
                "email_provider": data.get("email_provider", existing_cfg.get("email_provider", "gmail")),
                "recipients": data.get("recipients", existing_cfg.get("recipients", [])),
                "cc": data.get("cc", existing_cfg.get("cc", "")),
                "subject": data.get("subject", existing_cfg.get("subject", "Low Rating Feedback Alert")),
                "body": data.get("body", existing_cfg.get("body", "")),
                "include_sent": data.get("include_sent", existing_cfg.get("include_sent", False)),
                "email_interval": int(data.get("email_interval", existing_cfg.get("email_interval", 120))),
                "send_email_enabled": data.get("send_email_enabled", existing_cfg.get("send_email_enabled", True))
            })

            # Gmail
            if data.get("email_provider") == "gmail":

                gmail_cfg = data.get("gmail", {}) or {}
                existing_gmail = existing_cfg.get("gmail", {}) or {}

                # Merge top-level sender fields if provided by frontend
                top_sender = {
                    "sender_email": data.get("sender_email"),
                    "sender_password": data.get("sender_password")
                }

                # Prefer nested gmail config, fall back to top-level fields
                gmail_cfg = {**existing_gmail, **gmail_cfg, **{k: v for k, v in top_sender.items() if v}}
                # A blank password field means "leave the saved one alone" (the client
                # never receives the real password back, so it can't resubmit it) —
                # only overwrite when a new, non-empty value was actually typed.
                if not gmail_cfg.get("sender_password"):
                    gmail_cfg["sender_password"] = existing_gmail.get("sender_password", "")

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

                outlook_cfg = data.get("outlook", {}) or {}
                existing_outlook = existing_cfg.get("outlook", {}) or {}
                outlook_cfg = {**existing_outlook, **outlook_cfg}
                # Same "blank means unchanged" rule as the Gmail app password above.
                if not outlook_cfg.get("client_secret"):
                    outlook_cfg["client_secret"] = existing_outlook.get("client_secret", "")

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


        @self.flask_app.route("/api/test_feedback_email", methods=["POST"])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def test_feedback_email(user=None):
            """Send a small real test email using whatever sender config is
            currently saved — the same "verify it actually works" role Test
            Connection plays for the DB config, since a bad password/app-password
            otherwise only surfaces the first time a scheduled agent tries to fire."""
            data = request.json or {}
            test_recipient = (data.get("test_recipient") or "").strip()
            if not test_recipient or "@" not in test_recipient:
                return jsonify({"success": False, "message": "A valid test recipient address is required."}), 400

            try:
                sent = _send_email(
                    [test_recipient],
                    "Test email — chat_engine sender configuration",
                    "This is a test email confirming the scheduled-agent sender account is working.",
                    [],
                    "test.csv",
                )
                if not sent:
                    return jsonify({"success": False, "message": "Send was skipped — email sending is currently disabled (kill switch), or no provider config is saved."}), 400
                return jsonify({"success": True, "message": f"Test email sent to {test_recipient}."})
            except Exception as e:
                logger.exception(f"Test email send failed: {e}")
                return jsonify({"success": False, "message": f"Send failed: {e}"}), 500












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
        cache: Cache = None,  # MemoryCache() — built below, see VannaFlaskAPI.__init__
        auth: AuthInterface = None,  # BasicAuth()
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
        cache = cache if cache is not None else MemoryCache()
        auth = auth if auth is not None else BasicAuth()
        super().__init__(cache, auth, debug, allow_llm_to_see_data, chart, **kwargs)
         

        # A fixed key is required: a random per-process key silently logs every
        # user out on each restart and breaks sessions across a Teams tab reload.
        secret_key = os.environ.get("FLASK_SECRET_KEY", "")
        if not secret_key:
            # Name the exact file: this aborts startup, so the operator sees no
            # login page at all and has nothing else to go on.
            _env_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
            )
            raise RuntimeError(
                f"FLASK_SECRET_KEY is not set — the server cannot start. Add a long random "
                f"value to {_env_file}, e.g.\n"
                "    python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        self.flask_app.secret_key = secret_key

        # Inside a Teams tab the app runs in a third-party iframe: the session
        # cookie must be SameSite=None; Secure (HTTPS only) to be sent at all,
        # and Partitioned so browsers that block third-party cookies keep it.
        #
        # But a Secure cookie is dropped outright over plain HTTP, and this was
        # keyed only off TEAMS_TAB_ENABLED — so turning the tab on silently broke
        # login for anyone reaching the app at http://127.0.0.1:<port>: the POST
        # validated, the cookie never persisted, and the next request bounced
        # straight back to the login page with no error shown. SESSION_COOKIE_SECURE
        # now decides it explicitly, defaulting to the tab setting so HTTPS
        # deployments are unchanged.
        _cookie_config, _tab_without_secure, _secure_unconfigured = session_cookie_settings(os.environ)
        self.flask_app.config.update(_cookie_config)
        if _tab_without_secure:
            # Both can't be satisfied at once: the tab needs SameSite=None;Secure,
            # plain HTTP can't carry it. Say so rather than leaving the tab to fail
            # later with an unexplained empty session.
            logger.warning(
                "TEAMS_TAB_ENABLED is on but SESSION_COOKIE_SECURE is disabled — password "
                "login works over plain HTTP, but the Teams tab will not hold a session. "
                "Drop SESSION_COOKIE_SECURE from .env (and use the HTTPS URL) before using the tab.",
                extra={"admin": True},
            )
        if _secure_unconfigured:
            # Fine for local/plain-HTTP testing (this is the default so that keeps
            # working with zero config) but a real deployment reachable over the
            # network should opt in explicitly — nudge rather than silently leave
            # the session cookie sniffable over an unencrypted connection.
            logger.warning(
                "Session cookie is not marked Secure (SESSION_COOKIE_SECURE is not set "
                "in .env). Set SESSION_COOKIE_SECURE=true for any deployment reachable "
                "over the network, not just localhost.",
                extra={"admin": True},
            )

        install_access_control(self.flask_app)

        # Initialize ChromaDB client and collections
        self.client = chromadb.PersistentClient(path="admin_store")
        self.config_collection = self.client.get_or_create_collection(name="LLM_config")
        self.db_collection = self.client.get_or_create_collection(name="DB_connections")
        self.workspace_collection = self.client.get_or_create_collection(name="Workspaces") # New collection for workspaces
        self.users_collection = self.client.get_or_create_collection(name="users")
        _vanna_registry.configure(loader=self._build_vanna_for_workspace)
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"),model_name="text-embedding-3-large")
        self.sop_collection = self.client.get_or_create_collection(name="SOP_documents", embedding_function=openai_ef) #sop agents

        # Every field falls back through the FEEDBACK_DB_* env vars, then to an
        # empty string — never a hardcoded real server/database/username. A
        # deployment with nothing configured must fail loudly, not silently
        # connect to some other real box.
        self.user_mgmt_config = {
            'server': os.environ.get('USER_MGMT_SERVER', os.environ.get('FEEDBACK_DB_SERVER', '')),
            'port': os.environ.get('USER_MGMT_PORT', os.environ.get('FEEDBACK_DB_PORT', '')),
            'database': os.environ.get('USER_MGMT_DATABASE', os.environ.get('FEEDBACK_DB_NAME', '')),
            'username': os.environ.get('USER_MGMT_USERNAME', os.environ.get('FEEDBACK_DB_USER', '')),
            'password': os.environ.get('USER_MGMT_PASSWORD', os.environ.get('FEEDBACK_DB_PASSWORD', ''))
        }
        _ensure_feedback_schema(self.user_mgmt_config)
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
                        # Accept a leading CTE ("WITH ... SELECT ...", optionally
                        # semicolon-prefixed) as well as a plain SELECT — a CTE query
                        # is still read-only, just doesn't start with the literal
                        # word "select".
                        if not re.match(r"^\s*;?\s*(select|with)\b", sql, re.IGNORECASE):
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

        # ============= Scheduled (slash-command) read-only agents =============
        # A "/"-prefixed chat message can create a recurring or deferred SELECT-only
        # query that delivers its results later via chat or email, instead of
        # answering once synchronously. Records live in workspace metadata
        # ("scheduled_questions", a JSON list) and each enabled one gets a live
        # APScheduler job here. Because BackgroundScheduler's default jobstore is
        # in-memory, every enabled record is re-registered on every process start
        # (see the rebuild loop below) — the persisted record is the source of
        # truth, the scheduler's job registry is a derived cache.
        import json  # __init__ has a later local `import json` (elsewhere in this
                      # method) that would otherwise shadow the module-level import
                      # for this entire method and make the rebuild loop below fail
                      # with UnboundLocalError, since it runs before that later line.
        DEFAULT_SCHEDULE_TIMEZONE = os.environ.get("SCHEDULE_DEFAULT_TIMEZONE", "Asia/Kolkata")
        MIN_SCHEDULE_INTERVAL_SECONDS = 300
        MAX_ENABLED_SCHEDULES_PER_USER = 10

        def _build_schedule_trigger(schedule):
            tz = schedule.get("timezone") or DEFAULT_SCHEDULE_TIMEZONE
            schedule_type = schedule.get("type")
            if schedule_type == "date":
                run_at = datetime.fromisoformat(schedule["run_at"]).replace(tzinfo=ZoneInfo(tz))
                now = datetime.now(ZoneInfo(tz))
                if run_at <= now:
                    # A "run right now" request's run_at is captured before the
                    # extraction LLM call — by the time this actually registers
                    # the job (after that round-trip), the timestamp is already
                    # stale, and APScheduler silently drops a DateTrigger job
                    # whose fire time has already passed by more than its misfire
                    # grace period, without ever running it. Clamp forward a few
                    # seconds so "send this now" reliably still fires.
                    run_at = now + timedelta(seconds=5)
                return DateTrigger(run_date=run_at, timezone=tz)
            if schedule_type in ("interval", "conditional"):
                # A conditional agent polls on a plain interval too — the only
                # difference is how the result is interpreted at fire time
                # (see _run_scheduled_question), not how it's scheduled.
                return IntervalTrigger(seconds=int(schedule["seconds"]), timezone=tz)
            if schedule_type == "cron":
                cron_fields = {
                    k: v for k, v in schedule.items()
                    if k in ("year", "month", "day", "week", "day_of_week", "hour", "minute", "second")
                }
                return CronTrigger(timezone=tz, **cron_fields)
            raise ValueError(f"No live trigger for schedule type: {schedule_type!r}")

        def _describe_schedule(schedule):
            schedule_type = schedule.get("type")
            tz = schedule.get("timezone") or DEFAULT_SCHEDULE_TIMEZONE
            if schedule_type == "date":
                return f"once, at {schedule.get('run_at')} ({tz})"
            if schedule_type == "interval":
                return f"every {schedule.get('seconds')} second(s)"
            if schedule_type == "conditional":
                return f"checking every {schedule.get('seconds')}s whether: {schedule.get('condition_text', '')}"
            if schedule_type == "cron":
                parts = [
                    f"{k}={v}" for k, v in schedule.items()
                    if k in ("year", "month", "day", "week", "day_of_week", "hour", "minute", "second")
                ]
                return f"on a schedule ({', '.join(parts)}) ({tz})"
            return "on an unrecognized schedule"

        def _is_no_training_example(sql):
            """
            True when generate_sql() didn't fail on anything broken — the LLM's own
            anti-hallucination rule made it return the literal text "Insufficient
            data for query." because no trained example covers the tables/columns
            this question needs. Most commonly this means nobody has trained a
            Question→SQL example for that shape of question yet; it says nothing
            about whether the underlying data itself exists.
            """
            text = (sql or "").strip()
            return text.rstrip(".").lower() == "insufficient data for query"

        def _explain_invalid_sql(sql):
            """
            Turns a non-SELECT `sql` value from generate_sql() into a clear reason
            instead of the old generic "not a valid SELECT statement." `sql` here
            is usually not garbage — generate_sql() itself substitutes a plain-English
            reason when it internally rejects a malformed OPENQUERY literal or an
            out-of-scope table.
            """
            text = (sql or "").strip()
            if not text:
                return "the model did not return a query"
            if _is_no_training_example(text):
                return (
                    "no trained example covers this kind of question yet — ask your "
                    "admin to add a Question→SQL training example for it"
                )
            return text[:300]

        def _status_suffix(r):
            status = r.get("last_status")
            condition_suffix = ""
            if r.get("schedule", {}).get("type") == "conditional":
                keys = r.get("matched_keys")
                condition_suffix = " — currently: not yet checked" if keys is None else f" — currently: {len(keys)} matching"
            if status == "ok":
                return f" — last run OK ({r.get('run_count', 0)}x){condition_suffix}"
            if status in ("error", "rejected"):
                return f" — last run FAILED: {r.get('last_error') or 'unknown error'}{condition_suffix}"
            return f" — not yet run{condition_suffix}"

        def _scheduled_email_body(content):
            """Wraps a scheduled-agent email's actual content with a proper
            greeting/closing — chat_inbox delivery uses the bare `content` as-is,
            this wrapper is only for the email channel."""
            return (
                "Hello,\n\n"
                f"{content}\n\n"
                "Thank you for using Tychons WI — this report was generated automatically "
                "by an AI-powered reporting agent, so please verify any figures before "
                "acting on them.\n\n"
                "Regards,\n"
                "Tychons WI"
            )

        # Same palette/table-based layout as the Warehouse Performance Agent's
        # report emails (engine/warehouse_perf/exec_report.py) so every email
        # this app sends looks like it came from one product, not several.
        _SCHED_INK, _SCHED_INK_2, _SCHED_INK_3, _SCHED_LINE, _SCHED_BG = (
            "#1a1a19", "#52514e", "#76756f", "#e7e6e2", "#f5f5f3"
        )

        def _scheduled_email_html(kind_label, question, status_label, status_colour, status_icon, main_html, schedule_desc, question_label="You asked"):
            """
            Styled HTML counterpart to _scheduled_email_body: table-based, inline
            styles only, 640px, no scripts/external resources, so it renders
            consistently across email clients and still reads fine if images/CSS
            are stripped. Sent as the "html" alternative alongside the plain-text
            body (the source of truth for Teams delivery and for clients that
            can't render HTML) — never the only copy of the content.

            `question` and `schedule_desc` are escaped here; `main_html` is
            caller-built markup (already escaped internally) so it can include
            paragraphs/line breaks instead of being flattened to one block of text.
            """
            e = html_escape_lib.escape
            return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head><body style="margin:0;padding:0;background:{_SCHED_BG}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_SCHED_BG}"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;background:#ffffff;border:1px solid {_SCHED_LINE};border-radius:8px;font-family:Segoe UI,Arial,sans-serif">
<tr><td style="padding:20px 24px 8px"><div style="font-size:12px;color:{_SCHED_INK_3};text-transform:uppercase;letter-spacing:.06em">{e(kind_label)} &middot; Tychons WI</div></td></tr>
<tr><td style="padding:6px 24px 14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:6px solid {status_colour};background:#fafaf8;border-radius:4px"><tr><td style="padding:12px 16px">
<div style="font-size:13px;font-weight:700;color:{_SCHED_INK}">{status_icon} {e(status_label)}</div></td></tr></table></td></tr>
<tr><td style="padding:0 24px 6px"><div style="font-size:12px;font-weight:700;color:{_SCHED_INK_3};text-transform:uppercase;letter-spacing:.04em">{e(question_label)}</div>
<div style="font-size:15px;color:{_SCHED_INK};margin-top:4px;padding:10px 14px;background:#fafaf8;border:1px solid {_SCHED_LINE};border-radius:4px;font-style:italic">&ldquo;{e(question)}&rdquo;</div></td></tr>
<tr><td style="padding:14px 24px 0;font-size:14px;color:{_SCHED_INK};line-height:1.55">{main_html}</td></tr>
<tr><td style="padding:20px 24px 22px"><div style="border-top:1px solid {_SCHED_LINE};padding-top:12px;font-size:12px;color:{_SCHED_INK_3};line-height:1.5">
&#9432; This report was generated automatically by an AI-powered reporting agent — please verify any figures before acting on them.<br>
Runs {e(schedule_desc)}.</div></td></tr>
<tr><td style="padding:0 24px 22px;font-size:13px;color:{_SCHED_INK_2}">Regards,<br>Tychons WI</td></tr>
</table></td></tr></table></body></html>"""

        def _scheduled_email_filename(schedule_id):
            # Date/time leads so files sort and scan chronologically in an inbox or
            # download folder; schedule_id stays as a suffix for traceability back
            # to the specific agent that generated it.
            return f"{_dt.now():%Y-%m-%d_%H-%M-%S}_{schedule_id}.csv"

        def _condition_row_key(row):
            """Stable identity for one row of a conditional agent's match query, used
            to diff which specific records are newly matching across polls (not just
            whether the condition is non-empty overall — see extract_schedule_request's
            conditional prompt block, which requires the first selected column to be a
            stable per-record identifier). Returns None for an empty/falsy row."""
            if not row:
                return None
            return str(next(iter(row.values())))

        def _get_schedule_records(workspace_id):
            """Returns (workspace_metadata_dict, records_list) or (None, None) if the workspace doesn't exist."""
            existing = self.workspace_collection.get(ids=[str(workspace_id)])
            if not existing or not existing.get("metadatas"):
                return None, None
            metadata = existing["metadatas"][0]
            records = json.loads(metadata.get("scheduled_questions", "[]"))
            return metadata, records

        def _save_schedule_records(workspace_id, metadata, records):
            metadata["scheduled_questions"] = json.dumps(records)
            self.workspace_collection.update(
                ids=[str(workspace_id)],
                metadatas=[metadata],
                documents=[f"Workspace: {metadata.get('name', workspace_id)}"],
            )

        def _deliver_to_teams(record, text, rows=None):
            """Push a scheduled agent's result into the Teams conversation it was
            created from. No chat-inbox fallback on failure — see the "unassigned"
            handling in _deliver/_deliver_condition_matches/_fail for why that
            silent-drop mechanism was removed; a failed Teams send is just logged,
            same as an unassigned agent's result."""
            sender = getattr(self, "teams_proactive_sender", None)
            if sender is None:
                logger.warning(f"Scheduled question {record.get('schedule_id')}: Teams delivery unavailable (bot not running).")
                return
            try:
                if not sender(record["teams_aad_id"], text, rows):
                    logger.warning(f"Scheduled question {record.get('schedule_id')}: Teams delivery failed.")
            except Exception as teams_exc:
                logger.exception(f"Scheduled question {record.get('schedule_id')}: Teams delivery failed: {teams_exc}")

        def _run_scheduled_question(workspace_id, schedule_id):
            # Thin locking wrapper — see _get_schedule_records_lock: holds the
            # per-workspace lock for this fire's entire read-modify-write cycle so
            # it can't lose an update racing another fire, a /stop, or the chat
            # poll in the same workspace. The actual logic is unchanged below.
            with _get_schedule_records_lock(workspace_id):
                _run_scheduled_question_locked(workspace_id, schedule_id)

        def _run_scheduled_question_locked(workspace_id, schedule_id):
            global vn
            try:
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return  # workspace was deleted — nothing to do; cleaned up on next restart's rebuild
                record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                if not record or not record.get("enabled"):
                    return

                # "every other <weekday>": the cron trigger fires every week — this
                # gate silently skips the off weeks, counted from the anchor fire time.
                schedule = record.get("schedule", {})
                if schedule.get("fortnight_anchor") and record.get("fortnight_anchor_ts"):
                    weeks_elapsed = int((time.time() - record["fortnight_anchor_ts"]) / 604800)
                    if weeks_elapsed % 2 != 0:
                        return

                def _fail(status, error):
                    record["last_status"] = status
                    record["last_error"] = error
                    if schedule.get("type") == "date":
                        # A one-time schedule only ever gets one attempt — DateTrigger
                        # auto-removes itself from the scheduler whether the fire
                        # succeeded or not, so the persisted record must match that
                        # rather than staying "enabled" forever with no live job behind it.
                        record["enabled"] = False

                    # The user explicitly asked for this to be sent — a failure
                    # recorded only in backend state, with the recipient never told
                    # anything arrived (or didn't), isn't good enough. Best-effort
                    # deliver a short failure notice through the same channel they
                    # were expecting the real result on.
                    failure_note = f"Scheduled request \"{record.get('display_question', '')}\" failed: {error}"
                    try:
                        if record.get("channel") == "email" and record.get("email_recipients"):
                            _send_email(
                                record["email_recipients"],
                                f"[Scheduled - FAILED] {record.get('display_question', '')}",
                                _scheduled_email_body(failure_note),
                                [],
                                _scheduled_email_filename(schedule_id),
                            )
                        elif record.get("channel") == "teams" and record.get("teams_aad_id"):
                            _deliver_to_teams(record, failure_note)
                        else:
                            # Unassigned — the failure is already recorded in
                            # last_status/last_error, visible in the Scheduled
                            # Agents admin panel. No chat-inbox fallback (see
                            # _deliver above for why).
                            logger.info(f"Scheduled question {schedule_id}: no recipient assigned yet — failure notice not delivered.")
                    except Exception as notify_exc:
                        logger.exception(f"Scheduled question {schedule_id} failure-notice delivery also failed: {notify_exc}")

                    _save_schedule_records(workspace_id, metadata, records)

                ok, err = self.ensure_vanna_initialized(workspace_id)
                if not ok:
                    return _fail("error", err)

                # Full read-only gate chain, run fresh on every single fire — never
                # reuse SQL generated at an earlier fire (or at creation), since
                # generate_sql can bake in absolute dates ("last week" etc.) that
                # must re-resolve against "now" at fire time, not creation time.
                if vn.classify_intent(record["question_en"]) == "write":
                    try:
                        scheduled_agents_scheduler.remove_job(schedule_id)
                    except JobLookupError:
                        pass
                    record["enabled"] = False
                    return _fail("rejected", "Re-classified as a write request at fire time — agent disabled.")

                # "Send this" after a prediction/anomaly/performance answer:
                # re-run the check that produced it (it has no SQL to
                # regenerate) and mail its summary. A performance check
                # scheduled CONDITIONALLY (analysis.condition_rule set — see
                # _handle_schedule_message's extract_numeric_condition
                # wiring) is handled separately below: only notify when a
                # NEW row starts satisfying the rule, same new-match diffing
                # a plain-SQL conditional schedule already uses (matched_keys
                # / _condition_row_key), rather than delivering every poll.
                analysis = record.get("analysis")
                if (
                    analysis and analysis.get("config")
                    and (analysis.get("kind") or "prediction") == "performance"
                    and analysis.get("condition_rule")
                    and schedule.get("type") == "conditional"
                ):
                    configs = analysis["config"] if isinstance(analysis["config"], list) else [analysis["config"]]
                    try:
                        _text, result_df, _types = self._run_performance_configs_and_summarize(
                            configs, record["question_en"], record["workspace_name"]
                        )
                    except Exception as run_exc:
                        return _fail("error", f"The check failed to run: {run_exc}")
                    if result_df is None:
                        return _fail("error", "The check returned no data this cycle.")

                    condition_rule = analysis["condition_rule"]
                    is_safe, reason = _is_safe_eval_rule(condition_rule, list(result_df.columns))
                    if not is_safe:
                        return _fail("error", f"Saved condition is no longer valid: {reason}")
                    try:
                        mask = result_df.eval(condition_rule)
                    except Exception as eval_exc:
                        return _fail("error", f"Condition evaluation failed: {eval_exc}")

                    matching_rows = result_df[mask].to_dict(orient="records")
                    key_to_row = {}
                    for row in matching_rows:
                        key = _condition_row_key(row)
                        if key is not None:
                            key_to_row.setdefault(key, row)
                    current_keys = set(key_to_row)
                    previous_keys = set(record.get("matched_keys") or [])
                    new_keys = current_keys - previous_keys
                    record["matched_keys"] = sorted(current_keys)
                    record["last_condition_state"] = bool(current_keys)

                    if new_keys:
                        new_rows = [key_to_row[k] for k in sorted(new_keys)]
                        try:
                            alert_summary = vn.generate_performance_summary(
                                question=record["question_en"], df=pd.DataFrame(new_rows)
                            )
                        except Exception:
                            alert_summary = None
                        e = html_escape_lib.escape
                        subject = f"[Alert] {record['display_question']}"
                        base_line = (
                            f"{len(new_rows)} new record(s) now match: {analysis.get('condition_text', condition_rule)} "
                            f"({len(current_keys)} matching in total)."
                        )
                        body = f"{alert_summary}\n\n{base_line}" if alert_summary else base_line
                        main_html = (
                            (f"<p style=\"margin:0 0 10px\">{e(alert_summary)}</p>" if alert_summary else "")
                            + f"<p style=\"margin:0\">{len(new_rows)} new record(s) now match "
                              f"({len(current_keys)} matching in total) — attached as CSV.</p>"
                        )
                        if record.get("channel") == "email" and record.get("email_recipients"):
                            try:
                                _send_email(
                                    record["email_recipients"], subject, _scheduled_email_body(body), new_rows,
                                    _scheduled_email_filename(schedule_id),
                                    html=_scheduled_email_html(
                                        "Scheduled Alert", record["display_question"], "New match(es) found",
                                        "#c98500", "&#9888;", main_html, _describe_schedule(record.get("schedule") or {}),
                                        question_label="Watching for",
                                    ),
                                )
                            except Exception as email_exc:
                                logger.exception(f"Scheduled question {schedule_id} email delivery failed: {email_exc}")
                        elif record.get("channel") == "teams" and record.get("teams_aad_id"):
                            _deliver_to_teams(record, body, new_rows)
                        else:
                            logger.info(f"Scheduled question {schedule_id}: no recipient assigned yet — match not delivered.")

                    record["last_status"] = "ok"
                    record["last_error"] = None
                    record["last_run_at"] = time.time()
                    record["run_count"] = record.get("run_count", 0) + 1
                    _save_schedule_records(workspace_id, metadata, records)
                    return

                if analysis and analysis.get("config"):
                    reply_text, rows = self._run_analysis_check(
                        workspace_id, analysis.get("kind") or "prediction", analysis["config"],
                        record["question_en"], record["workspace_name"],
                    )
                    if reply_text is None:
                        return _fail("error", f"The check failed to run: {rows}")
                    e = html_escape_lib.escape
                    body = f"You asked: {record['display_question']}\n\n{reply_text}"
                    if rows:
                        body += f"\n\n({len(rows)} row(s) attached as CSV.)"
                    main_html = "".join(
                        f"<p style=\"margin:0 0 10px\">{e(part)}</p>" for part in reply_text.split("\n\n") if part.strip()
                    )
                    if record.get("channel") == "email" and record.get("email_recipients"):
                        try:
                            _send_email(
                                record["email_recipients"],
                                f"[Scheduled] {record['display_question']}",
                                _scheduled_email_body(body),
                                rows,
                                _scheduled_email_filename(schedule_id),
                                html=_scheduled_email_html(
                                    "Scheduled Report", record["display_question"],
                                    "Answered", "#0ca30c", "&#10003;", main_html,
                                    _describe_schedule(record.get("schedule") or {}),
                                ),
                            )
                        except Exception as email_exc:
                            logger.exception(f"Scheduled question {schedule_id} email delivery failed: {email_exc}")
                    elif record.get("channel") == "teams" and record.get("teams_aad_id"):
                        _deliver_to_teams(record, body, rows)
                    else:
                        logger.info(f"Scheduled question {schedule_id}: no recipient assigned yet — result not delivered.")
                    record["last_status"] = "ok"
                    record["last_error"] = None
                    record["last_run_at"] = time.time()
                    record["run_count"] = record.get("run_count", 0) + 1
                    if schedule.get("type") == "date":
                        record["enabled"] = False
                    _save_schedule_records(workspace_id, metadata, records)
                    return

                # A follow-up question ("show me top 4") is meaningless on its own —
                # resolve it against the SQL it was originally asked against, exactly
                # as the interactive follow-up branch does. .get() keeps agents created
                # before this field existed working (they simply have no context).
                total_tokens = input_tokens = output_tokens = 0
                model_name = "unknown"

                def _generate(**kwargs):
                    # Token counts add up across retries so billing covers every call.
                    nonlocal total_tokens, input_tokens, output_tokens, model_name
                    sql_result = vn.generate_sql(workspace=record["workspace_name"], **kwargs)
                    if isinstance(sql_result, tuple) and len(sql_result) == 5:
                        sql_text, total, inp, out, model_name = sql_result
                    elif isinstance(sql_result, tuple) and len(sql_result) == 2:
                        sql_text, total = sql_result
                        inp = out = 0
                    else:
                        sql_text, total, inp, out = sql_result, 0, 0, 0
                    total_tokens += int(total or 0)
                    input_tokens += int(inp or 0)
                    output_tokens += int(out or 0)
                    return str(sql_text)

                context_sql = record.get("context_sql")
                if context_sql:
                    sql = _generate(
                        question=context_sql,                  # previous context
                        followup_sql=record["question_en"],    # the follow-up itself
                    )
                else:
                    sql = _generate(question=record["question_en"])

                # "Send this by mail" right after a chat answer stores that answer's
                # SQL as context. When the question was already self-contained, the
                # follow-up prompt (question + whole previous SQL) skews retrieval
                # toward unrelated tables, and the model answers "Insufficient data
                # for query." even though the chat answered the same question fine.
                # Retry it on its own, then fall back to the SQL the user was shown.
                if context_sql and not vn.is_sql_valid(sql):
                    logger.warning(
                        f"Scheduled question {schedule_id}: follow-up generation failed "
                        f"({sql[:120]!r}) — retrying as a standalone question."
                    )
                    sql = _generate(question=record["question_en"])
                    if not vn.is_sql_valid(sql) and vn.is_sql_valid(context_sql):
                        logger.warning(
                            f"Scheduled question {schedule_id}: standalone generation failed too — "
                            f"running the SQL this agent was created from."
                        )
                        sql = context_sql
                no_training_example = False
                if not vn.is_sql_valid(sql):
                    if not _is_no_training_example(sql):
                        return _fail("rejected", f"Couldn't generate a query for this question: {_explain_invalid_sql(sql)}")
                    # No trained example covers this question — that's a training-data
                    # gap, not evidence the underlying data doesn't exist, but from the
                    # recipient's side it reads the same as "nothing found," and firing
                    # a FAILED alert every single time for a question that may never
                    # get better training data isn't useful. Deliver as an empty result
                    # instead; the gap itself is still logged server-side to notice.
                    logger.warning(
                        f"Scheduled question {schedule_id} (workspace {workspace_id}): no trained "
                        f"example covers question {record['question_en']!r} — delivering as empty result."
                    )
                    df = None
                    no_training_example = True
                else:
                    ok2, err2 = vn.validate_openquery_literals(sql)
                    if not ok2:
                        return _fail("rejected", err2)
                    ok3, err3 = vn.validate_db_scope(sql)
                    if not ok3:
                        return _fail("rejected", err3)

                    try:
                        df = vn.run_sql(sql)
                    except Exception as run_exc:
                        # A raised exception here (timeout, connection failure, etc.) must
                        # still be recorded — otherwise a real failure looks identical to
                        # "hasn't fired yet" in /list, and an email-channel failure leaves
                        # the user with zero visibility that nothing was ever sent.
                        return _fail("error", f"Query failed: {run_exc}")
                rows = df.to_dict(orient="records") if df is not None and len(df) else []

                def _summarize(sub_df):
                    # Best-effort only — a summarization failure (bad API key,
                    # provider outage, etc.) must never block delivery of the
                    # actual data, so callers fall back to the plain row-count
                    # text when this returns None/empty.
                    try:
                        if sub_df is None or sub_df.empty:
                            return None
                        summary_text, *_ = vn.generate_summary(
                            question=record["question_en"], df=sub_df, sql=sql,
                            workspace=record["workspace_name"],
                        )
                        return summary_text or None
                    except Exception as summary_exc:
                        logger.exception(f"Scheduled question {schedule_id} summary generation failed: {summary_exc}")
                        return None

                def _deliver(rows):
                    summary_text = _summarize(df)
                    e = html_escape_lib.escape
                    # Always lead with the actual question this agent was created to
                    # answer — display_question, never a link/id/last-seen-message —
                    # so every email is self-explanatory on its own, without having to
                    # dig through chat history to know what it's even about.
                    question_line = f"You asked: {record['display_question']}"
                    if not rows:
                        if no_training_example:
                            # Not "no data" — the question itself couldn't be understood
                            # well enough to even run (no trained example covers it). A
                            # vague/under-specified question looks identical to "nothing
                            # found" to an unsuspecting recipient unless this is spelled
                            # out, and the fix (rephrase) is different from "wait for
                            # data to show up."
                            status_label, status_colour, status_icon = "Needs a clearer question", "#c98500", "&#9888;"
                            explain = (
                                "I wasn't able to understand this well enough to answer it — "
                                "try recreating this agent with a more specific question (name "
                                "the exact data, table, or condition you want checked)."
                            )
                            body = f"{question_line}\n\n{explain}"
                            main_html = f"<p style=\"margin:0\">{e(explain)}</p>"
                        else:
                            # A genuinely executed, valid query that just found nothing this
                            # run — distinct wording from the case above so a recurring
                            # agent's "nothing to report this time" doesn't read as a failure.
                            status_label, status_colour, status_icon = "No Records Found", "#76756f", "&#9675;"
                            no_data_text = "No records currently match this request."
                            body = f"{question_line}\n\n{no_data_text}"
                            main_html = f"<p style=\"margin:0\">{no_data_text}</p>"
                    elif summary_text:
                        status_label, status_colour, status_icon = "Answered", "#0ca30c", "&#10003;"
                        body = f"{question_line}\n\n{summary_text}\n\n({len(rows)} row(s) attached as CSV.)"
                        main_html = (
                            f"<p style=\"margin:0 0 10px\">{e(summary_text)}</p>"
                            f"<p style=\"margin:0;color:{_SCHED_INK_3};font-size:13px\">{len(rows)} row(s) attached as CSV.</p>"
                        )
                    else:
                        status_label, status_colour, status_icon = "Answered", "#0ca30c", "&#10003;"
                        body = f"{question_line}\n\n{len(rows)} row(s) found — attached as CSV."
                        main_html = f"<p style=\"margin:0\">{len(rows)} row(s) found — attached as CSV.</p>"
                    if record.get("channel") == "email" and record.get("email_recipients"):
                        try:
                            _send_email(
                                record["email_recipients"],
                                f"[Scheduled] {record['display_question']}",
                                _scheduled_email_body(body),
                                rows,
                                _scheduled_email_filename(schedule_id),
                                html=_scheduled_email_html(
                                    "Scheduled Report", record["display_question"],
                                    status_label, status_colour, status_icon, main_html,
                                    _describe_schedule(record.get("schedule") or {}),
                                ),
                            )
                        except Exception as email_exc:
                            logger.exception(f"Scheduled question {schedule_id} email delivery failed: {email_exc}")
                    elif record.get("channel") == "teams" and record.get("teams_aad_id"):
                        _deliver_to_teams(record, body, rows)
                    else:
                        # Unassigned (no recipient yet) — the check still runs and
                        # last_status/last_run_at still update below, but nothing
                        # is sent anywhere. Chat delivery isn't a supported ongoing
                        # channel: it used to silently drop into the owner's chat
                        # inbox here, which looked like a broken/unassigned agent
                        # (because it was) and wasn't reliably seen anyway — the
                        # inbox only drains while that owner happens to have the
                        # chat page open. An admin assigns a real recipient from
                        # the Scheduled Agents panel; nothing fires until then.
                        logger.info(f"Scheduled question {schedule_id}: no recipient assigned yet — result not delivered.")

                def _deliver_condition_matches(new_rows, total_matching):
                    e = html_escape_lib.escape
                    subject = f"[Alert] {record['display_question']}"
                    base_line = (
                        f"{len(new_rows)} new record(s) now match: {record['display_question']} "
                        f"({total_matching} matching in total)."
                    )
                    summary_text = _summarize(pd.DataFrame(new_rows))
                    body = f"{summary_text}\n\n{base_line}" if summary_text else base_line
                    main_html = (
                        (f"<p style=\"margin:0 0 10px\">{e(summary_text)}</p>" if summary_text else "")
                        + f"<p style=\"margin:0\">{len(new_rows)} new record(s) now match "
                          f"({total_matching} matching in total) — attached as CSV.</p>"
                    )
                    if record.get("channel") == "email" and record.get("email_recipients"):
                        try:
                            _send_email(
                                record["email_recipients"],
                                subject,
                                _scheduled_email_body(body),
                                new_rows,
                                _scheduled_email_filename(schedule_id),
                                html=_scheduled_email_html(
                                    "Scheduled Alert", record["display_question"],
                                    "New match(es) found", "#c98500", "&#9888;", main_html,
                                    _describe_schedule(record.get("schedule") or {}),
                                    question_label="Watching for",
                                ),
                            )
                        except Exception as email_exc:
                            logger.exception(f"Scheduled question {schedule_id} email delivery failed: {email_exc}")
                    elif record.get("channel") == "teams" and record.get("teams_aad_id"):
                        _deliver_to_teams(record, body, new_rows)
                    else:
                        # Unassigned — see the matching comment in _deliver above.
                        # matched_keys/last_condition_state still get tracked below
                        # regardless, so nothing is missed once a recipient is
                        # assigned — only the notification itself is withheld.
                        logger.info(f"Scheduled question {schedule_id}: no recipient assigned yet — match not delivered.")

                if schedule.get("type") == "conditional" and no_training_example:
                    # The query couldn't even be generated this cycle (training-data
                    # gap, not a real "nothing matches" result) — rows is a fake empty
                    # set, not a real check. Leave matched_keys/last_condition_state
                    # untouched so a transient training-data gap can never be mistaken
                    # for "everything stopped matching," which would silently discard
                    # the history of already-notified records and cause every one of
                    # them to be re-notified as "new" the next time a real check runs.
                    logger.warning(
                        f"Scheduled question {schedule_id}: skipping condition diff this cycle "
                        f"(no trained example) — matched_keys left unchanged."
                    )
                elif schedule.get("type") == "conditional":
                    # Diff which SPECIFIC records currently match against what matched
                    # on the previous poll — an aggregate true/false isn't enough,
                    # since a condition can keep gaining new matching records forever
                    # (e.g. more items becoming "shipped" over time) without the
                    # aggregate ever going back to false in between.
                    key_to_row = {}
                    for row in rows:
                        key = _condition_row_key(row)
                        if key is not None:
                            key_to_row.setdefault(key, row)
                    current_keys = set(key_to_row)
                    previous_keys = set(record.get("matched_keys") or [])
                    new_keys = current_keys - previous_keys
                    record["matched_keys"] = sorted(current_keys)
                    record["last_condition_state"] = bool(current_keys)  # /list display cache only
                    if new_keys:
                        _deliver_condition_matches([key_to_row[k] for k in sorted(new_keys)], len(current_keys))
                else:
                    _deliver(rows)

                # Give scheduled-agent fires the same activity/billing trail an
                # interactive question gets — a fresh question_id per fire, since
                # each fire is its own independent question/answer, not an update
                # to a prior one.
                try:
                    # Hyphenated form (str(), not .hex) — dbo.users.question_id is a
                    # uniqueidentifier column and SQL Server only implicitly converts
                    # the 36-char 8-4-4-4-12 form; a bare 32-char hex string raises 8169.
                    question_id = str(uuid.uuid4())
                    cost_usd = self.log_token_count(
                        question_id=question_id,
                        total_tokens=total_tokens,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        model_name=model_name,
                        cached_input_tokens=0,
                    )
                    self.log_user_activity(
                        question_id=question_id,
                        question=record.get("display_question") or record["question_en"],
                        sql_query=sql,
                        workspace_name=record["workspace_name"],
                        workspace_id=workspace_id,
                        user_role=record.get("owner_username"),
                        token_count=total_tokens,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        model_name=model_name,
                        cost_usd=cost_usd,
                    )
                except Exception as log_exc:
                    logger.error(f"Scheduled question {schedule_id} activity/billing logging failed: {log_exc}")

                record["last_status"] = "ok"
                record["last_sql"] = sql
                record["last_error"] = None
                record["last_run_at"] = time.time()
                record["run_count"] = record.get("run_count", 0) + 1
                if schedule.get("type") == "date":
                    # DateTrigger fires exactly once and auto-removes itself from the
                    # scheduler — disable the persisted record to match.
                    record["enabled"] = False
                # Conditional agents never auto-disable — they keep monitoring
                # indefinitely (re-arming each time the condition returns to false)
                # until the user explicitly /stops them.

                _save_schedule_records(workspace_id, metadata, records)
            except Exception as e:
                logger.exception(f"Scheduled question {schedule_id} (workspace {workspace_id}) failed: {e}")

        global scheduled_agents_scheduler
        scheduled_agents_scheduler = BackgroundScheduler()
        scheduled_agents_scheduler.start()
        atexit.register(lambda: scheduled_agents_scheduler.shutdown())

        try:
            all_scheduled_ws = self.workspace_collection.get()
            for idx, ws_meta in enumerate(all_scheduled_ws.get("metadatas", []) or []):
                ws_id = all_scheduled_ws["ids"][idx]
                ws_records = json.loads(ws_meta.get("scheduled_questions", "[]"))
                for rec in ws_records:
                    if not rec.get("enabled"):
                        continue
                    try:
                        scheduled_agents_scheduler.add_job(
                            func=_run_scheduled_question,
                            args=[ws_id, rec["schedule_id"]],
                            trigger=_build_schedule_trigger(rec["schedule"]),
                            id=rec["schedule_id"],
                            max_instances=1,
                            coalesce=True,
                            replace_existing=True,
                            misfire_grace_time=120,
                        )
                    except Exception as rebuild_exc:
                        logger.warning(f"Failed to rebuild scheduled question {rec.get('schedule_id')}: {rebuild_exc}")
        except Exception as e:
            logger.exception(f"Scheduled-question agent rebuild failed: {e}")
        logger.info("Scheduled-question agents scheduler started and rebuilt from persisted state.")
        # ============= end scheduled agents infra =============

        # ============= Warehouse Performance Intelligence Agent =============
        # Automatic, zero-config agent in engine/warehouse_perf (routes under
        # /api/v0/warehouse_perf/*). Its per-workspace jobs run on the scheduled-agents
        # scheduler above; it resolves each workspace explicitly and never uses the global
        # `vn`. Reuses this module's _send_email / load_email_config for delivery. Returns
        # None (and logs) on any init failure, so it can't stop the app from starting.
        self.warehouse_perf = create_warehouse_perf(
            self, send_email=_send_email, load_email_config=load_email_config,
            scheduler=scheduled_agents_scheduler,
        )

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
        client = chromadb.PersistentClient(path="admin_store")
        collection = client.get_or_create_collection("DB_connections")
        # Get or create collections
        config_collection = client.get_or_create_collection(name="LLM_config")
        users_collection = client.get_or_create_collection(name="users_collection")


        def get_available_models():
            """Fetch locally available Ollama models."""
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
                local_models = [line.split()[0] for line in result.stdout.splitlines() if line and not line.startswith("NAME")]
            except Exception as e:
                print("Error fetching Ollama models:", e)
                local_models = []
            return local_models, local_models + ["gpt-4.1-mini", "gpt-4.1", "gpt-3.5-turbo", "gpt-4", "gpt-4o", "o3"]



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
        # list(ADMIN_ROLES), not the bare string "admin": requires_role compares
        # with == when given a string, so a superadmin — who outranks an admin and
        # whom access_control already admits here — was being 403'd off the admin
        # dashboard. Every other admin route uses the list form.
        @self.requires_role(list(ADMIN_ROLES))
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
        @self.requires_role(list(ADMIN_ROLES))  # see /admin above — excluded superadmin
        @self.requires_auth
        def index(**kwargs):
            """Render index page with available models and last saved config."""
            local_models, available_models = get_available_models()
            
            # Fetch the last stored configuration
            last_config = None
            results = config_collection.get()

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
            logger.info(f"Tested DB connection to {database} on {server},{port} as {username}: {success}")
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
        





        @self.flask_app.route("/connect-vanna", methods=["POST"])
        def connect_vanna():
            """
            Connect the caller's session to a workspace: its Vanna instance is
            built from the workspace's *saved* LLM + DB config. Connection details
            in the request body are ignored — they used to be echoed back from
            /get_workspace, which exposed the DB password and API key to every
            browser. A plain user may only connect their own assigned workspace.
            """
            try:
                data = request.get_json(silent=True) or {}
                workspace_id = data.get("workspace_id")
                if not workspace_id:
                    return jsonify({"success": False, "error": "workspace_id is required"}), 400

                user = self.auth.get_user(request) or {}
                if not self._user_can_access_workspace(user, workspace_id):
                    return jsonify({"success": False, "error": "You don't have access to this workspace"}), 403

                instance, err = _vanna_registry.get_or_build(workspace_id)
                if instance is None:
                    logger.warning(f"connect-vanna failed for workspace {workspace_id}: {err}", extra={"admin": True})
                    return jsonify({"success": False, "error": err}), 400

                session["workspace_id"] = workspace_id
                vn.bind_instance(instance)
                # No set_default_instance here: that default is process-global and
                # was never torn down (unlike the thread-local binding above, which
                # teardown_request clears), so the last person to connect silently
                # became the fallback workspace for every unbound caller in the
                # process — the cross-workspace leak this registry exists to prevent.
                # Legitimate callers are covered: request threads bind here or
                # resolve via session["workspace_id"], background jobs bind through
                # ensure_vanna_initialized. Anything left falls through to bare(),
                # which now logs instead of quietly borrowing someone's workspace.
                self.vn = vn

                logger.info(
                    f"Vanna connected for workspace {workspace_id}: model={instance.config.get('model')} "
                    f"database={getattr(instance, 'primary_db_name', None)}",
                    extra={"admin": True},
                )
                self.cache.refresh_cache_for_user(session.get('user_id'), workspace_id)
                return jsonify({"success": True, "redirect": url_for('hello')}), 200

            except Exception as e:
                logger.error(f"Failed to connect Vanna: {str(e)}", exc_info=True, extra={"admin": True})
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
        @self.requires_auth
        def get_workspaces(user: any = None):
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
                _vanna_registry.invalidate(id_str)
                return jsonify({"message": "Workspace updated successfully"}), 200
            except Exception as e:
                logger.error(f"Error updating workspace with ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Failed to update workspace"}), 500










































































































































































































































































































































































































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
                _vanna_registry.invalidate(id_str)
 
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
        @self.requires_auth
        def connect_workspace(id, user: any = None):
            """Admin: (re)build a workspace's Vanna instance from its saved config."""
            id_str = str(id)
            instance, err = _vanna_registry.get_or_build(id_str, refresh=True)
            if instance is None:
                logger.error(f"Failed to connect workspace {id_str}: {err}", extra={"admin": True})
                return jsonify({"error": "Failed to connect workspace", "details": err}), 400
            logger.info(f"Connected to workspace: ID={id_str}", extra={"admin": True})
            return jsonify({"message": "Workspace connected successfully"}), 200

        @self.flask_app.route('/get_workspace/<uuid:id>', methods=['GET'])
        @self.requires_auth
        def get_workspace(id, user: any = None):
            try:
                id_str = str(id)
                results = self.workspace_collection.get(ids=[id_str])
                if not results.get("metadatas"):
                    return jsonify({"error": f"Workspace with ID {id_str} not found"}), 404
                metadata = results["metadatas"][0]

                user = self.auth.get_user(request) or {}
                if str(user.get("role", "")).lower() not in ADMIN_ROLES:
                    # The chat UI and user dashboard only need the name. Config
                    # (DB password, API key) is admin-only; the empty objects
                    # keep existing callers that read .llm_config/.db_config safe.
                    if not self._user_can_access_workspace(user, id_str):
                        return jsonify({"error": "You don't have access to this workspace"}), 403
                    return jsonify({
                        "id": id_str,
                        "name": metadata.get("name"),
                        "llm_config": {}, "db_config": {}, "db_config_b": {},
                    })

                response = {
                    "id": id_str,
                    "name": metadata.get("name"),
                    "llm_config": json.loads(metadata["llm_config"]) if "llm_config" in metadata else {},
                    "db_config": json.loads(metadata["db_config"]) if "db_config" in metadata else {},
                    "db_config_b": json.loads(metadata["db_config_b"]) if "db_config_b" in metadata else {},
                    "training_id": metadata.get("training_id")
                }
                logger.info(f"Returning workspace data for {id_str} (admin)")
                return jsonify(response)
            except ValueError as e:
                logger.error(f"ValueError processing ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": f"Invalid ID format: {str(e)}"}), 400
            except Exception as e:
                logger.error(f"Error fetching workspace with ID {id}: {str(e)}", exc_info=True, extra={"admin": True})
                return jsonify({"error": f"Failed to fetch workspace: {str(e)}"}), 500



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
                _vanna_registry.invalidate(workspace_id)
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

            alias = (secondary_cfg.get("db_alias") or "").strip() or "SECONDARY"
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
                _vanna_registry.invalidate(workspace_id)

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







        @self.flask_app.route("/api/v0/train", methods=["POST"])
        @self.requires_auth
        @self.requires_role(list(ADMIN_ROLES))
        def add_training_data(user: any = None):
            logger.info(f"Received request from user: {user}")
            data = flask.request.json
            logger.info(f"Request data: {data}")

            workspace_id = data.get("workspace_id")
            if not workspace_id:
                return jsonify({"error": "Workspace ID is required"}), 400

            # workspace_id is taken straight from the request body, so authenticating
            # the caller isn't enough — check they may actually write to THIS
            # workspace. Training data steers generate_sql for everyone in it.
            if not self._user_can_access_workspace(user, workspace_id):
                return jsonify({"error": "You don't have access to this workspace"}), 403

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
            return _initialize_vanna_instance_module(workspace_id, llm_details, db_details, db_details_b)

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

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            try:
                safe_table = table_name.replace("'", "''")
                df = vn.run_sql(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    f"WHERE TABLE_NAME = '{safe_table}' ORDER BY ORDINAL_POSITION"
                )
                columns = df["COLUMN_NAME"].tolist() if df is not None and not df.empty else []
                if not columns:
                    return jsonify({"type": "error", "error": f"No columns found for table {table_name}."}), 404
                return jsonify({"type": "success", "columns": columns})
            except Exception as e:
                return jsonify({"type": "error", "error": f"Failed to fetch columns: {str(e)}"}), 500

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
        def get_tables():
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
            return VannaFlaskAPI.ensure_vanna_initialized(self, workspace_id)

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

            workspace = get_workspace_metadata(self, workspace_id) or {}
            body, status = _stage_pending_write(vn, workspace.get("name") or workspace_id, workspace_id, question)
            return jsonify(body), status

        def _execute_pending_write(workspace_id, write_id, user_id=None):
            """Execute a previously-staged write after explicit confirmation.
            The SQL is looked up server-side by write_id — never accepted as a raw
            string from the client — and re-validated against the whitelist here,
            independent of whatever staging already checked. Callers must have
            already verified the confirming user is admin/superadmin.

            Returns (body_dict, http_status)."""
            if not workspace_id or not write_id:
                return {"type": "error", "error": "workspace_id and write_id are required"}, 400

            with _pending_writes_lock:
                pending = _pending_writes.pop(write_id, None)

            if not pending or pending.get("workspace_id") != workspace_id:
                return {"type": "error", "error": "Unknown or expired write_id"}, 404

            # A pending write is single-use and short-lived (10 minutes) — re-generate
            # if it has gone stale, so a confirmation click can't replay a write against
            # data that may have changed, or execute long after the user actually saw it.
            if time.time() - pending.get("created_at", 0) > 600:
                return {"type": "error", "error": "This write has expired — please ask again"}, 410

            sql = pending["sql"]
            question = pending["question"]

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return {"type": "error", "error": error}, 400

            whitelist = vn.get_write_whitelist(workspace=workspace_id)
            valid, reason = vn.is_write_sql_valid(sql, whitelist)
            operation, table_ref, _ = _parse_write_statement(sql)

            if not valid:
                _insert_write_audit_log(workspace_id, user_id, question, sql, table_ref, operation,
                                         None, "rejected", reason)
                return {"type": "error", "error": reason}, 400

            workspace = get_workspace_metadata(self, workspace_id)
            db_config = json.loads(workspace.get("db_config", "{}")) if workspace else {}
            if not db_config:
                return {"type": "error", "error": "Database configuration not found for workspace"}, 400

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

                return {
                    "type": "success",
                    "message": "Write executed successfully",
                    "rows_affected": rows_affected,
                }, 200

            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                logger.error(f"execute_write_sql failed: {e}", exc_info=True, extra={"admin": True})
                _insert_write_audit_log(workspace_id, user_id, question, sql, table_ref, operation,
                                         None, "failed", str(e))
                return {"type": "error", "error": str(e)}, 200

            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        @self.flask_app.route('/api/v0/execute_write_sql', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def execute_write_sql_route(user=None):
            data = request.get_json() or {}
            body, status = _execute_pending_write(
                data.get('workspace_id'), data.get('write_id'), session.get('user_id')
            )
            return jsonify(body), status

        # Published for handlers outside this scope (_handle_query_message lives
        # in VannaFlaskAPI.__init__; the Teams bot uses the execute path).
        self._stage_pending_write = _stage_pending_write
        self._execute_pending_write = _execute_pending_write

        def _user_email_for(username):
            """The app user's own registered email (lowercased), or None."""
            if not username:
                return None
            try:
                found = self.users_collection.get(where={"username": username}, limit=1)
                metas = found.get("metadatas") or []
                return (metas[0].get("email") or None) if metas else None
            except Exception:
                return None

        def _has_pending_clarification(workspace_id, username, text=None):
            """Peek (without consuming) whether (workspace_id, username) has an
            open schedule clarification — used by the routing endpoints to force
            a bare follow-up reply down the schedule path even though the reply
            text alone wouldn't obviously classify as "schedule". The actual
            pop+merge happens inside _handle_schedule_message."""
            key = f"{workspace_id}:{username}"
            with _pending_schedule_clarifications_lock:
                pending = _pending_schedule_clarifications.get(key)
                # A fresh question instead of an answer: the user moved on, so the
                # prompt is dropped and the question is routed as usual.
                if pending and _is_new_question(text):
                    _pending_schedule_clarifications.pop(key, None)
                    return False
            return bool(pending) and time.time() - pending.get("created_at", 0) <= _PENDING_CLARIFICATION_TTL_SECONDS

        def _handle_schedule_message(workspace_id, raw_text, prior_question, username, prior_sql=None, ctx=None, main_question=None, prior_kind=None):
            """
            Core scheduling/conditional-agent pipeline: fixed literals (list /
            stop <id> / email list) are handled deterministically with no LLM
            call; anything else costs exactly one extract_schedule_request call.
            Strictly read-only — a write-classified request is hard-rejected,
            never staged or downgraded. Shared by slash_command_route ("/"-prefixed
            POST body) and route_message (POST, natural-language dispatch) so both
            entry points run identical logic.

            main_question: the ORIGINAL root question of the current follow-up
            thread (resolved client-side by walking parent_question_id back to its
            first question), distinct from prior_question which is just the most
            recent message. Needed because scheduling a bare follow-up like "show
            me top 4" stores THAT text as the agent's question — accurate for
            re-running it (paired with prior_sql as context), but meaningless on
            its own in a notification email sent days later. None when there is
            no broader thread (prior_question is already the root) or no caller
            supplies it (e.g. the Teams channel, which has no thread tracking).

            prior_kind: "prediction" when prior_question was answered by the
            prediction/anomaly pipeline. That answer has no SQL, so a bare "send
            this" stores the check that produced it and re-runs that at fire time.

            Returns (body_dict, status_code).
            """
            body = raw_text[1:].strip() if raw_text.startswith('/') else raw_text

            # A "/" command always abandons any open clarification (pop clears it
            # either way); a plain reply merges it with the pending context so a
            # bare "the sales report" can complete an earlier "send this to me".
            pending_key = f"{workspace_id}:{username}"
            with _pending_schedule_clarifications_lock:
                pending = _pending_schedule_clarifications.pop(pending_key, None)

            # Also discard any pending QUERY clarification for this user — found
            # live: open "show me the problem orders" (query clarification
            # pending) -> interrupt with an unrelated "/list" (routed straight
            # here, never through _handle_query_message) -> ask a totally fresh,
            # unrelated question minutes later -> it silently got merged with
            # the stale "problem orders" text, since nothing had ever popped it.
            # Any explicit trip into the scheduling pipeline means the user has
            # moved on from whatever query clarification was open, same as a
            # "/" command already abandons this function's own pending state.
            with _pending_query_clarifications_lock:
                _pending_query_clarifications.pop(pending_key, None)

            clarification_attempts = 0
            if (
                pending and body and not raw_text.startswith('/')
                and time.time() - pending.get("created_at", 0) <= _PENDING_CLARIFICATION_TTL_SECONDS
            ):
                body = f"{pending['raw_text']} {body}".strip()
                clarification_attempts = pending.get("attempts", 0)

            def _ask_clarification(question_text):
                """Store `body` as pending context and ask instead of hard-erroring,
                unless the retry cap is hit — then give up with a plain error."""
                new_attempts = clarification_attempts + 1
                if new_attempts >= _MAX_CLARIFICATION_ATTEMPTS:
                    return {
                        "type": "error",
                        "error": "I still don't have enough information — please restate the full request in one message.",
                    }, 400
                with _pending_schedule_clarifications_lock:
                    _pending_schedule_clarifications[pending_key] = {
                        "raw_text": body,
                        "created_at": time.time(),
                        "attempts": new_attempts,
                    }
                return {"type": "text", "text": question_text}, 200

            if not body:
                return {
                    "type": "text",
                    "text": "Usage: /list, /stop <id>, /email list, or a scheduling request like "
                            "\"every Monday at 9am send me open orders to my manager by email\". "
                            "Email recipients are configured by your workspace admin.",
                }, 200

            # Deterministic "list" shortcut: exact "/list" (the fast path), or
            # a natural-language ask to view existing scheduled agents (e.g.
            # "list my scheduled questions", "show my schedules", "what are my
            # scheduled agents") — tested as a verb/noun combination rather than
            # an enumerated phrase list, same rationale as classify_message_route,
            # since typed-out NL phrasing for this varies a lot more than the
            # bare "/list" the "/"-prefixed fast path expects. Without this, a
            # request that only reaches here via NL routing (not "/") fell
            # through to the schedule-creation extractor, which correctly
            # refused to treat it as a new schedule but replied with a
            # confusing refusal instead of actually listing anything.
            is_list_request = re.match(r'^list$', body, re.IGNORECASE) or (
                re.search(r'\b(list|show|view|see|display)\b', body, re.IGNORECASE)
                and re.search(r'\bschedul\w*\b', body, re.IGNORECASE)
            ) or re.search(r'\bwhat\s+(?:are|is)\b.*\bschedul\w*\b', body, re.IGNORECASE)
            if is_list_request:
                _, records = _get_schedule_records(workspace_id)
                mine = [r for r in (records or []) if r.get("owner_username") == username]
                if not mine:
                    return {"type": "text", "text": "You have no scheduled agents in this workspace."}, 200
                lines = [
                    f"{r['schedule_id']} — {r.get('display_question', '')} — "
                    f"{_describe_schedule(r.get('schedule', {}))} — "
                    f"{'enabled' if r.get('enabled') else 'stopped'}"
                    f"{_status_suffix(r)}"
                    for r in mine
                ]
                return {"type": "text", "text": "\n".join(lines)}, 200

            stop_match = re.match(r'^stop\s+(\S+)$', body, re.IGNORECASE)
            if stop_match:
                schedule_id = stop_match.group(1)
                with _get_schedule_records_lock(workspace_id):
                    metadata, records = _get_schedule_records(workspace_id)
                    if metadata is None:
                        return {"type": "error", "error": "Workspace not found"}, 404
                    record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                    if not record or record.get("owner_username") != username:
                        return {"type": "error", "error": f"No scheduled agent {schedule_id} found for you."}, 404
                    record["enabled"] = False
                    try:
                        scheduled_agents_scheduler.remove_job(schedule_id)
                    except JobLookupError:
                        pass
                    _save_schedule_records(workspace_id, metadata, records)
                return {"type": "text", "text": f"Stopped {schedule_id}."}, 200

            if re.match(r'^email\s+list$', body, re.IGNORECASE):
                registered = _get_workspace_emails(workspace_id)
                if not registered:
                    return {"type": "text", "text": "No email recipients configured for this workspace yet — ask your admin to add some."}, 200
                lines = [f"{e['label']} — {e['address']}" for e in registered]
                return {"type": "text", "text": "\n".join(lines)}, 200

            # Anything else: exactly one LLM call.
            initialized, init_err = self.ensure_vanna_initialized(workspace_id)
            if not initialized:
                return {"type": "error", "error": init_err}, 400

            registered_emails = _get_workspace_emails(workspace_id)
            reference_time = datetime.now(ZoneInfo(DEFAULT_SCHEDULE_TIMEZONE)).isoformat()
            extraction = vn.extract_schedule_request(
                body, default_timezone=DEFAULT_SCHEDULE_TIMEZONE, reference_time=reference_time,
                known_email_labels=[e["label"] for e in registered_emails],
            )

            schedules = extraction.get("schedules") or []
            if not extraction.get("ok") or not schedules:
                return {
                    "type": "text",
                    "text": extraction.get("error") or "I couldn't understand that as a scheduling request — please rephrase.",
                }, 200

            # A compound request ("send this now and every Monday") comes back as
            # more than one entry — almost every request is exactly one, though.
            multi = len(schedules) > 1
            for schedule in schedules:
                if schedule.get("type") == "conditional" and not schedule.get("seconds"):
                    schedule["seconds"] = 1800  # no check frequency stated — default to every 30 min

            first_conditional = next((s for s in schedules if s.get("type") == "conditional"), None)
            extracted_question = extraction.get("question")
            conditional_text = first_conditional.get("condition_text") if first_conditional else None

            # Safety net for extract_schedule_request misreading a bare delivery
            # command ("send mail now", "email this now") as if the command text
            # ITSELF were the data question — found live: a schedule created from
            # "send mail now" stored that literal phrase as display_question, so
            # every fire tried to run "send mail now" as a question (no trained
            # example for it, obviously) and every email read "No data found for:
            # send mail now" instead of answering the real question that was
            # actually being discussed beforehand. The extraction prompt is
            # supposed to leave "question" null for a bare follow-up, but an
            # imperative with no back-reference pronoun ("this"/"it") doesn't
            # reliably trigger that. When prior_question is available, prefer it
            # over an "extracted" question that's really just the command restated
            # with nothing else added.
            def _norm(s):
                return re.sub(r'[^a-z0-9]+', '', (s or '').lower())
            if prior_question and extracted_question:
                norm_extracted, norm_body = _norm(extracted_question), _norm(body)
                if norm_extracted and (norm_extracted == norm_body or norm_extracted in norm_body):
                    extracted_question = None

            question_en = extracted_question or conditional_text or prior_question

            # When the request only referred back ("send this", "email that") we reuse
            # the prior question verbatim — but that text may itself be a follow-up
            # ("show me top 4") that means nothing on its own. Carry the prior SQL as
            # context so each fire can resolve it the same way the interactive
            # follow-up branch does; a self-contained question needs no context and
            # gets none, so generation stays unbiased.
            context_sql = prior_sql if (not extracted_question and not conditional_text and prior_sql) else None
            analysis = None
            # "send this"/"notify me if..." referring back to a prior
            # prediction/anomaly/performance chat answer has no SQL of its
            # own to regenerate (performance: admin-curated config SQL;
            # prediction/anomaly: an LLM-built check) — look up what actually
            # produced it and re-run THAT at fire time, regardless of what
            # prior_kind the caller claims (previously gated on prior_kind ==
            # "prediction" specifically, which meant this never fired for a
            # remembered performance answer at all) — _last_analysis_run_for
            # is already self-contained/safe (TTL + exact question-text
            # match), so trying it can only ADD a correct match.
            run = _last_analysis_run_for(workspace_id, username, prior_question) if prior_question else None

            if conditional_text:
                # A conditional request naming a performance metric directly
                # ("alert me if the warehouse's performance goes below 70%")
                # has no numeric SQL of its own to build a WHERE clause from
                # — the threshold applies to an admin-curated performance
                # config's OWN result columns. Two ways to find that config:
                # a follow-up to something already answered earlier in this
                # chat thread (remembered via `run`), or a brand-new message
                # that names a performance metric never discussed in this
                # thread but still matches a saved config fresh — found live:
                # "send a mail to X if the performance of the warehouse goes
                # below 70%", asked with no prior chat answer to refer back
                # to, fell straight to the plain-SQL conditional path below,
                # which has no trained example for it and refused with "no
                # trained example covers this kind of question yet" even
                # though the identical question answers fine as a plain
                # (non-conditional) report.
                if run and run.get("kind") == "performance":
                    perf_cfgs_for_condition = run["config"]
                else:
                    cond_ws_meta = get_workspace_metadata(self, workspace_id) or {}
                    perf_cfgs_for_condition = self._match_performance_configs(
                        question_en, cond_ws_meta, cond_ws_meta.get("name") or str(workspace_id)
                    )

                if perf_cfgs_for_condition:
                    # Checked even when extracted_question ALSO came back
                    # non-empty, since a clause like "any warehouse's
                    # occupancy exceeds 90%" reads just as plausibly as a
                    # standalone question to extract_schedule_request, which
                    # has no way to know it's really qualifying a performance
                    # check. Only committed to if the condition actually maps
                    # to one of that check's real columns (extract_numeric_
                    # condition below); otherwise falls through to the
                    # existing plain-SQL conditional path using whatever
                    # extracted_question/conditional_text already resolved
                    # to, unchanged.
                    sample_configs = (
                        perf_cfgs_for_condition if isinstance(perf_cfgs_for_condition, list)
                        else [perf_cfgs_for_condition]
                    )
                    try:
                        _sample_text, sample_df, _sample_types = self._run_performance_configs_and_summarize(
                            sample_configs, prior_question or question_en, None
                        )
                    except Exception as sample_exc:
                        logger.warning(f"Condition grounding run failed: {sample_exc}")
                        sample_df = None
                    if sample_df is not None:
                        numeric_cols = [
                            c for c in sample_df.columns
                            if pd.api.types.is_numeric_dtype(sample_df[c])
                        ]
                        cond = vn.extract_numeric_condition(conditional_text, numeric_cols)
                        rule = cond.get("rule")
                        if rule:
                            is_safe, reason = _is_safe_eval_rule(rule, list(sample_df.columns))
                            if is_safe:
                                analysis = {
                                    "kind": "performance", "config": perf_cfgs_for_condition,
                                    "condition_rule": rule, "condition_text": conditional_text,
                                }
                                # question_en must stay the ORIGINAL question
                                # (what's being checked), never conditional_text
                                # (the rule) — otherwise every fire's display/
                                # subject would read as the raw condition
                                # instead of what's monitored. Only needed for
                                # the `run` case: a fresh match already has a
                                # proper question_en from extraction, since
                                # this isn't a bare follow-up with nothing else
                                # said.
                                if run and run.get("kind") == "performance":
                                    question_en = prior_question
                                context_sql = None
                            else:
                                logger.warning(
                                    f"extract_numeric_condition produced an unsafe rule, "
                                    f"discarding: {rule!r} ({reason})"
                                )

            if analysis is None and not extracted_question and run:
                # Bare "send this"/"email that" — no new question, no
                # (usable) condition — reuse whatever was last answered,
                # regardless of kind.
                analysis = {"kind": run["kind"], "config": run["config"]}
                context_sql = None

            # A freshly typed scheduling request ("every Monday, send me a
            # report on the warehouse's performance") has no prior chat
            # answer to fall back on — the `run` lookup above only covers
            # "send this"-style references to something already answered.
            # Without this, such a request fell straight to generate_sql,
            # which has no trained example for an admin-curated performance
            # metric and delivered "Needs a clearer question" on every fire,
            # even though the exact same question answered correctly in
            # chat. Match it against performance configs the same way chat
            # does before treating it as a plain data question.
            if analysis is None and question_en:
                schedule_ws_meta = get_workspace_metadata(self, workspace_id) or {}
                matched_perf_cfgs = self._match_performance_configs(
                    question_en, schedule_ws_meta, schedule_ws_meta.get("name") or str(workspace_id)
                )
                if matched_perf_cfgs:
                    analysis = {"kind": "performance", "config": matched_perf_cfgs}
                    context_sql = None

            if not question_en:
                return _ask_clarification("What would you like me to send you, or what should I watch for?")

            # question_en stays exactly what's actually re-run at fire time (the
            # follow-up fragment, resolved against context_sql) — never rewritten
            # for readability, or generation would be working from different text
            # than what the user actually asked. display_question is the separate,
            # human-facing copy everywhere else (subject lines, /list, the "You
            # asked" box in emails): when this agent was created from mid-thread
            # follow-up text, prefix it with the thread's original question so a
            # notification read days later is still self-explanatory instead of
            # just "show me top 4" with no context.
            display_question = question_en
            if context_sql and main_question and _norm(main_question) != _norm(question_en):
                display_question = f"{main_question} — {question_en}"

            if vn.classify_intent(question_en) == "write":
                return {
                    "type": "error",
                    "error": "That looks like a write request — scheduled agents are strictly read-only.",
                }, 409

            # Email is the only real delivery channel — chat was previously a
            # silent fallback that pinged the OWNER's own chat inbox whenever no
            # recipient could be resolved, which looked broken (a message with
            # nobody actually assigned to it) and wasn't reliably seen anyway (it
            # only surfaced if the owner happened to have the chat page open at
            # the right moment — no push/notification exists). A NAMED-but-unknown
            # recipient ("email this to Bob" when "Bob" isn't registered) is a
            # likely typo/mistake worth catching, so that always asks rather than
            # silently dropping what the user asked for; see the no-recipient-at-all
            # case below for when nothing was named.
            email_recipients = []
            email_labels = extraction.get("email_labels") or []
            registered_by_label = {e["label"].lower(): e["address"] for e in registered_emails}

            if any(label.lower() == "all" for label in email_labels):
                email_recipients = list(registered_by_label.values())
            elif email_labels:
                unknown = [label for label in email_labels if label.lower() not in registered_by_label]
                if unknown:
                    known_list = ", ".join(e["label"] for e in registered_emails) or "(none registered)"
                    return _ask_clarification(
                        f"\"{unknown[0]}\" isn't a registered recipient. You have: {known_list} — which did you mean?"
                    )
                email_recipients = [registered_by_label[label.lower()] for label in email_labels]
            elif extraction.get("email_address"):
                email_recipients = [extraction["email_address"]]
            elif len(registered_emails) == 1:
                email_recipients = [registered_emails[0]["address"]]
            # else: no recipient named at all, and either zero or multiple
            # recipients are registered — ask who should receive it instead of
            # silently creating an unassigned agent, below.

            # A request from Teams with no explicit email goes back into that same
            # Teams conversation instead of needing a recipient asked for — it
            # already has a real, reliable delivery target (unlike the old
            # chat-inbox fallback this replaced; see _deliver_to_teams below).
            is_teams_request = bool(ctx and ctx.channel == "teams" and ctx.teams_aad_id)

            if not email_recipients and not is_teams_request:
                if registered_emails:
                    known_list = ", ".join(e["label"] for e in registered_emails)
                    return _ask_clarification(f"Who should receive this — {known_list}, or another email address?")
                return _ask_clarification(
                    "Who should receive this? Give me an email address, or ask your admin to register one first."
                )

            channel = "email" if email_recipients else "teams"

            # The whole read-modify-write cycle below (get -> validate -> persist)
            # runs under the per-workspace lock so it can't lose an update racing a
            # fire/stop/resume/delete/poll for this workspace. Early-exit validation
            # failures raise _ScheduleRequestError instead of returning directly,
            # so the lock (acquired once, around the call) still covers every path.
            def _create_schedules():
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    raise _ScheduleRequestError({"type": "error", "error": "Workspace not found"}, 404)

                enabled_count = sum(1 for r in records if r.get("owner_username") == username and r.get("enabled"))
                if enabled_count + len(schedules) > MAX_ENABLED_SCHEDULES_PER_USER:
                    raise _ScheduleRequestError({
                        "type": "error",
                        "error": f"That would put you at {enabled_count + len(schedules)} scheduled agents — "
                                 f"the limit is {MAX_ENABLED_SCHEDULES_PER_USER}. Stop some before creating more.",
                    }, 400)

                # Pass 1: validate every entry and run each conditional entry's preview
                # check BEFORE persisting anything — a compound request must succeed or
                # fail as a whole, never leave a partial set of agents behind because
                # entry 2 of 3 turned out to be unschedulable.
                prepared = []
                for idx, schedule in enumerate(schedules):
                    label = f"Schedule {idx + 1} of {len(schedules)}: " if multi else ""
                    is_conditional = schedule.get("type") == "conditional"

                    try:
                        trigger = _build_schedule_trigger(schedule)
                    except Exception as trigger_exc:
                        raise _ScheduleRequestError({"type": "error", "error": f"{label}Couldn't build a schedule from that: {trigger_exc}"}, 400)

                    tz = schedule.get("timezone") or DEFAULT_SCHEDULE_TIMEZONE
                    now = datetime.now(ZoneInfo(tz))
                    fires = []
                    t = trigger.get_next_fire_time(None, now)
                    for _ in range(3):
                        if t is None:
                            break
                        fires.append(t)
                        t = trigger.get_next_fire_time(t, t)

                    if not fires:
                        raise _ScheduleRequestError({"type": "error", "error": f"{label}That schedule never fires — please rephrase."}, 400)
                    if len(fires) >= 2 and (fires[1] - fires[0]).total_seconds() < MIN_SCHEDULE_INTERVAL_SECONDS:
                        raise _ScheduleRequestError({
                            "type": "error",
                            "error": f"{label}That schedule fires more than once within {MIN_SCHEDULE_INTERVAL_SECONDS // 60} "
                                     f"minutes — please choose a longer interval.",
                        }, 400)
                    if schedule.get("type") in ("interval", "conditional") and int(schedule.get("seconds", 0)) < MIN_SCHEDULE_INTERVAL_SECONDS:
                        raise _ScheduleRequestError({
                            "type": "error",
                            "error": f"{label}Please choose a check interval of at least {MIN_SCHEDULE_INTERVAL_SECONDS // 60} minutes.",
                        }, 400)

                    # Conditional agents run indefinitely, so — unlike every other type,
                    # which defers all SQL generation to the first fire — run the full
                    # chain once here: catches a broken condition immediately instead of
                    # only at the first poll, and lets the confirmation echo show the
                    # condition's current state. This is a real query, but never delivers
                    # a notification for it — the user asked to hear about *future*
                    # transitions, not be re-told what the echo already shows them.
                    initial_condition_state = None
                    initial_matched_keys = None
                    condition_preview_error = None
                    condition_row_count = 0
                    if is_conditional and analysis and analysis.get("condition_rule"):
                        # Performance-based conditional (see extract_numeric_
                        # condition in _handle_schedule_message above) — the
                        # "condition" is a threshold on the remembered
                        # check's own numeric result, not a plain data
                        # question to regenerate SQL for. question_en here is
                        # deliberately the ORIGINAL question (what's being
                        # checked), not the condition text, so vn.generate_sql
                        # would either fail outright (no trained example for
                        # "how is the warehouse performing?") or answer a
                        # different question than the one actually being
                        # watched — seed the baseline from the same shared
                        # runner the live chat answer and every poll use.
                        configs = analysis["config"] if isinstance(analysis["config"], list) else [analysis["config"]]
                        try:
                            _preview_text, preview_df, _preview_types = self._run_performance_configs_and_summarize(
                                configs, question_en, metadata.get("name") or str(workspace_id)
                            )
                        except Exception as check_exc:
                            condition_preview_error = f"Condition check failed: {check_exc}"
                            preview_df = None
                        if preview_df is not None:
                            is_safe, reason = _is_safe_eval_rule(analysis["condition_rule"], list(preview_df.columns))
                            if not is_safe:
                                condition_preview_error = f"Condition is no longer valid: {reason}"
                            else:
                                try:
                                    mask = preview_df.eval(analysis["condition_rule"])
                                    matching_df = preview_df[mask]
                                    condition_row_count = len(matching_df)
                                    initial_condition_state = condition_row_count > 0
                                    preview_rows = matching_df.to_dict(orient="records")
                                    initial_matched_keys = sorted({
                                        key for key in (_condition_row_key(r) for r in preview_rows)
                                        if key is not None
                                    })
                                except Exception as eval_exc:
                                    condition_preview_error = f"Condition evaluation failed: {eval_exc}"
                        if condition_preview_error:
                            raise _ScheduleRequestError({"type": "error", "error": f"{label}Couldn't set up that condition: {condition_preview_error}"}, 400)
                    elif is_conditional:
                        sql, *_rest = vn.generate_sql(question=question_en, workspace=metadata.get("name") or str(workspace_id))
                        if not vn.is_sql_valid(sql):
                            condition_preview_error = _explain_invalid_sql(sql)
                        else:
                            ok2, err2 = vn.validate_openquery_literals(sql)
                            ok3, err3 = (True, "") if not ok2 else vn.validate_db_scope(sql)
                            if not ok2:
                                condition_preview_error = err2
                            elif not ok3:
                                condition_preview_error = err3
                            else:
                                try:
                                    df = vn.run_sql(sql)
                                    condition_row_count = len(df) if df is not None else 0
                                    initial_condition_state = condition_row_count > 0
                                    # Seed the baseline match set from this creation-time check —
                                    # these already-matching records must NOT be reported as "new"
                                    # the moment the first real poll runs (the echo below already
                                    # tells the user what currently matches).
                                    preview_rows = df.to_dict(orient="records") if df is not None and len(df) else []
                                    initial_matched_keys = sorted({
                                        key for key in (_condition_row_key(r) for r in preview_rows)
                                        if key is not None
                                    })
                                except Exception as check_exc:
                                    condition_preview_error = f"Condition check failed: {check_exc}"
                        if condition_preview_error:
                            raise _ScheduleRequestError({"type": "error", "error": f"{label}Couldn't set up that condition: {condition_preview_error}"}, 400)

                    prepared.append({
                        "schedule": schedule, "is_conditional": is_conditional, "trigger": trigger,
                        "fires": fires, "condition_row_count": condition_row_count,
                        "initial_condition_state": initial_condition_state, "initial_matched_keys": initial_matched_keys,
                    })

                # Pass 2: everything validated cleanly — persist and register every entry.
                created = []
                for p in prepared:
                    schedule = p["schedule"]
                    is_conditional = p["is_conditional"]
                    schedule_id = uuid.uuid4().hex[:8]
                    record = {
                        "schedule_id": schedule_id,
                        "owner_username": username,
                        "workspace_id": str(workspace_id),
                        "workspace_name": metadata.get("name") or str(workspace_id),
                        "question_en": question_en,
                        "context_sql": context_sql,
                        # A conditional schedule normally means "the SQL
                        # itself is the condition" (plain data questions) —
                        # analysis (a prediction/anomaly/performance check)
                        # has no SQL of its own to double as that, so it's
                        # wiped by default for a conditional schedule UNLESS
                        # it carries its own condition_rule (performance +
                        # extract_numeric_condition — see _handle_schedule_
                        # message above), in which case keeping it is the
                        # whole point: _run_scheduled_question_locked's
                        # analysis branch uses condition_rule to do the same
                        # new-match diffing a plain-SQL conditional does.
                        "analysis": (
                            analysis if (not is_conditional or (analysis and analysis.get("condition_rule")))
                            else None
                        ),
                        "display_question": schedule.get("condition_text") if is_conditional else display_question,
                        "channel": channel,
                        "teams_aad_id": ctx.teams_aad_id if channel == "teams" else None,
                        "email_recipients": email_recipients,
                        "schedule": schedule,
                        "fortnight_anchor_ts": p["fires"][0].timestamp() if schedule.get("fortnight_anchor") else None,
                        "enabled": True,
                        "created_at": time.time(),
                        "last_run_at": None,
                        "last_status": None,
                        "last_error": None,
                        "last_sql": None,
                        "run_count": 0,
                        "chat_inbox": [],
                        "last_condition_state": p["initial_condition_state"],
                        "matched_keys": p["initial_matched_keys"],
                    }
                    records.append(record)
                    scheduled_agents_scheduler.add_job(
                        func=_run_scheduled_question,
                        args=[workspace_id, schedule_id],
                        trigger=p["trigger"],
                        id=schedule_id,
                        max_instances=1,
                        coalesce=True,
                        replace_existing=True,
                        misfire_grace_time=120,
                    )
                    created.append({
                        "schedule_id": schedule_id, "schedule": schedule, "is_conditional": is_conditional,
                        "fires": p["fires"], "condition_row_count": p["condition_row_count"],
                    })
                _save_schedule_records(workspace_id, metadata, records)
                return created

            try:
                with _get_schedule_records_lock(workspace_id):
                    created = _create_schedules()
            except _ScheduleRequestError as sre:
                return sre.body, sre.status

            note = ("Note: " + "; ".join(extraction["ambiguous"]) + "\n") if extraction.get("ambiguous") else ""

            delivery_note = {
                "email": "You'll be notified by email",
                "teams": "You'll be notified in Microsoft Teams",
            }.get(channel, "This isn't assigned to a recipient yet, so nothing will be sent "
                           "until an admin assigns one from the Scheduled Agents panel")

            def _describe_created(c):
                schedule = c["schedule"]
                schedule_id = c["schedule_id"]
                if c["is_conditional"]:
                    return (
                        f"Watching: {schedule.get('condition_text', display_question)}, "
                        f"checked every {schedule['seconds']}s. "
                        f"Currently: {c['condition_row_count']} record(s) match. "
                        f"{delivery_note} whenever a NEW record starts matching — "
                        f"not the {c['condition_row_count']} that already match now. "
                        f"Reply `/stop {schedule_id}` to cancel."
                    )
                fire_list = " · ".join(f.strftime("%a %d %b %H:%M") for f in c["fires"])
                return (
                    f"Scheduled {_describe_schedule(schedule)}. {delivery_note}. "
                    f"Next runs: {fire_list}. "
                    f"Reply `/stop {schedule_id}` to cancel."
                )

            if not multi:
                echo = f"{note}{display_question}\n{_describe_created(created[0])}"
            else:
                lines = "\n".join(f"{i + 1}. {_describe_created(c)}" for i, c in enumerate(created))
                echo = f"{note}{display_question} — split into {len(created)} schedules:\n{lines}"
            return {"type": "text", "text": echo}, 200

        # Exposed on self so _handle_query_message (a separate closure/scope,
        # defined earlier in VannaFlaskAPI.__init__, though it runs on the same
        # instance) can hand off to this when a resumed query clarification
        # turns out to actually be a scheduling request — see the matching
        # comment in _handle_query_message. Same pattern already used for
        # self._handle_query_message below.
        self._handle_schedule_message = _handle_schedule_message

        # ============= prediction/anomaly chat integration =============

        def _has_pending_analysis_confirmation(workspace_id, username):
            """Peek (without consuming) whether (workspace_id, username) has a
            freshly-generated prediction/anomaly config awaiting a save/discard
            decision — used by the routing endpoints to force a bare "yes"/"no"
            reply down the prediction path. The actual pop+resolve happens
            inside _handle_prediction_message."""
            key = f"{workspace_id}:{username}"
            with _pending_analysis_confirmations_lock:
                pending = _pending_analysis_confirmations.get(key)
            return bool(pending) and time.time() - pending.get("created_at", 0) <= _PENDING_ANALYSIS_CONFIRMATION_TTL_SECONDS

        def _has_pending_query_clarification(workspace_id, username):
            """Peek (without consuming) whether (workspace_id, username) was just
            asked a clarifying question about an ordinary data query that
            generate_sql couldn't answer — used by the routing endpoints to force
            the next reply down the query path instead of re-classifying it. The
            actual pop+merge happens inside _handle_query_message itself."""
            key = f"{workspace_id}:{username}"
            with _pending_query_clarifications_lock:
                pending = _pending_query_clarifications.get(key)
            return bool(pending) and time.time() - pending.get("created_at", 0) <= _PENDING_QUERY_CLARIFICATION_TTL_SECONDS

        def _save_analysis_config(workspace_id, kind, config):
            """Upsert one prediction/anomaly config into the workspace's saved
            list — the same upsert-by-type + workspace_collection.update
            pattern save_prediction_config/save_anomaly_config already use
            (engine/flask/__init__.py), factored out here so the chat
            confirm-to-save step doesn't need to fake a request context to
            call those routes directly."""
            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return False
            field = "predictions" if kind == "prediction" else "anomalies"
            existing = json.loads(workspace.get(field, "[]"))
            idx = next((i for i, c in enumerate(existing) if c.get("type") == config.get("type")), -1)
            if idx >= 0:
                existing[idx] = config
            else:
                existing.append(config)
            workspace[field] = json.dumps(existing)
            self.workspace_collection.update(
                ids=[str(workspace_id)],
                metadatas=[workspace],
                documents=[f"Workspace: {workspace.get('name', workspace_id)}"],
            )
            return True

        def _summarize_analysis_result(rows, question_text, workspace_name, kind, sql_query=None):
            """Turns a prediction/anomaly result row list into a chat-friendly
            text reply — reusing the same generate_summary-based pattern
            already used for scheduled-agent chat delivery (_deliver /
            _deliver_condition_matches inside _run_scheduled_question)."""
            if not rows:
                return {"type": "text", "text": f"No data found for: {question_text}"}
            df = pd.DataFrame(rows)
            summary_text = None
            try:
                summary_text, *_ = vn.generate_summary(question=question_text, df=df, sql=sql_query, workspace=workspace_name)
            except Exception as summary_exc:
                logger.warning(f"Analysis result summarization failed: {summary_exc}")

            if kind == "anomaly" and "is_anomaly" in df.columns:
                anomaly_count = int(df["is_anomaly"].sum())
                tail = f"{anomaly_count} of {len(df)} record(s) flagged as anomalous."
            else:
                tail = f"{len(df)} row(s) evaluated."

            body_text = f"{summary_text}\n\n{tail}" if summary_text else tail
            return {"type": "text", "text": body_text}

        def _remember_analysis_run(key, question, kind, config):
            with _last_analysis_runs_lock:
                _last_analysis_runs[key] = {
                    "question": question, "kind": kind, "config": config, "created_at": time.time(),
                }

        def _last_analysis_run_for(workspace_id, username, question):
            """The check that answered `question` for this user, if it was their
            latest prediction answer (and recent enough to still be "this")."""
            with _last_analysis_runs_lock:
                run = _last_analysis_runs.get(f"{workspace_id}:{username}")
            if not run or time.time() - run["created_at"] > _LAST_ANALYSIS_RUN_TTL_SECONDS:
                return None
            if question and run["question"].strip().lower() != question.strip().lower():
                return None
            return run

        def _last_performance_run_for(workspace_id, username):
            """The user's most recent remembered performance-check answer,
            regardless of its exact question text — unlike
            _last_analysis_run_for above (used for "send this"/conditional-
            alert follow-ups, which must match the prior question verbatim),
            a methodology question ("how is this calculated?") is itself a
            NEW question, not a repeat of the old one, so requiring an exact
            match would never find anything."""
            with _last_analysis_runs_lock:
                run = _last_analysis_runs.get(f"{workspace_id}:{username}")
            if not run or run.get("kind") != "performance":
                return None
            if time.time() - run["created_at"] > _LAST_ANALYSIS_RUN_TTL_SECONDS:
                return None
            return run

        def _last_prediction_or_anomaly_run_for(workspace_id, username):
            """Same as _last_performance_run_for, but for the user's most
            recent remembered prediction OR anomaly answer — the fallback
            used when a methodology question names no specific check."""
            with _last_analysis_runs_lock:
                run = _last_analysis_runs.get(f"{workspace_id}:{username}")
            if not run or run.get("kind") not in ("prediction", "anomaly"):
                return None
            if time.time() - run["created_at"] > _LAST_ANALYSIS_RUN_TTL_SECONDS:
                return None
            return run

        def _run_analysis_check(workspace_id, kind, config, question, workspace_name):
            """Runs a stored prediction/anomaly/performance check once, without
            any chat state. Returns (reply_text, rows), or (None, error_text)
            when it fails.

            config is a single config dict for "prediction"/"anomaly", but a
            LIST of one or more config dicts for "performance" — a remembered
            performance answer may have come from several merged checks (see
            _run_performance_configs_and_summarize), and re-running it later
            (a "send this", or a conditional scheduled poll) needs to merge
            the same way the original chat answer did."""
            if kind == "performance":
                configs = config if isinstance(config, list) else [config]
                reply_text, df, _ran_types = self._run_performance_configs_and_summarize(
                    configs, question, workspace_name
                )
                if df is None:
                    return None, reply_text or "the check failed to run"
                return reply_text, df.to_dict(orient="records")
            if kind == "prediction":
                body, status = _run_prediction_config(workspace_id, config=config)
                rows = body.get("df") if status == 200 else None
            else:
                body, status = _run_anomaly_config(workspace_id, config=config)
                rows = body.get("results") if status == 200 else None
            if status != 200:
                return None, body.get("error") or "the check failed to run"
            reply = _summarize_analysis_result(rows, question, workspace_name, kind, config.get("sql_query"))
            return reply["text"], rows or []

        self._last_analysis_run_for = _last_analysis_run_for
        self._last_performance_run_for = _last_performance_run_for
        self._last_prediction_or_anomaly_run_for = _last_prediction_or_anomaly_run_for
        self._run_analysis_check = _run_analysis_check
        self._remember_analysis_run = _remember_analysis_run

        _AFFIRMATIVE_ANALYSIS_REPLIES = {
            "yes", "y", "yep", "yeah", "sure", "save", "save it", "please save",
            "ok", "okay", "confirm", "do it", "go ahead", "yes please",
        }
        _NEGATIVE_ANALYSIS_REPLIES = {
            "no", "n", "nope", "nah", "don't save", "do not save", "skip", "cancel", "no thanks",
        }

        def _handle_prediction_message(workspace_id, raw_text, username):
            """
            Core prediction/anomaly chat pipeline: matches the message against
            this workspace's saved configs (vn.match_analysis_config), runs the
            match and summarizes it — or, if nothing matches, generates a new
            check on the fly via vn.get_prediction_suggestions/
            get_anomaly_suggestions, runs THAT immediately, and offers to save
            it (resolved by the user's next message via
            _pending_analysis_confirmations). Returns (body_dict, status).
            """
            pending_key = f"{workspace_id}:{username}"
            with _pending_analysis_confirmations_lock:
                pending = _pending_analysis_confirmations.pop(pending_key, None)

            # Also discard any pending QUERY clarification — same reasoning as
            # the matching discard in _handle_schedule_message: an explicit
            # trip into the prediction pipeline means the user has moved on
            # from whatever query clarification was open. A no-op when this
            # call IS the reclassification handoff from _handle_query_message,
            # since that already popped it before calling here.
            with _pending_query_clarifications_lock:
                _pending_query_clarifications.pop(pending_key, None)

            def _fallback_to_query_or(apology_text):
                """
                classify_message_route's "prediction" label is a UX router, not
                proof a forecast/anomaly check is actually what's needed — e.g.
                "orders at risk of missing their delivery date" reads like the
                classifier's own prediction example, but is really a concrete,
                current-state condition (promised_date vs. today, not yet
                shipped) that a plain trained SQL question can already answer,
                same as the AI Fix Agent's SLA Risk Radar job. Rather than
                dead-ending here when the prediction/anomaly pipeline can't
                build a reliable check, give the ordinary query pipeline a
                chance at the same raw text before giving up.
                """
                try:
                    query_body, query_status = self._handle_query_message(raw_text, None, workspace_id)
                except Exception as fallback_exc:
                    logger.warning(f"Prediction-pipeline fallback to query failed: {fallback_exc}")
                    return {"type": "text", "text": apology_text}, 200
                if query_status == 200 and query_body.get("type") == "sql":
                    return query_body, query_status
                # No SQL, but the query pipeline asked the user a clarifying question
                # (and left a pending clarification for their reply) — that's a
                # useful answer, far better than the generic apology below.
                with _pending_query_clarifications_lock:
                    asked_user = pending_key in _pending_query_clarifications
                if query_status == 200 and asked_user and query_body.get("text"):
                    return query_body, query_status
                # The query pipeline didn't produce an answer either (e.g. "Insufficient
                # data for query.") — on that path _handle_query_message may have just
                # opened a query clarification for this same user/workspace, inviting a
                # follow-up reply. We're discarding its result in favor of the apology
                # below, so that invitation must be discarded too — otherwise the user's
                # NEXT, completely unrelated message would silently get merged with this
                # probe's dead-end text (the exact "normal question doesn't answer after
                # a prediction/anomaly question" failure mode this fallback exists to fix).
                with _pending_query_clarifications_lock:
                    _pending_query_clarifications.pop(pending_key, None)
                return {"type": "text", "text": apology_text}, 200

            if pending and time.time() - pending.get("created_at", 0) <= _PENDING_ANALYSIS_CONFIRMATION_TTL_SECONDS:
                # "How is this calculated?" right after the "want me to save
                # this?" prompt is the single most direct case there is for a
                # methodology question — pending["config"] IS literally what
                # "this" refers to, with no matching/fallback needed at all.
                # Found live: before this check, this exact message ("predict
                # next month's order volume" -> "how is this calculated")
                # fell through to the yes/no handling below, which isn't a
                # yes or no, so it would have gone through the generic
                # reroute path and come out as "the question is too vague" —
                # the ad-hoc check was never saved, so
                # _try_match_analysis_methodology's own last-run fallback
                # inside _handle_query_message never got a chance to run,
                # since this whole branch is reached BEFORE _handle_query_message
                # is ever called for a message while a confirmation is pending.
                if _METHODOLOGY_CUE.search(raw_text):
                    explanation = vn.generate_analysis_methodology_explanation(
                        raw_text, pending["kind"], pending["config"]
                    )
                    if explanation:
                        return {"type": "text", "text": explanation}, 200
                if raw_text.strip().lower() in _AFFIRMATIVE_ANALYSIS_REPLIES:
                    saved = _save_analysis_config(workspace_id, pending["kind"], pending["config"])
                    if saved:
                        return {
                            "type": "text",
                            "text": f"Saved \"{pending['config'].get('type')}\" as a reusable {pending['kind']} "
                                    f"check — you can run it again anytime by asking about it.",
                        }, 200
                    return {"type": "error", "error": "Couldn't save that check — workspace not found."}, 404
                if raw_text.strip().lower() in _NEGATIVE_ANALYSIS_REPLIES:
                    return {"type": "text", "text": "No problem, I won't save that as a reusable check."}, 200
                # Not a recognizable yes/no at all — the user didn't answer the save
                # prompt, they've moved on to something else (e.g. a completely
                # unrelated follow-up question asked within the same 10-minute
                # window). Before this fix, that case fell through to the "no"
                # reply below, silently discarding the user's real question as
                # an implicit decline for up to 10 minutes. Re-route it fresh
                # instead, same as the analogous schedule/query "moved on"
                # discard above.
                try:
                    reroute_initialized, _reroute_err = self.ensure_vanna_initialized(workspace_id)
                    reroute_ws_meta = get_workspace_metadata(self, workspace_id) or {}
                    ws_name = reroute_ws_meta.get("name")
                    if not reroute_initialized or _dataset_route(clean_question(raw_text), ws_name):
                        route = "query"   # a dataset question isn't an answer to "save this check?"
                    else:
                        route = vn.classify_message_route(raw_text)
                except Exception as reroute_exc:
                    logger.warning(f"Re-routing after stale analysis confirmation failed: {reroute_exc}")
                    route = "query"
                    reroute_ws_meta = {}
                if route == "schedule":
                    # "send this to X" here means the prediction answer just given.
                    last_run = _last_analysis_run_for(workspace_id, username, None)
                    return self._handle_schedule_message(
                        workspace_id, raw_text, last_run["question"] if last_run else None, username, None,
                        prior_kind="prediction" if last_run else None,
                    )
                if route != "prediction":
                    return self._handle_query_message(raw_text, None, workspace_id)
                # route == "prediction": a saved performance config is always a
                # better answer than an ad-hoc one when both could apply (same
                # rationale as route_message's "prediction" branch) — try one
                # before falling through to the normal fresh-match logic below.
                # Found live: a stale "want to save this?" confirmation from
                # an earlier, unrelated prediction/anomaly question left this
                # reroute as the ONLY path a later message like "are exceptions
                # trending up or down?" went through (the early
                # _has_pending_analysis_confirmation check in route_message
                # sends straight here, skipping route_message's own "prediction"
                # branch entirely) — so this path needs the same safety net,
                # not just that one.
                perf_summary_text = self._try_match_performance_config(
                    raw_text, ws_name or workspace_id, reroute_ws_meta, workspace_id, username
                )
                if perf_summary_text is not None:
                    return {"type": "text", "text": perf_summary_text}, 200
                # no performance config matched: fall through to the normal fresh-match logic below.

            initialized, init_err = self.ensure_vanna_initialized(workspace_id)
            if not initialized:
                return {"type": "error", "error": init_err}, 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return {"type": "error", "error": "Workspace not found"}, 404
            workspace_name = workspace.get("name") or str(workspace_id)

            predictions = [p for p in json.loads(workspace.get("predictions", "[]")) if p.get("enabled", True)]
            anomalies = [a for a in json.loads(workspace.get("anomalies", "[]")) if a.get("enabled", True)]
            def _sql_tables(sql):
                # Saved checks often have no table/justification filled in, leaving
                # the matcher only a name to go on — the tables its SQL actually
                # reads say far more about what it's for.
                return ", ".join(dict.fromkeys(
                    m.split(".")[-1].strip("[]")
                    for m in re.findall(r"\b(?:FROM|JOIN)\s+([\w.\[\]]+)", sql or "", re.I)
                )) or None

            configs = (
                [{
                    "kind": "prediction", "type": p.get("type"),
                    "name": p.get("prediction_name") or p.get("type"),
                    "table": p.get("table_names") or _sql_tables(p.get("sql_query")),
                    "predicts": (p.get("parameters") or {}).get("target"),
                    "justification": p.get("justification"),
                } for p in predictions]
                + [{
                    "kind": "anomaly", "type": a.get("type"),
                    "name": a.get("anomaly_name") or a.get("type"),
                    "table": a.get("table_name") or _sql_tables(a.get("sql_query")),
                    "justification": a.get("justification"),
                } for a in anomalies]
            )

            try:
                tables_df = vn.run_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
                tables = tables_df["TABLE_NAME"].tolist() if tables_df is not None and not tables_df.empty else []
            except Exception as table_exc:
                logger.warning(f"Could not list tables for analysis matching: {table_exc}")
                tables = []

            match = vn.match_analysis_config(raw_text, configs, tables)

            # A broken saved check (e.g. its features no longer match its own SQL's
            # columns) used to surface its raw error — "Invalid features or target
            # column." — as the whole reply. The user asked a question, not to run
            # that check: log it for the admin, drop it, and re-match, so another
            # saved check, a fresh one, or plain SQL can still answer. Terminates:
            # each pass removes one config, and a match must name a remaining one.
            while match.get("matched"):
                kind = match["kind"]
                cfg_type = match["type"]
                matched_cfg = next((c for c in (predictions if kind == "prediction" else anomalies) if c.get("type") == cfg_type), {})
                if kind == "prediction":
                    body, status = _run_prediction_config(workspace_id, cfg_type)
                    rows = body.get("df") if status == 200 else None
                else:
                    body, status = _run_anomaly_config(workspace_id, cfg_type)
                    rows = body.get("results") if status == 200 else None

                if status == 200:
                    _remember_analysis_run(pending_key, raw_text, kind, matched_cfg)
                    name = matched_cfg.get("prediction_name") or matched_cfg.get("anomaly_name") or cfg_type
                    matched_reply = _summarize_analysis_result(rows, name, workspace_name, kind, matched_cfg.get("sql_query"))
                    if body.get("truncated"):
                        matched_reply["text"] = f"{matched_reply['text']}\n\n{body['truncated_note']}"
                    return matched_reply, 200

                logger.warning(
                    f"Saved {kind} check {cfg_type!r} matched {raw_text!r} but failed to run: "
                    f"{body.get('error')} — trying without it.",
                    extra={"admin": True},
                )
                configs = [c for c in configs if not (c.get("kind") == kind and c.get("type") == cfg_type)]
                match = vn.match_analysis_config(raw_text, configs, tables)

            # No existing config matched — generate one on the fly.
            kind = match.get("kind", "prediction")
            table = match.get("suggested_table")
            if not table:
                return _fallback_to_query_or(
                    "I don't have enough documented tables in this workspace to build that check "
                    "yet — ask your admin to add table documentation first."
                )

            try:
                if kind == "prediction":
                    suggestion_raw, *_rest = vn.get_prediction_suggestions(table=table, user_query=raw_text, workspace=workspace_name)
                else:
                    suggestion_raw, *_rest = vn.get_anomaly_suggestions(table=table, user_query=raw_text, workspace=workspace_name)
            except Exception as suggest_exc:
                logger.error(f"Failed to generate {kind} suggestion for table {table}: {suggest_exc}")
                return _fallback_to_query_or(f"Couldn't build a {kind} check for that: {suggest_exc}")

            try:
                parsed = json.loads(suggestion_raw)
                suggestion = parsed[0] if isinstance(parsed, list) and parsed else (parsed if isinstance(parsed, dict) else None)
            except Exception:
                suggestion = None
            if not suggestion:
                return _fallback_to_query_or(
                    f"I couldn't work out a reliable {kind} check for that yet — try rephrasing, "
                    f"or ask your admin to add one from the dashboard."
                )

            name_field = "prediction_name" if kind == "prediction" else "anomaly_name"
            table_field = "table_names" if kind == "prediction" else "table_name"
            name = suggestion.get(name_field) or f"{kind}_{table}"
            cfg_type = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') or f"{kind}_{table}".lower()
            config = {
                "type": cfg_type,
                name_field: name,
                table_field: table,
                "algorithm": suggestion.get("algorithm"),
                "sql_query": suggestion.get("sql_query"),
                "parameters": suggestion.get("parameters") or {},
                "justification": suggestion.get("justification"),
                "enabled": True,
            }

            if kind == "prediction":
                body, status = _run_prediction_config(workspace_id, config=config)
                rows = body.get("df") if status == 200 else None
            else:
                body, status = _run_anomaly_config(workspace_id, config=config)
                rows = body.get("results") if status == 200 else None

            if status != 200:
                # A freshly-generated (not yet saved) config can fail for many
                # reasons — no data, or the LLM's suggested SQL referencing a
                # column that doesn't actually exist despite the suggestion
                # prompt being told to use only documented columns (seen live:
                # a hallucinated column name on a real table). Whatever the
                # cause, the raw SQL/pyodbc error is not something a chat user
                # should see — log it for debugging and reply with one clean
                # message either way; the "insufficient data" phrasing below
                # covers a real no-data case well enough without being wrong
                # for the "bad SQL" case (both mean "I couldn't build a
                # reliable check for that").
                logger.warning(f"Freshly-generated {kind} check for table {table} failed to run: {body.get('error')}")
                return _fallback_to_query_or(
                    f"I wasn't able to build a reliable {kind} check for that yet — try rephrasing, "
                    f"or ask your admin to set one up from the dashboard."
                )

            _remember_analysis_run(pending_key, raw_text, kind, config)
            reply = _summarize_analysis_result(rows, name, workspace_name, kind, config.get("sql_query"))
            if body.get("truncated"):
                reply["text"] = f"{reply['text']}\n\n{body['truncated_note']}"
            reply["text"] = (
                f"{reply['text']}\n\nThis isn't a saved check yet — want me to save it as \"{name}\" "
                f"for reuse? Reply yes to save."
            )

            with _pending_analysis_confirmations_lock:
                _pending_analysis_confirmations[pending_key] = {
                    "kind": kind,
                    "config": config,
                    "created_at": time.time(),
                }
            return reply, 200

        # Exposed on self for the same reason as self._handle_schedule_message
        # above — lets _handle_query_message hand off here if a resumed query
        # clarification turns out to be a prediction/anomaly request instead.
        self._handle_prediction_message = _handle_prediction_message

        def _try_performance_or_methodology_before_prediction(workspace_id, raw_text, username):
            """
            Shared gate for every entry point that has labeled a message
            "prediction" before it reaches the ad-hoc prediction/anomaly
            pipeline (_handle_prediction_message) — classify_message_route
            reads "trend"/"abnormal pattern" language the same way for a
            management performance question ("are exceptions trending up or
            down?") as it does for a genuine ad-hoc anomaly request. An
            admin-validated performance config, or an existing check's
            methodology explanation, is always a better answer than a fresh
            ad-hoc check when either applies, so try both here first.

            Originally inlined in route_message's "prediction" branch only —
            found live that the web chat UI never calls route_message for an
            ordinary typed message at all; it calls classify_message_route_
            endpoint to get the label, then POSTs straight to
            run_matched_analysis_route for a "prediction" label, which had
            none of this and went directly to _handle_prediction_message. The
            route_message branch's fix was effectively dead for the actual
            browser chat.

            Returns (body_dict, status) if answered here, else None — None
            means "fall through to _handle_prediction_message".
            """
            ws_meta = get_workspace_metadata(self, workspace_id) or {}
            ws_name = ws_meta.get("name")
            perf_summary_text = self._try_match_performance_config(
                raw_text, ws_name or workspace_id, ws_meta, workspace_id, username
            )
            if perf_summary_text is not None:
                return {"type": "text", "text": perf_summary_text}, 200
            if _METHODOLOGY_CUE.search(raw_text):
                # A methodology question can carry a prediction/anomaly cue
                # word itself ("how is the order volume FORECAST calculated?",
                # "how is this ANOMALY check done?") — without this,
                # _handle_prediction_message would match its own saved config
                # by name and actually RE-RUN the forecast/anomaly check
                # instead of explaining it.
                analysis_kind, analysis_config = self._try_match_analysis_methodology(
                    raw_text, ws_meta, workspace_id, username
                )
                if analysis_config:
                    analysis_explanation = vn.generate_analysis_methodology_explanation(
                        raw_text, analysis_kind, analysis_config
                    )
                    if analysis_explanation:
                        return {"type": "text", "text": analysis_explanation}, 200
            return None

        @self.flask_app.route('/api/v0/run_matched_analysis', methods=['POST'])
        @self.requires_auth
        def run_matched_analysis_route(user=None):
            """
            Chat entry point for prediction/anomaly questions — see
            _handle_prediction_message for the actual logic.
            """
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            raw_text = (data.get('text') or '').strip()

            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
            if not workspace_id or not username:
                return jsonify({"type": "error", "error": "workspace_id and an authenticated user are required"}), 400
            if not raw_text:
                return jsonify({"type": "error", "error": "No message provided"}), 400

            # vn is bound per-thread by ensure_vanna_initialized (see its
            # docstring) — this route previously never called it itself,
            # relying entirely on some earlier request having already bound
            # vn on whichever waitress worker thread picks this one up.
            # Found live: a worker thread that hadn't yet served a request
            # going through classify_message_route_endpoint/route_message
            # (which do call it) hit "'_OpenAIVanna' object has no attribute
            # 'client'" the moment _try_performance_or_methodology_before_
            # prediction's performance-config match tried its first LLM
            # call — exactly the failure mode ensure_vanna_initialized exists
            # to prevent everywhere else in this file.
            initialized, init_err = self.ensure_vanna_initialized(workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": init_err}), 400

            # A pending "save this check?" confirmation must be resolved by
            # _handle_prediction_message directly — a bare "yes"/"no" reply
            # (or a "how is this calculated?" about the check just shown,
            # which _handle_prediction_message already handles against
            # pending["config"]) isn't a fresh question to re-match against
            # performance configs.
            if _has_pending_analysis_confirmation(workspace_id, username):
                result = None
            else:
                result = _try_performance_or_methodology_before_prediction(workspace_id, raw_text, username)
            if result is not None:
                body, status = result
            else:
                body, status = _handle_prediction_message(workspace_id, raw_text, username)
            return jsonify(body), status

        # ============= end prediction/anomaly chat integration =============

        @self.flask_app.route('/api/v0/slash_command', methods=['POST'])
        @self.requires_auth
        def slash_command_route(user=None):
            """
            Single entry point for every "/"-prefixed chat message. Fixed literals
            (list / stop <id> / email <address>) are handled deterministically with
            no LLM call; anything else costs exactly one extract_schedule_request
            call. Strictly read-only — a write-classified request is hard-rejected,
            never staged or downgraded. See _handle_schedule_message, which is
            also called by route_message for natural-language (no "/") dispatch.
            """
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            raw_text = (data.get('text') or '').strip()
            prior_question = data.get('prior_question')
            prior_sql = data.get('prior_sql')
            main_question = data.get('main_question')

            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
            if not workspace_id or not username:
                return jsonify({"type": "error", "error": "workspace_id and an authenticated user are required"}), 400

            # "/warehouse ..." belongs to the Warehouse Performance Agent; everything else is unchanged.
            _wpa = getattr(self, "warehouse_perf", None)
            if _wpa is not None and _wpa.is_warehouse_command(raw_text):
                body, status = _wpa.handle_chat(user, workspace_id, raw_text)
                return jsonify(body), status

            body, status = _handle_schedule_message(workspace_id, raw_text, prior_question, username, prior_sql, main_question=main_question, prior_kind=data.get('prior_kind'))
            return jsonify(body), status

        @self.flask_app.route('/api/v0/route_message', methods=['POST'])
        @self.requires_auth
        def route_message(user=None):
            """
            Single natural-language entry point for chat: classifies the raw
            message (vn.classify_message_route) as a scheduling/condition
            request or an ordinary data question and dispatches to the same
            underlying logic as slash_command_route / generate_sql — no "/"
            prefix required. An explicit leading "/" is still honored as a
            fast path that skips the classifier call. Deliberately
            channel-agnostic: any future entry point (Teams, voice) can drive
            the same routing by POSTing raw text here.
            """
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            workspace = data.get('workspace') or workspace_id
            raw_text = (data.get('text') or '').strip()
            prior_question = data.get('prior_question')
            previous_sql = data.get('sql')
            main_question = data.get('main_question')

            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
            if not workspace_id or not username:
                return jsonify({"type": "error", "error": "workspace_id and an authenticated user are required"}), 400
            if not raw_text:
                return jsonify({"type": "error", "error": "No message provided"}), 400

            _wpa = getattr(self, "warehouse_perf", None)
            if _wpa is not None and _wpa.is_warehouse_command(raw_text):
                body, status = _wpa.handle_chat(user, workspace_id, raw_text)
                return jsonify(body), status

            if raw_text.startswith('/') or _has_pending_clarification(workspace_id, username, raw_text):
                body, status = _handle_schedule_message(workspace_id, raw_text, prior_question, username, previous_sql, main_question=main_question, prior_kind=data.get('prior_kind'))
                return jsonify(body), status

            if _has_pending_analysis_confirmation(workspace_id, username):
                body, status = _handle_prediction_message(workspace_id, raw_text, username)
                return jsonify(body), status

            if _has_pending_query_clarification(workspace_id, username):
                body, status = self._handle_query_message(raw_text, previous_sql, workspace)
                return jsonify(body), status

            # vn is a lazily-initialized global — on a fresh process this may be
            # the very first request to touch it. Found live: calling this
            # route before any other request had initialized vn crashed with
            # AttributeError: 'NoneType' object has no attribute
            # 'classify_message_route' instead of a clean error. Same fix
            # already applied to classify_message_route_endpoint above.
            initialized, init_err = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": init_err}), 400

            # Trained question → its stored SQL, never an LLM re-route.
            ws_meta = get_workspace_metadata(self, workspace_id) or {}
            ws_name = ws_meta.get("name")
            if _dataset_route(clean_question(raw_text), ws_name):
                route = "query"
            else:
                route = vn.classify_message_route(raw_text)
            if route == "schedule":
                body, status = _handle_schedule_message(workspace_id, raw_text, prior_question, username, previous_sql, main_question=main_question, prior_kind=data.get('prior_kind'))
            elif route == "prediction":
                # Admin-validated performance config / methodology explanation
                # before the ad-hoc prediction/anomaly pipeline — see
                # _try_performance_or_methodology_before_prediction.
                result = _try_performance_or_methodology_before_prediction(workspace_id, raw_text, username)
                if result is not None:
                    body, status = result
                else:
                    body, status = _handle_prediction_message(workspace_id, raw_text, username)
            else:
                body, status = self._handle_query_message(raw_text, previous_sql, workspace)
            return jsonify(body), status

        def run_chat_turn(ctx, text, state=None):
            """
            One complete chat turn for a caller with no HTTP session (Teams).
            Routes exactly like route_message; then, unlike the web flow (where
            the browser drives run_sql / generate_summary as separate calls),
            also runs the query and summarizes it, so the channel gets a full
            answer in one reply.

            Must be called with ctx.workspace_id's Vanna instance bound to the
            current thread (vn.bound_to), e.g. by the Teams bot's worker pool.

            state: per-conversation dict carrying follow-up context between
            turns ("previous_sql", "prior_question"); updated in place.

            Returns a dict with "kind" = "answer" | "text" | "write_confirmation" | "error":
              answer:              text (summary), columns, rows (<=10), total_rows, sql, language, question_id
              text / error:        text
              write_confirmation:  text (SQL), write_id, preview, question
            """
            state = state if state is not None else {}
            raw_text = (text or "").strip()
            if not raw_text:
                return {"kind": "error", "text": "No message provided"}

            prior_question = state.get("prior_question")
            previous_sql = state.get("previous_sql")

            if raw_text.startswith('/') or _has_pending_clarification(ctx.workspace_id, ctx.username, raw_text):
                route = "schedule"
            elif _dataset_route(clean_question(raw_text), ctx.workspace_name):
                route = "query"   # trained question (or close rephrasing) → answered from the dataset
            else:
                route = vn.classify_message_route(raw_text)

            if route == "schedule":
                body, _status = _handle_schedule_message(
                    ctx.workspace_id, raw_text, prior_question, ctx.username, previous_sql, ctx=ctx
                )
                is_error = body.get("type") == "error"
                return {"kind": "error" if is_error else "text", "text": body.get("error") if is_error else body.get("text", "")}

            body, _status = self._handle_query_message(raw_text, previous_sql, ctx.workspace_name, ctx=ctx)
            body_type = body.get("type")
            if body_type == "write_confirmation":
                return {
                    "kind": "write_confirmation",
                    "text": body.get("text"),
                    "write_id": body.get("write_id"),
                    "preview": body.get("preview") or {},
                    "question": body.get("original_question") or raw_text,
                }
            if body_type != "sql":
                # "Insufficient data for query." and other non-SQL answers.
                is_error = body_type == "error"
                return {"kind": "error" if is_error else "text", "text": body.get("error") if is_error else body.get("text", "")}

            sql = body["text"]
            question_id = body.get("id")
            language = body.get("detected_language") or "en"
            question_en = body.get("translated_question") or raw_text

            try:
                df = vn.run_sql(sql=sql)
            except TimeoutError:
                return {"kind": "error", "sql": sql,
                        "text": "The query ran for more than 15 seconds and was stopped to protect the database. Try narrowing it down."}
            except Exception as e:
                logger.error(f"run_chat_turn: SQL execution failed: {e}", exc_info=True, extra={"admin": True})
                return {"kind": "error", "sql": sql, "text": friendly_sql_error(str(e))}

            state["previous_sql"] = sql
            state["prior_question"] = raw_text

            if df is None or df.empty:
                return {
                    "kind": "answer", "text": translate_text("No data available for your request.", language),
                    "columns": [], "rows": [], "total_rows": 0, "sql": sql,
                    "language": language, "question_id": question_id,
                }

            summary = ""
            try:
                summary_en, total, inp, out, model = vn.generate_summary(
                    question=question_en, df=df, sql=sql, workspace=ctx.workspace_name
                )
                summary = translate_text(summary_en, language)
                cost_usd = self.log_token_count(
                    question_id=question_id, total_tokens=total, input_tokens=inp,
                    output_tokens=out, model_name=model, cached_input_tokens=0, user_id=ctx.user_id,
                )
                self.log_user_activity(
                    question_id=question_id, question=raw_text, sql_query=sql, summary=summary,
                    workspace_name=ctx.workspace_name, workspace_id=ctx.workspace_id,
                    user_role=ctx.username, user_id=ctx.user_id, token_count=total,
                    input_tokens=inp, output_tokens=out, model_name=model,
                    cost_usd=cost_usd, detected_language=language,
                )
            except Exception as e:
                logger.error(f"run_chat_turn: summary failed: {e}", exc_info=True, extra={"admin": True})

            return {
                "kind": "answer",
                "text": summary,
                "columns": [str(c) for c in df.columns],
                # to_json handles numpy types, NaN -> null and timestamps -> ISO strings.
                "rows": json.loads(df.head(10).to_json(orient="records", date_format="iso")),
                "total_rows": int(len(df)),
                "sql": sql,
                "language": language,
                "question_id": question_id,
            }

        self.run_chat_turn = run_chat_turn

        @self.flask_app.route('/api/v0/classify_message_route', methods=['POST'])
        @self.requires_auth
        def classify_message_route_endpoint(user=None):
            """
            Classification-only counterpart to route_message: given raw chat text,
            says whether it's a scheduling/condition request or an ordinary data
            question, without executing either path. The chat UI (index.js's uT())
            calls this to decide between handleSlashCommand (scheduling) and its
            existing generate_sql flow (query) — that query flow's rewritten-question
            and get_function steps are frontend-only orchestration and would be lost
            if every message were instead sent straight through route_message.

            Also forces "schedule" whenever this user/workspace has an open
            clarification pending (e.g. they were just asked "what would you like
            me to send you?"), and forces "prediction" whenever there's a pending
            save-this-check confirmation — a bare "the sales report" or "yes"
            reply wouldn't otherwise obviously classify as scheduling/prediction
            on its own.
            """
            data = request.get_json() or {}
            raw_text = (data.get('text') or '').strip()
            workspace_id = data.get('workspace_id')
            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)

            if not raw_text:
                return jsonify({"type": "route", "route": "query"})
            if raw_text.startswith('/'):
                return jsonify({"type": "route", "route": "schedule"})
            if workspace_id and username and _has_pending_clarification(workspace_id, username, raw_text):
                return jsonify({"type": "route", "route": "schedule"})

            # vn is a lazily-initialized global — on a fresh process this may be
            # the very first request to touch it. Fail open to "query" (the
            # existing RAG flow already handles an un-initialized vn with its
            # own clear error) rather than a raw 500 if init fails.
            initialized, _init_err = ensure_vanna_initialized(self, workspace_id) if workspace_id else (False, "no workspace_id")

            # A trained question, or a close rephrasing of one, is answered from
            # the dataset. Checked before a pending "save this check?" prompt and
            # before the LLM classifier, which both used to send questions like
            # "Show me orders at risk of missing delivery" to the prediction
            # pipeline. "trained" (exact only) lets the chat skip its follow-up
            # rewrite step: the stored SQL answers the question as asked.
            if initialized:
                ws_meta = get_workspace_metadata(self, workspace_id) or {}
                dataset = _dataset_route(clean_question(raw_text), ws_meta.get("name"))
                if dataset:
                    return jsonify({"type": "route", "route": "query", "trained": dataset == "exact"})

            # "send this to X" after a prediction is a delivery request, not an
            # answer to its "save this check?" prompt.
            if (workspace_id and username and not DELIVERY_CUES.search(raw_text)
                    and _has_pending_analysis_confirmation(workspace_id, username)):
                return jsonify({"type": "route", "route": "prediction"})
            if workspace_id and username and _has_pending_query_clarification(workspace_id, username):
                return jsonify({"type": "route", "route": "query"})
            if not initialized:
                return jsonify({"type": "route", "route": "query"})
            return jsonify({"type": "route", "route": vn.classify_message_route(raw_text)})

        @self.flask_app.route('/api/v0/scheduled_agents', methods=['GET'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def list_scheduled_agents_route(user=None):
            workspace_id = request.args.get('workspace_id')
            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400

            metadata, records = _get_schedule_records(workspace_id)
            if metadata is None:
                return jsonify({"type": "error", "error": "Workspace not found"}), 404

            # Monitoring view: every agent in the workspace, not just the
            # requester's own — that's the actual point of "how many crons
            # are running", unlike chat's /list which is deliberately scoped
            # to the asking user.
            agents = [
                {
                    "schedule_id": r.get("schedule_id"),
                    "owner_username": r.get("owner_username"),
                    "display_question": r.get("display_question"),
                    "channel": r.get("channel"),
                    "email_recipients": r.get("email_recipients") or [],
                    "schedule_type": r.get("schedule", {}).get("type"),
                    "description": _describe_schedule(r.get("schedule", {})),
                    "enabled": bool(r.get("enabled")),
                    "status_suffix": _status_suffix(r),
                    "last_status": r.get("last_status"),
                    "last_error": r.get("last_error"),
                    "last_run_at": r.get("last_run_at"),
                    "run_count": r.get("run_count", 0),
                    "created_at": r.get("created_at"),
                }
                for r in (records or [])
            ]
            agents.sort(key=lambda a: a.get("created_at") or 0, reverse=True)
            return jsonify({"agents": agents})

        @self.flask_app.route('/api/v0/scheduled_agents/stop', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def stop_scheduled_agent_route(user=None):
            data = request.json or {}
            workspace_id = data.get('workspace_id')
            schedule_id = data.get('schedule_id')
            if not workspace_id or not schedule_id:
                return jsonify({"type": "error", "error": "workspace_id and schedule_id are required"}), 400

            with _get_schedule_records_lock(workspace_id):
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404
                record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                if not record:
                    return jsonify({"type": "error", "error": f"No scheduled agent {schedule_id} found."}), 404

                # Unlike chat's /stop, an admin may stop any user's agent here.
                record["enabled"] = False
                try:
                    scheduled_agents_scheduler.remove_job(schedule_id)
                except JobLookupError:
                    pass
                _save_schedule_records(workspace_id, metadata, records)
            return jsonify({"success": True})

        @self.flask_app.route('/api/v0/scheduled_agents/resume', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def resume_scheduled_agent_route(user=None):
            data = request.json or {}
            workspace_id = data.get('workspace_id')
            schedule_id = data.get('schedule_id')
            if not workspace_id or not schedule_id:
                return jsonify({"type": "error", "error": "workspace_id and schedule_id are required"}), 400

            with _get_schedule_records_lock(workspace_id):
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404
                record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                if not record:
                    return jsonify({"type": "error", "error": f"No scheduled agent {schedule_id} found."}), 404

                schedule = record.get("schedule", {})
                if schedule.get("type") == "date":
                    # A one-time run already fired (or was stopped before it could) —
                    # there's nothing recurring left to resume.
                    return jsonify({"type": "error", "error": "This was a one-time agent — create a new one instead of resuming it."}), 400

                try:
                    trigger = _build_schedule_trigger(schedule)
                except Exception as trigger_exc:
                    return jsonify({"type": "error", "error": f"Couldn't rebuild that schedule: {trigger_exc}"}), 400

                record["enabled"] = True
                scheduled_agents_scheduler.add_job(
                    func=_run_scheduled_question,
                    args=[workspace_id, schedule_id],
                    trigger=trigger,
                    id=schedule_id,
                    max_instances=1,
                    coalesce=True,
                    replace_existing=True,
                    misfire_grace_time=120,
                )
                _save_schedule_records(workspace_id, metadata, records)
            return jsonify({"success": True})

        @self.flask_app.route('/api/v0/scheduled_agents/delete', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def delete_scheduled_agent_route(user=None):
            data = request.json or {}
            workspace_id = data.get('workspace_id')
            schedule_id = data.get('schedule_id')
            if not workspace_id or not schedule_id:
                return jsonify({"type": "error", "error": "workspace_id and schedule_id are required"}), 400

            with _get_schedule_records_lock(workspace_id):
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404
                record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                if not record:
                    return jsonify({"type": "error", "error": f"No scheduled agent {schedule_id} found."}), 404

                try:
                    scheduled_agents_scheduler.remove_job(schedule_id)
                except JobLookupError:
                    pass
                records = [r for r in records if r.get("schedule_id") != schedule_id]
                _save_schedule_records(workspace_id, metadata, records)
            return jsonify({"success": True})

        @self.flask_app.route('/api/v0/scheduled_agents/update_recipients', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def update_scheduled_agent_recipients_route(user=None):
            """
            Lets an admin assign or change WHO an existing scheduled/conditional
            agent sends to, without recreating it — found missing during manual
            conditional-agent testing (the admin panel showed Stop/Resume/Delete but
            no way to see or edit the recipient, and a chat-channel agent had no
            recipient at all — it silently fell back to notifying whoever happened
            to be its owner). Works on ANY agent regardless of its current channel:
            assigning one or more recipients here converts it to email delivery
            going to those addresses specifically, replacing the owner-chat-inbox
            fallback. Only accepts addresses already registered in the workspace's
            email config (same "never invent a recipient" policy used when a
            schedule is first created via chat).
            """
            data = request.json or {}
            workspace_id = data.get('workspace_id')
            schedule_id = data.get('schedule_id')
            submitted = data.get('email_recipients')
            if not workspace_id or not schedule_id:
                return jsonify({"type": "error", "error": "workspace_id and schedule_id are required"}), 400
            if not isinstance(submitted, list):
                return jsonify({"type": "error", "error": "email_recipients must be a list"}), 400

            with _get_schedule_records_lock(workspace_id):
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return jsonify({"type": "error", "error": "Workspace not found"}), 404
                record = next((r for r in records if r.get("schedule_id") == schedule_id), None)
                if not record:
                    return jsonify({"type": "error", "error": f"No scheduled agent {schedule_id} found."}), 404

                registered = {e.get("address") for e in _get_workspace_emails(workspace_id) if e.get("address")}
                cleaned = []
                for addr in submitted:
                    addr = addr.strip() if isinstance(addr, str) else ""
                    if not addr:
                        continue
                    if addr not in registered:
                        return jsonify({"type": "error", "error": f"'{addr}' isn't a registered recipient for this workspace."}), 400
                    if addr not in cleaned:
                        cleaned.append(addr)
                if not cleaned:
                    return jsonify({"type": "error", "error": "At least one recipient is required."}), 400

                record["email_recipients"] = cleaned
                record["channel"] = "email"
                _save_schedule_records(workspace_id, metadata, records)
            return jsonify({"success": True, "email_recipients": cleaned, "channel": "email"})

        @self.flask_app.route('/api/v0/scheduled_questions/poll', methods=['POST'])
        @self.requires_auth
        def scheduled_questions_poll_route(user=None):
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
            if not workspace_id or not username:
                return jsonify({"type": "error", "error": "workspace_id and an authenticated user are required"}), 400

            with _get_schedule_records_lock(workspace_id):
                metadata, records = _get_schedule_records(workspace_id)
                if metadata is None:
                    return jsonify({"type": "schedule_results", "messages": []})

                messages = []
                changed = False
                for r in records:
                    if r.get("owner_username") != username:
                        continue
                    inbox = r.get("chat_inbox") or []
                    if inbox:
                        for entry in inbox:
                            messages.append({
                                "schedule_id": r["schedule_id"],
                                "text": entry.get("text", ""),
                                "created_at": entry.get("created_at"),
                            })
                        r["chat_inbox"] = []
                        changed = True

                if changed:
                    _save_schedule_records(workspace_id, metadata, records)

            return jsonify({"type": "schedule_results", "messages": messages})

        def _get_workspace_emails(workspace_id):
            """
            Admin-configured named email recipients for a workspace (Email Recipients
            section of the DB config panel) — any user in the workspace can read this
            to reference a label when scheduling ("send to my manager"); only an
            admin/superadmin can change it (see save_workspace_email_config_route).
            """
            try:
                results = self.workspace_collection.get(ids=[str(workspace_id)])
                if not results or not results.get("metadatas"):
                    return []
                return json.loads(results["metadatas"][0].get("email_recipients", "[]"))
            except Exception as e:
                logger.error(f"Error reading workspace email config for {workspace_id}: {e}", extra={"admin": True})
                return []

        @self.flask_app.route('/api/v0/get_workspace_email_config', methods=['GET'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def get_workspace_email_config_route(user=None):
            workspace_id = request.args.get('workspace_id')
            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400
            return jsonify({"type": "success", "emails": _get_workspace_emails(workspace_id)})

        @self.flask_app.route('/api/v0/save_workspace_email_config', methods=['POST'])
        @self.requires_auth
        @self.requires_role(["admin", "superadmin"])
        def save_workspace_email_config_route(user=None):
            data = request.get_json() or {}
            workspace_id = data.get('workspace_id')
            submitted = data.get('emails') or []
            if not workspace_id:
                return jsonify({"type": "error", "error": "workspace_id is required"}), 400
            if not isinstance(submitted, list):
                return jsonify({"type": "error", "error": "emails must be a list"}), 400
            if len(submitted) > 50:
                return jsonify({"type": "error", "error": "A workspace can have at most 50 email recipients."}), 400

            address_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
            seen_labels = set()
            normalized = []
            for entry in submitted:
                label = (entry.get("label") or "").strip() if isinstance(entry, dict) else ""
                address = (entry.get("address") or "").strip() if isinstance(entry, dict) else ""
                if not label or not address:
                    continue
                if label.lower() == "all":
                    return jsonify({"type": "error", "error": "\"all\" is reserved to mean every recipient — pick a different label."}), 400
                if label.lower() in seen_labels:
                    return jsonify({"type": "error", "error": f"Duplicate label \"{label}\" — labels must be unique."}), 400
                if not address_re.match(address):
                    return jsonify({"type": "error", "error": f"\"{address}\" doesn't look like a valid email address."}), 400
                seen_labels.add(label.lower())
                normalized.append({"label": label, "address": address})

            existing = self.workspace_collection.get(ids=[str(workspace_id)])
            if not existing or not existing.get("metadatas"):
                return jsonify({"type": "error", "error": "Workspace not found"}), 404

            metadata = existing["metadatas"][0]
            metadata["email_recipients"] = json.dumps(normalized)
            self.workspace_collection.update(
                ids=[str(workspace_id)],
                metadatas=[metadata],
                documents=[f"Workspace: {metadata.get('name', workspace_id)}"],
            )
            logger.info(f"Saved {len(normalized)} email recipient(s) for workspace {workspace_id}", extra={"admin": True})
            return jsonify({"type": "success", "emails": normalized})

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

        @self.flask_app.route('/save_performance_config', methods=['POST'])
        def save_performance_config():
            """
            Save or update performance-check configurations for a workspace —
            same upsert-by-type shape as save_anomaly_config/save_prediction_config.

            Expects a JSON payload with:
            - workspace_id: The ID of the workspace.
            - performance: A list of performance configurations, each containing:
              - type: Unique identifier (lowercase, underscored).
              - name/description: Human-readable summary of what it computes,
                used by match_performance_config to decide if a chat question
                matches it.
              - sql_query: The validated SELECT/WITH SQL to run (no stored
                procedure call — see is_select_only_sql).
              - enabled: Boolean.
            """
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            new_checks = data.get('performance', [])

            if not workspace_id:
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                existing_checks = json.loads(workspace.get("performance", "[]"))
                for new_check in new_checks:
                    perf_type = new_check.get("type")
                    if not perf_type:
                        return jsonify({"type": "error", "error": "Performance check type is required."}), 400
                    sql_query = new_check.get("sql_query")
                    if not sql_query:
                        return jsonify({"type": "error", "error": "Performance check sql_query is required."}), 400
                    is_safe, reason = vn.is_select_only_sql(sql_query)
                    if not is_safe:
                        return jsonify({"type": "error", "error": f"sql_query failed validation: {reason}"}), 400

                    existing_idx = next((i for i, c in enumerate(existing_checks) if c["type"] == perf_type), -1)
                    if existing_idx >= 0:
                        existing_checks[existing_idx] = new_check
                    else:
                        existing_checks.append(new_check)

                workspace["performance"] = json.dumps(existing_checks)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Saved performance config for workspace: ID={workspace_id}")
                return jsonify({"type": "success", "message": "Performance checks saved successfully."})
            except Exception as e:
                logger.error(f"Failed to save performance checks: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to save performance checks: {str(e)}"}), 500

        @self.flask_app.route('/delete_performance_config', methods=['POST'])
        def delete_performance_config():
            data = request.get_json()
            workspace_id = data.get('workspace_id')
            performance_type = data.get('performance_type')

            if not workspace_id or not performance_type:
                return jsonify({"type": "error", "error": "Workspace ID and performance type are required."}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                existing_checks = json.loads(workspace.get("performance", "[]"))
                updated_checks = [p for p in existing_checks if p.get("type") != performance_type]

                workspace["performance"] = json.dumps(updated_checks)
                self.workspace_collection.update(
                    ids=[str(workspace_id)],
                    metadatas=[workspace],
                    documents=[f"Workspace: {workspace['name']}"]
                )
                logger.info(f"Deleted performance check '{performance_type}' for workspace ID={workspace_id}")
                return jsonify({"type": "success", "message": "Performance check deleted successfully."})
            except Exception as e:
                logger.error(f"Failed to delete performance check: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to delete performance check: {str(e)}"}), 500

        @self.flask_app.route('/api/v0/get_performance_configs', methods=['GET'])
        def get_performance_configs():
            workspace_id = request.args.get('workspace_id')
            logger.info(f"Fetching performance configs for workspace ID: {workspace_id}")
            if not workspace_id:
                return jsonify({"type": "error", "error": "Workspace ID is required."}), 400

            initialized, error = ensure_vanna_initialized(self, workspace_id)
            if not initialized:
                return jsonify({"type": "error", "error": error}), 400

            workspace = get_workspace_metadata(self, workspace_id)
            if not workspace:
                return jsonify({"type": "error", "error": "Workspace not found."}), 404

            try:
                performance_raw = workspace.get("performance", "[]")
                performance = json.loads(performance_raw)
                if not isinstance(performance, list):
                    logger.warning(f"Invalid performance format for workspace {workspace_id}: {performance_raw}")
                    performance = []
                return jsonify({"type": "success", "performance": performance})
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse performance configs for workspace {workspace_id}: {str(e)}")
                return jsonify({"type": "error", "error": "Failed to parse performance configs: Invalid JSON format."}), 500
            except Exception as e:
                logger.error(f"Unexpected error in get_performance_configs for workspace {workspace_id}: {str(e)}", exc_info=True)
                return jsonify({"type": "error", "error": f"Failed to retrieve performance configs: {str(e)}"}), 500


        def _resolve_column(name, columns):
            """
            Maps a config's feature/target name to a column the SQL actually
            returns. Saved suggestions often name features the way the SQL wrote
            them before aliasing — "po.create_date", "po.status" (selected AS
            po_status), "pod.qty" (selected AS ordered_qty) — none of which is a
            result column, so every run failed with "Invalid features or target
            column." Tries: exact; without the alias prefix; prefix_column; then
            the single column ending in _column. Returns None when ambiguous or
            absent rather than guessing.
            """
            if not name:
                return None
            if name in columns:
                return name
            prefix, _, bare = name.rpartition(".")
            if bare in columns:
                return bare
            if prefix and f"{prefix}_{bare}" in columns:
                return f"{prefix}_{bare}"
            suffixed = [c for c in columns if str(c).endswith(f"_{bare}")]
            return suffixed[0] if len(suffixed) == 1 else None

        def _coerce_numeric_features(df, columns):
            """
            Every ML algorithm below (linear/logistic regression, isolation forest,
            DBSCAN) needs a purely numeric feature matrix — but a prediction/anomaly
            config's SQL is free to select a date or a text/categorical column as a
            "feature" (e.g. a suggested query grouping by a formatted month string),
            which is often exactly the meaningful column for that use case. Found
            live: a suggestion using a 'year_month' string column ('2019-05') as a
            feature crashed with "could not convert string to float" instead of
            ever producing a prediction. Converts in place: a datetime column
            becomes its ordinal day number; anything else non-numeric is
            label-encoded (pandas.factorize) into an integer code — lossy for a
            model that would benefit from true one-hot encoding, but turns a hard
            crash into a working (if simplistic) prediction, which is the actual
            goal here.
            """
            for col in columns:
                if col not in df.columns:
                    continue
                series = df[col]
                if pd.api.types.is_numeric_dtype(series):
                    continue
                if pd.api.types.is_datetime64_any_dtype(series):
                    df[col] = series.map(lambda d: d.toordinal() if pd.notnull(d) else None)
                    continue
                try:
                    parsed_dates = pd.to_datetime(series, errors="raise")
                    df[col] = parsed_dates.map(lambda d: d.toordinal() if pd.notnull(d) else None)
                except Exception:
                    codes, _ = pd.factorize(series)
                    df[col] = codes
            return df

        def _is_safe_eval_rule(rule, allowed_columns):
            """
            Validates a "custom" anomaly rule is a pure boolean/comparison
            expression over real columns — no function calls, attribute access,
            or subscripts, which is how a pandas df.eval() expression could
            otherwise reach outside the expression itself. Walking the AST
            (rather than blocklisting specific syntax) rejects every node shape
            not explicitly allowed, so there's nothing left to enumerate around.

            Returns (True, "") if safe to pass to df.eval(), else (False, reason).
            """
            try:
                tree = ast.parse(rule, mode="eval")
            except SyntaxError as exc:
                return False, f"Not a valid expression: {exc}"

            allowed_node_types = (
                ast.Expression, ast.Compare, ast.BoolOp, ast.BinOp, ast.UnaryOp,
                ast.Name, ast.Load, ast.Constant,
                ast.And, ast.Or, ast.Not,
                ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd,
            )
            for node in ast.walk(tree):
                if not isinstance(node, allowed_node_types):
                    return False, f"'{type(node).__name__}' is not permitted in a custom rule"
                if isinstance(node, ast.Name) and node.id not in allowed_columns:
                    return False, f"'{node.id}' is not a real column in this query's results"
            return True, ""

        def _run_performance_config(workspace_id, performance_type=None, config=None):
            """
            Runs a performance-check config and returns (body, status). Either
            looks one up by performance_type (an existing, saved config) or,
            when config is given directly, runs that config as-is.

            Unlike anomaly/prediction configs, there is no algorithm step here
            — a performance check is just admin-curated, validated SQL (e.g. a
            flattened warehouse-performance stored procedure) run and handed
            back as rows for the caller to summarize. The SQL is re-validated
            with is_select_only_sql on every run (not just at save time) so an
            edit that slips in something unsafe is still caught.
            """
            if config is None:
                if not workspace_id or not performance_type:
                    logger.warning(f"Missing parameters: workspace_id={workspace_id}, performance_type={performance_type}")
                    return {"type": "error", "error": "Workspace ID and performance type are required."}, 400

                initialized, error = ensure_vanna_initialized(self, workspace_id)
                if not initialized:
                    logger.error(f"Vanna initialization failed: {error}")
                    return {"type": "error", "error": error}, 400

                workspace = get_workspace_metadata(self, workspace_id)
                if not workspace:
                    logger.error(f"Workspace not found: ID={workspace_id}")
                    return {"type": "error", "error": "Workspace not found."}, 404

                try:
                    performance_checks = json.loads(workspace.get("performance", "[]"))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse performance configs for workspace {workspace_id}: {str(e)}")
                    return {"type": "error", "error": "Invalid performance configuration format."}, 500

                perf_config = next((p for p in performance_checks if p.get('type') == performance_type), None)
                if not perf_config:
                    logger.error(f"Performance type {performance_type} not found in workspace {workspace_id}")
                    return {"type": "error", "error": f"Performance check '{performance_type}' not found."}, 404

                if not perf_config.get('enabled', True):
                    logger.warning(f"Performance type {performance_type} is disabled in workspace {workspace_id}")
                    return {"type": "error", "error": f"Performance check '{performance_type}' is disabled."}, 400
            else:
                perf_config = config

            sql_query = perf_config.get('sql_query')
            if not sql_query:
                return {"type": "error", "error": "Performance check has no sql_query configured."}, 400

            is_safe, reason = vn.is_select_only_sql(sql_query)
            if not is_safe:
                logger.error(f"Performance config '{perf_config.get('type')}' failed SQL safety check: {reason}")
                return {"type": "error", "error": f"Performance check's SQL failed validation: {reason}"}, 400

            try:
                df = vn.run_sql(sql_query)
                logger.info(f"Raw data from SQL query for performance check {perf_config.get('type')}:\n{df}")
                if df is None or df.empty:
                    return {"type": "success", "results": [], "sql": sql_query}, 200

                truncated = len(df) > _MAX_ANALYSIS_ROWS
                if truncated:
                    logger.warning(
                        f"Performance check {perf_config.get('type')}: query returned {len(df)} rows, "
                        f"truncating to {_MAX_ANALYSIS_ROWS} to avoid hanging."
                    )
                    df = df.head(_MAX_ANALYSIS_ROWS)

                df = df.replace({np.nan: None})
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].astype(str)

                return {"type": "success", "results": df.to_dict(orient="records"), "sql": sql_query}, 200
            except Exception as e:
                logger.error(f"Error running performance config '{perf_config.get('type')}': {str(e)}", exc_info=True)
                return {"type": "error", "error": f"Failed to run performance check: {str(e)}"}, 500

        def _run_anomaly_config(workspace_id, anomaly_type=None, config=None):
            """
            Runs an anomaly-detection config and returns (body, status). Either
            looks one up by anomaly_type (existing, saved config — the original
            run_anomaly behavior) or, when config is given directly, runs that
            config as-is without requiring it to be saved first — lets a
            freshly-LLM-suggested config be executed immediately from chat
            before the user has decided whether to keep it.
            """
            if config is None:
                # Validate input parameters
                if not workspace_id or not anomaly_type:
                    logger.warning(f"Missing parameters: workspace_id={workspace_id}, anomaly_type={anomaly_type}")
                    return {"type": "error", "error": "Workspace ID and anomaly type are required."}, 400

                # Ensure Vanna is initialized
                initialized, error = ensure_vanna_initialized(self, workspace_id)
                if not initialized:
                    logger.error(f"Vanna initialization failed: {error}")
                    return {"type": "error", "error": error}, 400

                # Fetch workspace metadata
                workspace = get_workspace_metadata(self, workspace_id)
                if not workspace:
                    logger.error(f"Workspace not found: ID={workspace_id}")
                    return {"type": "error", "error": "Workspace not found."}, 404

                # Get anomaly configuration
                try:
                    anomalies = json.loads(workspace.get("anomalies", "[]"))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse anomalies for workspace {workspace_id}: {str(e)}")
                    return {"type": "error", "error": "Invalid anomaly configurations format."}, 500

                anomaly = next((a for a in anomalies if a['type'] == anomaly_type), None)

                if not anomaly:
                    logger.error(f"Anomaly type {anomaly_type} not found in workspace {workspace_id}")
                    return {"type": "error", "error": f"Anomaly type {anomaly_type} not found."}, 404

                if not anomaly.get('enabled', True):
                    logger.warning(f"Anomaly type {anomaly_type} is disabled in workspace {workspace_id}")
                    return {"type": "error", "error": f"Anomaly type {anomaly_type} is disabled."}, 400
            else:
                anomaly = config

            logger.info(f"Anomaly configuration for {anomaly_type}: {anomaly}")

            try:
                # Step 1: Fetch data using the SQL query
                df = vn.run_sql(anomaly['sql_query'])
                logger.info(f"Raw data from SQL query for {anomaly_type}:\n{df}")
                if df.empty:
                    logger.warning(f"SQL query returned no results for {anomaly_type}")
                    return {"type": "success", "results": []}, 200

                truncated = len(df) > _MAX_ANALYSIS_ROWS
                if truncated:
                    logger.warning(
                        f"Anomaly {anomaly_type}: query returned {len(df)} rows, "
                        f"truncating to {_MAX_ANALYSIS_ROWS} to avoid hanging."
                    )
                    df = df.head(_MAX_ANALYSIS_ROWS)

                # Step 2: Preprocess data
                algorithm = anomaly.get('algorithm')
                parameters = anomaly.get('parameters', {})
                target = _resolve_column(parameters.get('target'), list(df.columns)) or parameters.get('target')
                features = [_resolve_column(f, list(df.columns)) or f for f in parameters.get('features', [])]

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
                        return {"type": "error", "error": f"No target column specified for z_score anomaly {anomaly_type}."}, 400
                    if target not in df.columns:
                        logger.error(f"Target column {target} not found in data for {anomaly_type}")
                        return {"type": "error", "error": f"Target column {target} not found in query results for {anomaly_type}."}, 400
                    threshold = float(parameters.get('threshold', 2.0))
                    mean = df[target].mean()
                    std = df[target].std()
                    if std == 0:
                        logger.error(f"Standard deviation is zero for {target} in {anomaly_type}")
                        return {"type": "error", "error": f"Standard deviation is zero for {target}, cannot compute z-score."}, 400
                    result_df['z_score'] = (df[target] - mean) / std
                    result_df['is_anomaly'] = result_df['z_score'].abs() > threshold
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['z_score', 'is_anomaly']]

                elif algorithm == 'isolation_forest':
                    if not features or not all(f in df.columns for f in features):
                        logger.error(f"Invalid or missing features {features} for {anomaly_type}")
                        return {"type": "error", "error": f"Invalid or missing features {features} for isolation_forest anomaly {anomaly_type}."}, 400
                    contamination = float(parameters.get('contamination', 0.1))
                    model = IsolationForest(contamination=contamination, random_state=42)
                    df = _coerce_numeric_features(df, features)
                    X = df[features].values
                    result_df['is_anomaly'] = model.fit_predict(X) == -1
                    result_df['anomaly_score'] = model.score_samples(X)
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['anomaly_score', 'is_anomaly']]

                elif algorithm == 'dbscan':
                    if not features or not all(f in df.columns for f in features):
                        logger.error(f"Invalid or missing features {features} for {anomaly_type}")
                        return {"type": "error", "error": f"Invalid or missing features {features} for dbscan anomaly {anomaly_type}."}, 400
                    eps = float(parameters.get('eps', 0.5))
                    min_samples = int(parameters.get('min_samples', 5))
                    model = DBSCAN(eps=eps, min_samples=min_samples)
                    df = _coerce_numeric_features(df, features)
                    X = df[features].values
                    labels = model.fit_predict(X)
                    result_df['is_anomaly'] = labels == -1
                    # Do not filter, keep all rows
                    result_df = result_df[df.columns.tolist() + ['is_anomaly']]

                elif algorithm == 'custom':
                    rule = parameters.get('rule')
                    if not rule:
                        logger.error(f"No rule provided for custom anomaly {anomaly_type}")
                        return {"type": "error", "error": f"No rule specified for custom anomaly {anomaly_type}."}, 400
                    try:
                        if rule.strip().upper().startswith('SELECT'):
                            # Found live: a bare .startswith('SELECT') check is trivially
                            # passed by e.g. "SELECT 1; DROP TABLE x;--" and let this run
                            # straight through vn.run_sql with none of the read-only/
                            # write-whitelist checks every other SQL path in this app
                            # goes through. is_select_only_sql is that same backstop.
                            ok, reason = vn.is_select_only_sql(rule)
                            if not ok:
                                return {"type": "error", "error": f"Invalid custom rule: {reason}"}, 400
                            result_df = vn.run_sql(rule)
                            if len(result_df) > _MAX_ANALYSIS_ROWS:
                                truncated = True
                                result_df = result_df.head(_MAX_ANALYSIS_ROWS)
                            result_df['is_anomaly'] = True
                            # Need to merge with original df to include normal data
                            original_df = df.copy()
                            original_df['is_anomaly'] = False
                            result_df = pd.concat([original_df, result_df]).drop_duplicates().reset_index(drop=True)
                        else:
                            # df.eval() is not a secure sandbox on its own — gate it with
                            # an AST allowlist first (see _is_safe_eval_rule) so a rule
                            # that passes can only be a comparison over real columns,
                            # never a function call or attribute-access escape.
                            ok, reason = _is_safe_eval_rule(rule, set(df.columns))
                            if not ok:
                                return {"type": "error", "error": f"Invalid custom rule: {reason}"}, 400
                            result_df['is_anomaly'] = df.eval(rule)
                        # Do not filter, keep all rows
                        result_df = result_df[df.columns.tolist() + ['is_anomaly']]
                    except Exception as e:
                        logger.error(f"Failed to apply custom rule '{rule}' for {anomaly_type}: {str(e)}")
                        return {"type": "error", "error": f"Failed to apply custom rule for {anomaly_type}: {str(e)}"}, 400

                # Convert DataFrame to list of dicts for JSON response
                result = result_df.to_dict(orient='records')
                logger.info(f"Returning {len(result)} rows (including {len(result_df[result_df['is_anomaly']])} anomalies) for {anomaly_type}")
                body = {"type": "success", "results": result}
                if truncated:
                    body["truncated"] = True
                    body["truncated_note"] = (
                        f"Note: this check's query returned more than {_MAX_ANALYSIS_ROWS} rows — "
                        f"results below are based on the first {_MAX_ANALYSIS_ROWS} only."
                    )
                return body, 200

            except Exception as e:
                logger.error(f"Error running anomaly {anomaly_type}: {str(e)}", exc_info=True)
                return {"type": "error", "error": f"Error running anomaly detection: {str(e)}"}, 500

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
            body, status = _run_anomaly_config(workspace_id, anomaly_type)
            return jsonify(body), status

        @self.flask_app.route('/api/v0/run_performance', methods=['GET'])
        def run_performance():
            """
            Run a performance check for a specified type in a workspace — lets
            the admin panel test a check's SQL before relying on it in chat.

            Query Parameters:
                workspace_id: The ID of the workspace.
                performance_type: The type of performance configuration to run.
            """
            workspace_id = request.args.get('workspace_id')
            performance_type = request.args.get('performance_type')
            body, status = _run_performance_config(workspace_id, performance_type)
            return jsonify(body), status

        def _run_prediction_config(workspace_id, prediction_type=None, config=None):
            """
            Runs a prediction config and returns (body, status). Either looks one
            up by prediction_type (existing, saved config — the original
            run_prediction behavior) or, when config is given directly, runs that
            config as-is without requiring it to be saved first — same rationale
            as _run_anomaly_config above.
            """
            global vn
            if config is None:
                # Validate input parameters
                if not workspace_id or not prediction_type:
                    return {"type": "error", "error": "Workspace ID and prediction type are required."}, 400

                # Ensure Vanna is initialized
                initialized, error = ensure_vanna_initialized(self, workspace_id)
                if not initialized:
                    return {"type": "error", "error": error}, 400

                # Fetch workspace metadata
                workspace = get_workspace_metadata(self, workspace_id)
                if not workspace:
                    return {"type": "error", "error": "Workspace not found."}, 404

                # Get prediction configuration
                predictions = json.loads(workspace.get("predictions", "[]"))
                prediction = next((p for p in predictions if p['type'] == prediction_type), None)
                if not prediction:
                    return {"type": "error", "error": f"Prediction type {prediction_type} not found."}, 404

                if not prediction.get('enabled', True):
                    return {"type": "error", "error": f"Prediction type {prediction_type} is disabled."}, 400
            else:
                prediction = config

            try:
                # Step 1: Fetch historical data using the SQL query
                df = vn.run_sql(prediction['sql_query'])
                logger.info(f"Raw data from SQL query:\n{df}")
                if df.empty:
                    return {"type": "error", "error": "SQL query returned no results."}, 400

                truncated = len(df) > _MAX_ANALYSIS_ROWS
                if truncated:
                    logger.warning(
                        f"Prediction {prediction_type}: query returned {len(df)} rows, "
                        f"truncating to {_MAX_ANALYSIS_ROWS} to avoid hanging."
                    )
                    df = df.head(_MAX_ANALYSIS_ROWS)

                # Step 2: Preprocess data based on prediction parameters
                algorithm = prediction.get('algorithm')
                parameters = prediction.get('parameters', {})
                target = _resolve_column(parameters.get('target'), list(df.columns)) or parameters.get('target')
                features = [_resolve_column(f, list(df.columns)) or f for f in parameters.get('features', [])]
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
                        return {"type": "error", "error": "Target column missing or invalid."}, 400
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
                        return {"type": "error", "error": "Target column missing or invalid."}, 400
                    std_value = df[target].std()
                    result_df[f'predicted_{target}_std'] = std_value  # Add std as a column

                elif algorithm == 'linear_regression':
                    if not features or not target or not all(f in df.columns for f in features) or target not in df.columns:
                        return {"type": "error", "error": "Invalid features or target column."}, 400
                    df = _coerce_numeric_features(df, features)
                    X = df[features]
                    y = df[target]
                    model = LinearRegression()
                    model.fit(X, y)
                    result_df[f'predicted_{target}'] = model.predict(X) * (1 + inflation_rate)

                elif algorithm == 'logistic_regression':
                    if not features or not target or not all(f in df.columns for f in features) or target not in df.columns:
                        return {"type": "error", "error": "Invalid features or target column."}, 400
                    df = _coerce_numeric_features(df, features)
                    X = df[features]
                    y = df[target]
                    model = LogisticRegression()
                    model.fit(X, y)
                    result_df[f'predicted_{target}_prob'] = model.predict_proba(X)[:, 1]
                    result_df[f'predicted_{target}'] = (result_df[f'predicted_{target}_prob'] > 0.5).astype(int)

                # Convert DataFrame to list of dicts for JSON response
                result = result_df.to_dict(orient='records')
                body = {"type": "success", "df": result}
                if truncated:
                    body["truncated"] = True
                    body["truncated_note"] = (
                        f"Note: this check's query returned more than {_MAX_ANALYSIS_ROWS} rows — "
                        f"results below are based on the first {_MAX_ANALYSIS_ROWS} only."
                    )
                return body, 200

            except Exception as e:
                logger.error(f"Error running prediction {prediction_type}: {str(e)}")
                return {"type": "error", "error": f"Error running prediction: {str(e)}"}, 500

        @self.flask_app.route('/api/v0/run_prediction', methods=['GET'])
        def run_prediction():
            workspace_id = request.args.get('workspace_id')
            prediction_type = request.args.get('prediction_type')
            body, status = _run_prediction_config(workspace_id, prediction_type)
            return jsonify(body), status



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
            """
            Enable/disable the Teams bot and tab for a workspace. Several
            workspaces may be Teams-enabled at once: each Teams user is routed
            to their own assigned workspace (see engine/teams/identity.py).
            Enabling verifies the workspace's LLM + DB config actually builds,
            so a broken config surfaces here instead of on the first Teams message.
            """
            try:
                data = request.json or {}
                workspace_id = data.get('workspace_id')
                teams_config = data.get('teams_config')

                if not workspace_id:
                    return jsonify({'error': 'Workspace ID is required'}), 400
                if not isinstance(teams_config, dict):
                    return jsonify({'error': 'Teams configuration is required'}), 400

                existing = self.workspace_collection.get(ids=[workspace_id])
                if not existing.get("metadatas"):
                    return jsonify({'error': f'Workspace with ID {workspace_id} not found'}), 404

                metadata = existing["metadatas"][0]
                stored = json.loads(metadata.get("teams_config") or "{}")
                stored["enabled"] = bool(teams_config.get("enabled", False))

                if stored["enabled"]:
                    instance, err = _vanna_registry.get_or_build(workspace_id, refresh=True)
                    if instance is None:
                        return jsonify({'error': f'LLM and DB configuration required for Teams integration: {err}'}), 400

                metadata["teams_config"] = json.dumps(stored)
                self.workspace_collection.update(
                    ids=[workspace_id],
                    metadatas=[metadata],
                    documents=[f"Workspace: {metadata['name']}"]
                )

                logger.info(f"Saved Teams config for workspace: ID={workspace_id} enabled={stored['enabled']}", extra={"admin": True})
                return jsonify({'message': 'Teams configuration saved successfully'}), 200

            except Exception as e:
                logger.error(f"Error saving Teams config: {str(e)}", exc_info=True)
                return jsonify({'error': 'Failed to save Teams config'}), 500

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


                        
        
        def clean_metadata(metadata_dict):
            """Ensure no None values — replace with empty string."""
            return {k: ("" if v is None else v) for k, v in metadata_dict.items()}

        _EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

        def _is_workspace_name(workspace):
            if not workspace:
                return False
            try:
                ws_get = self.workspace_collection.get()
                names = {md.get("name") for md in (ws_get.get("metadatas") or []) if isinstance(md, dict)}
                return workspace in names
            except Exception:
                return False

        @self.flask_app.route("/api/add_user", methods=["POST"])
        @self.requires_auth
        def add_user(user=None):
            """
            Add a user to the ChromaDB 'users' collection (admin/superadmin, enforced
            by the access guard). Accepts { username, password, workspace, role?, email? }.
            Only a superadmin may create admin/superadmin accounts. `email` links the
            account to a Microsoft Teams identity (the Teams bot and tab look users
            up by it) and is the only raw address a user may schedule emails to.
            """
            try:
                data = request.get_json() or {}
                username = (data.get("username") or "").strip()
                password = data.get("password") or ""
                workspace = (data.get("workspace") or "").strip()
                role = str(data.get("role") or "user").strip().lower()
                email = (data.get("email") or "").strip().lower()

                if not username or not password:
                    return jsonify({"error": "Username and password are required"}), 400
                if role not in ("user", "admin", "superadmin"):
                    return jsonify({"error": f"Invalid role '{role}'"}), 400
                if role != "user" and str(session.get("role") or "").lower() != "superadmin":
                    return jsonify({"error": "Only a superadmin can create admin accounts"}), 403
                if email and not _EMAIL_RE.match(email):
                    return jsonify({"error": f"'{email}' doesn't look like a valid email address"}), 400

                existing_user = self.users_collection.get(where={"username": username})
                if existing_user and existing_user.get("ids"):
                    return jsonify({"error": "Username already exists"}), 400
                if email and self.find_user_by_email(email)[0]:
                    return jsonify({"error": f"{email} is already linked to another user"}), 400

                password_hash = generate_password_hash(password)
                workspace_valid = _is_workspace_name(workspace)

                self.users_collection.add(
                    ids=[str(uuid.uuid4())],
                    metadatas=[{
                        "username": username,
                        "password_hash": password_hash,
                        "role": role,
                        "workspace": workspace or "",
                        "workspace_valid": bool(workspace_valid),
                        "email": email,
                    }],
                    documents=["user record"]
                )
                logger.info(f"Added user {username} (role={role}, workspace={workspace or '-'})", extra={"admin": True})

                return jsonify({
                    "message": f"User '{username}' added successfully",
                    "workspace_valid": workspace_valid
                }), 200

            except Exception as e:
                logger.error(f"add_user failed: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route("/api/update_user", methods=["POST"])
        @self.requires_auth
        def update_user(user=None):
            """
            Update an existing user's email / workspace / role (admin/superadmin).
            Expects { user_id, email?, workspace?, role? }; omitted fields are
            unchanged, an empty email clears it. Only a superadmin can change roles.
            """
            try:
                data = request.get_json() or {}
                user_id = data.get("user_id")
                if not user_id:
                    return jsonify({"error": "user_id is required"}), 400

                existing = self.users_collection.get(ids=[user_id])
                if not existing or not existing.get("ids"):
                    return jsonify({"error": f"User '{user_id}' not found"}), 404
                meta = dict(existing["metadatas"][0] or {})

                if "email" in data:
                    email = (data.get("email") or "").strip().lower()
                    if email and not _EMAIL_RE.match(email):
                        return jsonify({"error": f"'{email}' doesn't look like a valid email address"}), 400
                    other_id, _ = self.find_user_by_email(email) if email else (None, None)
                    if other_id and other_id != user_id:
                        return jsonify({"error": f"{email} is already linked to another user"}), 400
                    if email != meta.get("email", ""):
                        meta["aad_object_id"] = ""   # re-link on the next Teams sign-in
                    meta["email"] = email

                if "workspace" in data:
                    workspace = (data.get("workspace") or "").strip()
                    meta["workspace"] = workspace
                    meta["workspace_valid"] = bool(_is_workspace_name(workspace))

                if "role" in data:
                    role = str(data.get("role") or "").strip().lower()
                    if role not in ("user", "admin", "superadmin"):
                        return jsonify({"error": f"Invalid role '{role}'"}), 400
                    if role != meta.get("role") and str(session.get("role") or "").lower() != "superadmin":
                        return jsonify({"error": "Only a superadmin can change roles"}), 403
                    meta["role"] = role

                self.users_collection.update(ids=[user_id], metadatas=[meta])
                logger.info(f"Updated user {meta.get('username')} ({user_id})", extra={"admin": True})
                return jsonify({"message": "User updated", "user_id": user_id,
                                "email": meta.get("email", ""), "workspace": meta.get("workspace", ""),
                                "role": meta.get("role", "user"), "workspace_valid": bool(meta.get("workspace_valid"))}), 200
            except Exception as e:
                logger.error(f"update_user failed: {e}", exc_info=True)
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
        @self.requires_auth
        def list_users(user: any = None):
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
                        "role": metadata.get("role", "user"),
                        "workspace": metadata.get("workspace", ""),
                        "workspace_valid": bool(metadata.get("workspace_valid", False)),
                        "email": metadata.get("email", ""),
                        "teams_linked": bool(metadata.get("aad_object_id")),
                    })
                logger.info(f"Listed {len(user_list)} users")
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
                f"SERVER={self.user_mgmt_config['server']}{',' + self.user_mgmt_config['port'] if self.user_mgmt_config['port'] else ''};"
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
            try:
                validate_month(month or "")
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            data = get_monthly_billing_summary(self, month)

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

            csv_text = rows_to_csv(rows) or "Workspace\n"
            return Response(
                csv_text,
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename=billing_{month}.csv"},
            )


  
        ###################sop documentations ##############################


        @self.flask_app.route("/sop-chat")
        @self.requires_auth
        def sop_chat(user):
            role = user.get("role", "user")  # admin / user
            return render_template("sop_chat.html", role=role)

        #uploading sop files
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
                    model="gpt-4.1-mini",  # same model as the rest of the agents
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

        # ---- Channels outside the web UI: Teams bot/tab and voice ----
        # These live in their own packages and reach the chat pipeline only
        # through the published hooks below.
        self.vanna_registry = _vanna_registry
        self.vn_router = vn

        def discard_pending_write(write_id):
            with _pending_writes_lock:
                _pending_writes.pop(write_id, None)
        self.discard_pending_write = discard_pending_write

        from ..voice import register_voice_routes
        from ..teams import register_teams
        register_voice_routes(self)
        register_teams(self)


    def _workspace_id_from_ref(self, ref):
        """Workspace id for a reference that may be the id itself, its name or its
        display name (the chat UI sends the name). None if no workspace matches."""
        ref = str(ref or "").strip()
        if not ref:
            return None
        try:
            if self.workspace_collection.get(ids=[ref]).get("ids"):
                return ref
            for field in ("name", "display_name"):
                ids = self.workspace_collection.get(where={field: ref}).get("ids") or []
                if ids:
                    return ids[0]
        except Exception as e:
            logger.warning(f"_workspace_id_from_ref: lookup failed for {ref!r}: {e}")
        return None

    def _user_can_access_workspace(self, user, workspace_id):
        """Admins/superadmins may use any workspace; a plain user only the one
        assigned to them (stored as the workspace name, or legacy UUID).

        "admin" is intentionally platform-wide here, same as "superadmin" — it
        is never assigned to a workspace-scoped/client account (confirmed with
        the team: admin accounts are internal staff, not per-client managers).
        If that ever changes, this check must instead scope "admin" to its own
        assigned `user["workspace"]`, the same way a plain "user" is scoped
        below — otherwise any admin account created with a specific workspace
        (see /api/add_user) could still read every OTHER workspace's data just
        by changing workspace_id, regardless of what it was assigned."""
        role = str((user or {}).get("role") or session.get("role") or "user").lower()
        if role in ADMIN_ROLES:
            return True
        assigned = (user or {}).get("workspace") or ""
        if not assigned or not workspace_id:
            return False
        if assigned == str(workspace_id):
            return True
        meta = get_workspace_metadata(self, workspace_id)
        return bool(meta) and assigned in (meta.get("name"), meta.get("display_name"))

    def find_user_by_email(self, email):
        """(user_id, metadata) for the user whose email matches (case-insensitive), else (None, None)."""
        email = (email or "").strip().lower()
        if not email:
            return None, None
        found = self.users_collection.get(where={"email": email}, limit=1)
        if found and found.get("ids"):
            return found["ids"][0], found["metadatas"][0]
        return None, None

    def find_user_by_aad_id(self, aad_object_id):
        """(user_id, metadata) for the user already linked to this Entra object id, else (None, None)."""
        if not aad_object_id:
            return None, None
        found = self.users_collection.get(where={"aad_object_id": aad_object_id}, limit=1)
        if found and found.get("ids"):
            return found["ids"][0], found["metadatas"][0]
        return None, None

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
                fig_json = None
                df = None
                if fig_json:
                    if isinstance(fig_json, (dict, list)):
                        plot_data = json.dumps(fig_json, ensure_ascii=False)
                    else:
                        plot_data = None
                else:
                    plot_data = json.dumps({"data": "No chart generated"}, ensure_ascii=False)
            except Exception as e:
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
 
 
 
 
 
    def normalize_model_name(self, model_name: str) -> str:
        if not model_name:
            return "unknown"

        name = model_name.strip().lower()

        # Strip dated/version suffixes ("gpt-4.1-mini-2025-04-14" -> "gpt-4.1-mini")
        # by matching the LONGEST known prefix. Fixed-order startswith checks
        # matched "gpt-4.1" first, so gpt-4.1-mini was billed at full gpt-4.1
        # prices (~5x too high) — and every agent here runs on mini.
        for known in sorted(MODEL_PRICING, key=len, reverse=True):
            if name == known or name.startswith(known + "-"):
                return known

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
        plot_data: str = None,
        workspace_id: str = None,  # explicit override — required for callers with
                                    # no active Flask request/session (e.g. a
                                    # scheduled agent firing on a background thread)
        parent_question_id: str = None,  # follow-up's parent, for the FAQ/history
                                    # sidebar's grouping — persisted here so it
                                    # survives a fresh session reload (see
                                    # fetch_user_documents_for_user), not just the
                                    # in-memory cache
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
        parent_question_id = (parent_question_id or None)

        token_count         = int(token_count or 0)
        input_tokens        = int(input_tokens or 0)
        output_tokens       = int(output_tokens or 0)
        cached_input_tokens = int(cached_input_tokens or 0)
        cost_usd            = float(cost_usd) if cost_usd is not None else None

        if workspace_id is None and has_request_context():  # Teams turns have no session
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
                    f"SERVER={self.user_mgmt_config['server']}{',' + self.user_mgmt_config['port'] if self.user_mgmt_config['port'] else ''};"
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
                            model_name          = ?,
                            parent_question_id  = ?
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
                        parent_question_id,
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
                            cached_input_tokens, cost_usd, model_name, parent_question_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        model_name,
                        parent_question_id
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

        cost_usd = compute_cost_usd(normalized_model, input_tokens, output_tokens, cached_input_tokens)

        conn = None
        cursor = None

        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.user_mgmt_config['server']}{',' + self.user_mgmt_config['port'] if self.user_mgmt_config['port'] else ''};"
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


def _is_trained_question(question, workspace_name):
    """True when `question` is one of this workspace's trained questions — its
    stored SQL answers it directly, so it must not be re-routed, merged into a
    pending clarification, or second-guessed by an LLM classifier."""
    finder = getattr(vn, "find_trained_sql", None)
    if not finder or not question or not workspace_name:
        return False
    try:
        return bool(finder(question, workspace_name))
    except Exception as e:
        logger.warning(f"Trained-question lookup failed: {e}")
        return False


# Messages closer than this to a trained question are answered from the dataset
# instead of being routed by the LLM classifier. Calibrated on the demo workspace
# (Chroma default embedding): rephrasings of its trained questions sat at
# 0.00–0.61 (96% under 0.5); genuine forecast/anomaly requests at 0.35–1.57
# (1 of 20 under 0.5).
_NEAR_TRAINED_DISTANCE = 0.5

_QUESTION_OPENERS = re.compile(
    r"^\s*(what|which|who|whose|when|where|why|how|show|list|give|get|fetch|find|display|"
    r"count|tell me|is|are|was|were|do|does|did|can|could|will|would|has|have)\b",
    re.IGNORECASE,
)


def _is_new_question(text):
    """True when a reply to an open scheduling prompt ("What would you like me
    to send you?", "Who should receive this?") is really a fresh question — e.g.
    "how many warehouses do we have" — that should be answered, not scheduled.
    A reply that mentions sending/mailing/scheduling still continues the prompt."""
    text = (text or "").strip()
    if not text or text.startswith("/") or DELIVERY_CUES.search(text):
        return False
    if len(text.split()) < 3:
        return False
    return text.endswith("?") or bool(_QUESTION_OPENERS.match(text))


def _dataset_route(question, workspace_name):
    """How a chat message relates to this workspace's trained dataset:
    "exact"  — it IS a trained question (its stored SQL answers it);
    "near"   — a close rephrasing of one, and it doesn't ask for anything to be
               sent/scheduled, so the query pipeline (which retrieves that
               trained example) answers it — not prediction or scheduling;
    None     — neither; route it as usual.
    Before this, "Show me orders at risk…" style questions — a quarter of the
    demo dataset — were sent to the prediction pipeline by the classifier and
    answered by an unrelated saved check."""
    if not question or not workspace_name:
        return None
    if _is_trained_question(question, workspace_name):
        return "exact"
    if DELIVERY_CUES.search(question):
        return None
    finder = getattr(vn, "nearest_trained_distance", None)
    distance = finder(question, workspace_name) if finder else None
    if distance is not None and distance < _NEAR_TRAINED_DISTANCE:
        return "near"
    return None


def _canonical_question_id(value):
    """The hyphenated lowercase UUID form of a question id, or None if it isn't one.

    dbo.users.question_id is UNIQUEIDENTIFIER, so a non-UUID that reached the
    feedback tables would fail with SQL Server error 8169 wherever the two are
    compared. Every id the server issues is str(uuid4()), so this only rejects
    malformed client input — and normalises the 32-hex-digit form to match.
    """
    try:
        return str(uuid.UUID(str(value).strip()))
    except (ValueError, AttributeError, TypeError):
        return None


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














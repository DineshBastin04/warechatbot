# import logging
 
# # Logging
# logging.basicConfig(
#     level=logging.INFO,
#     # format="%(asctime)s - %(levelname)s - %(message)s",
#     # format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
#     format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler("vanna.log"),
#     ],
# )

import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import os
import calendar

from dotenv import load_dotenv
load_dotenv()  # loads D:\WAI\.env into the process environment (e.g. OPENAI_API_KEY)

class MonthlyWeeklyRotatingFileHandler(TimedRotatingFileHandler):
    """
    Custom handler that automatically creates month subfolders
    and names log files week_#.log under that folder.
    """
    def __init__(self, base_dir, prefix, *args, **kwargs):
        self.base_dir = base_dir
        self.prefix = prefix
        os.makedirs(base_dir, exist_ok=True)
        self.update_filename()
        super().__init__(self.current_file, when="W0", interval=1, backupCount=12, *args, **kwargs)

    def update_filename(self):
        now = datetime.now()
        month_name = calendar.month_name[now.month]
        week_number = (now.day - 1) // 7 + 1  # crude week number (1–4/5)
        month_folder = os.path.join(self.base_dir, month_name)
        os.makedirs(month_folder, exist_ok=True)
        filename = f"week_{week_number}_{self.prefix}.log"
        self.current_file = os.path.join(month_folder, filename)

    def doRollover(self):
        # update filename before rolling over
        self.update_filename()
        # Close the old stream and start a new one
        if self.stream:
            self.stream.close()
        self.baseFilename = self.current_file
        os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
        self.stream = self._open()

import logging
from logging import Filter
from datetime import time

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# ---------- Console Handler ----------
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# ---------- Filters ----------
class ExtraFlagFilter(Filter):
    def __init__(self, flag_name):
        super().__init__()
        self.flag_name = flag_name
    def filter(self, record):
        return bool(record.__dict__.get(self.flag_name, False))

# ---------- Admin Log Handler ----------
admin_handler = MonthlyWeeklyRotatingFileHandler(
    base_dir="Logs",
    prefix="developer",
    encoding="utf-8"
)
admin_handler.setLevel(logging.INFO)
admin_handler.setFormatter(logging.Formatter(LOG_FORMAT))
admin_handler.addFilter(ExtraFlagFilter("admin"))
admin_handler.atTime = time(0, 0)  # rollover at midnight

# ---------- User Log Handler ----------
user_handler = MonthlyWeeklyRotatingFileHandler(
    base_dir="Logs",
    prefix="admin",
    encoding="utf-8"
)
user_handler.setLevel(logging.INFO)
user_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
user_handler.addFilter(ExtraFlagFilter("user"))
user_handler.atTime = time(0, 0)

# ---------- Root Logger ----------
root = logging.getLogger()
root.setLevel(logging.DEBUG)
root.addHandler(console_handler)
root.addHandler(admin_handler)
root.addHandler(user_handler)

logger = logging.getLogger(__name__)
# logger.info("Logging initialized", extra={"admin": True})

# import logging
# from logging import Filter

# console_fmt = logging.Formatter(
#     "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
# )
# # file_fmt = logging.Formatter(
# #     "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
# # )
# admin_fmt = logging.Formatter(
#     "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
# )

# user_fmt = logging.Formatter(
#     "%(asctime)s - %(levelname)s - %(message)s"
# )

cache_fmt = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
# # ---------- Shared format ----------
# # LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# # ---------- Console handler (shows everything) ----------
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(console_fmt)

# # ---------- Custom Filters ----------
# class ExtraFlagFilter(Filter):
#     """Filter that only allows records having extra[flag_name] == True"""
#     def __init__(self, flag_name):
#         super().__init__()
#         self.flag_name = flag_name

#     def filter(self, record):
#         return bool(record.__dict__.get(self.flag_name, False))

# # ---------- Admin file handler ----------
# admin_handler = logging.FileHandler("admin.log", mode="a", encoding="utf-8")
# admin_handler.setLevel(logging.INFO)
# admin_handler.setFormatter(admin_fmt)
# admin_handler.addFilter(ExtraFlagFilter("admin"))  # Only logs with extra={"admin": True}

# # ---------- User file handler ----------
# user_handler = logging.FileHandler("user.log", mode="a", encoding="utf-8")
# user_handler.setLevel(logging.INFO)
# user_handler.setFormatter(user_fmt)
# user_handler.addFilter(ExtraFlagFilter("user"))    # Only logs with extra={"user": True}


# cache_handler = logging.FileHandler("cache.log", mode="a", encoding="utf-8")
# cache_handler.setLevel(logging.INFO)
# cache_handler.setFormatter(cache_fmt)
# cache_handler.addFilter(ExtraFlagFilter("cache"))

# require_cache_handler = logging.FileHandler("require_cache.log", "a", encoding="utf-8")
# require_cache_handler.setLevel(logging.INFO)
# require_cache_handler.setFormatter(cache_fmt)
# require_cache_handler.addFilter(ExtraFlagFilter("required"))

# session_handler = logging.FileHandler("session.log", "a", encoding="utf-8")
# session_handler.setLevel(logging.INFO)
# session_handler.setFormatter(cache_fmt)
# session_handler.addFilter(ExtraFlagFilter("session"))

# flow_handler = logging.FileHandler("flow.log", "a", encoding="utf-8")
# flow_handler.setLevel(logging.INFO)
# flow_handler.setFormatter(cache_fmt)
# flow_handler.addFilter(ExtraFlagFilter("flow"))

followup = logging.FileHandler("followup.log", "a", encoding="utf-8")
followup.setLevel(logging.INFO)
followup.setFormatter(cache_fmt)
followup.addFilter(ExtraFlagFilter("followup"))

document = logging.FileHandler("document.log", "a", encoding="utf-8")
document.setLevel(logging.INFO)
document.setFormatter(cache_fmt)
document.addFilter(ExtraFlagFilter("document"))
# # ---------- Root logger configuration ----------
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)
# root_logger.addHandler(console_handler)
# root_logger.addHandler(admin_handler)
# root_logger.addHandler(user_handler)
# root_logger.addHandler(cache_handler)
# root_logger.addHandler(require_cache_handler)
# root_logger.addHandler(session_handler)
# root_logger.addHandler(flow_handler)
root.addHandler(followup)
root.addHandler(document)
# # ---------- Confirm setup ----------
logger = logging.getLogger(__name__)
logger.info("Logging system initialized")

logger.info("Initialized WI with OpenAI (GPT-4) as a placeholder.")
logger.info("Starting the Flask app with Waitress...")
 
# Create Vanna app
from waitress import serve
from vanna.flask.__init__ import VannaFlaskApp
vanna_app = VannaFlaskApp()
app = vanna_app.flask_app
#  Pass the internal Flask instance to Waitress
serve(app, host="127.0.0.1", port=8084, threads=8)
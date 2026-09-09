import calendar
import logging
import os
from datetime import datetime, time
from logging import Filter
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv

load_dotenv()


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
        week_number = (now.day - 1) // 7 + 1  # crude week number (1-4/5)
        month_folder = os.path.join(self.base_dir, month_name)
        os.makedirs(month_folder, exist_ok=True)
        filename = f"week_{week_number}_{self.prefix}.log"
        self.current_file = os.path.join(month_folder, filename)

    def doRollover(self):
        self.update_filename()
        if self.stream:
            self.stream.close()
        self.baseFilename = self.current_file
        os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
        self.stream = self._open()


class ExtraFlagFilter(Filter):
    def __init__(self, flag_name):
        super().__init__()
        self.flag_name = flag_name

    def filter(self, record):
        return bool(record.__dict__.get(self.flag_name, False))


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
cache_fmt = logging.Formatter(LOG_FORMAT)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

admin_handler = MonthlyWeeklyRotatingFileHandler(base_dir="Logs", prefix="developer", encoding="utf-8")
admin_handler.setLevel(logging.INFO)
admin_handler.setFormatter(logging.Formatter(LOG_FORMAT))
admin_handler.addFilter(ExtraFlagFilter("admin"))
admin_handler.atTime = time(0, 0)  # rollover at midnight

user_handler = MonthlyWeeklyRotatingFileHandler(base_dir="Logs", prefix="admin", encoding="utf-8")
user_handler.setLevel(logging.INFO)
user_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
user_handler.addFilter(ExtraFlagFilter("user"))
user_handler.atTime = time(0, 0)

followup = logging.FileHandler("followup.log", "a", encoding="utf-8")
followup.setLevel(logging.INFO)
followup.setFormatter(cache_fmt)
followup.addFilter(ExtraFlagFilter("followup"))

document = logging.FileHandler("document.log", "a", encoding="utf-8")
document.setLevel(logging.INFO)
document.setFormatter(cache_fmt)
document.addFilter(ExtraFlagFilter("document"))

root = logging.getLogger()
root.setLevel(logging.DEBUG)
root.addHandler(console_handler)
root.addHandler(admin_handler)
root.addHandler(user_handler)
root.addHandler(followup)
root.addHandler(document)

logger = logging.getLogger(__name__)
logger.info("Logging system initialized")
logger.info("Initialized WI with OpenAI (GPT-4) as a placeholder.")
logger.info("Starting the Flask app with Waitress...")

from waitress import serve
from engine.flask.__init__ import VannaFlaskApp

vanna_app = VannaFlaskApp()
app = vanna_app.flask_app
serve(app, host="127.0.0.1", port=8084, threads=8)

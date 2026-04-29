"""
Logger module — all output goes to logs/game_assistant.log.
Also captures stderr/stdout so native library errors (ONNX, ctranslate2, etc.)
are not silently lost in a GUI app.
"""

import os
import sys
import logging
from datetime import datetime


# --- Log directory next to the exe/script ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "game_assistant.log")


# --- Rotate: keep log file under 5MB ---
# If the log file is too big, rename it and start fresh
try:
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 5 * 1024 * 1024:
        backup = LOG_FILE + ".old"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(LOG_FILE, backup)
except:
    pass


# --- Set up Python logging ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

logger = logging.getLogger("GameAssistant")


# --- Redirect stdout/stderr to log file ---
# This catches print() calls from third-party libraries (ONNX, ctranslate2, etc.)
# and native error messages that would otherwise be lost in a GUI app.

class _StreamToLogger:
    """Redirects a stream (stdout/stderr) to the log file."""

    def __init__(self, log_level):
        self.log_level = log_level
        self._buffer = ""

    def write(self, text):
        if text and text.strip():
            for line in text.strip().splitlines():
                logger.log(self.log_level, f"[stdio] {line}")

    def flush(self):
        pass

    def isatty(self):
        return False


# Only redirect if we're running as a GUI (no console attached)
# This prevents breaking interactive debugging
if not sys.stdout or not hasattr(sys.stdout, "fileno"):
    sys.stdout = _StreamToLogger(logging.INFO)
    sys.stderr = _StreamToLogger(logging.ERROR)
else:
    try:
        sys.stdout.fileno()
    except:
        # No console — redirect
        sys.stdout = _StreamToLogger(logging.INFO)
        sys.stderr = _StreamToLogger(logging.ERROR)


# --- Write startup marker ---
logger.info("=" * 50)
logger.info(f"Game Assistant starting — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Python {sys.version}")
logger.info(f"Log file: {LOG_FILE}")
logger.info("=" * 50)

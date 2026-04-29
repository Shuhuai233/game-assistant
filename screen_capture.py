"""
Screen capture module.
Takes a screenshot and encodes it as base64 for vision models.
"""

import base64
import io
from config_loader import Config
from logger import logger


class ScreenCapture:
    """Captures screen and returns base64-encoded PNG."""

    def __init__(self, config: Config):
        self.enabled = config.screen_capture_enabled
        self.monitor_index = config.screen_capture_monitor

    def capture(self) -> str:
        if not self.enabled:
            return None

        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitors = sct.monitors
                if self.monitor_index < len(monitors):
                    monitor = monitors[self.monitor_index]
                else:
                    monitor = monitors[0]

                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                max_size = 1280
                ratio = min(max_size / img.width, max_size / img.height)
                if ratio < 1:
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)

                buffer = io.BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode("utf-8")

        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None

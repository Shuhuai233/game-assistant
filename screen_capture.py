"""
Screen capture module.
Takes a screenshot and encodes it as base64 for vision models.
"""

import base64
import io
from config_loader import Config


class ScreenCapture:
    """Captures screen and returns base64-encoded PNG."""

    def __init__(self, config: Config):
        self.enabled = config.screen_capture_enabled
        self.monitor_index = config.screen_capture_monitor
        print(f"[Screen] Capture {'enabled' if self.enabled else 'disabled'}")

    def capture(self) -> str:
        """
        Capture the screen and return base64-encoded PNG string.
        Returns None if screen capture is disabled.
        """
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

                # Convert to PIL Image and resize to save tokens
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Resize to max 1280px on longest side to save API costs
                max_size = 1280
                ratio = min(max_size / img.width, max_size / img.height)
                if ratio < 1:
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)

                # Encode to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode("utf-8")

        except Exception as e:
            print(f"[Screen] Capture failed: {e}")
            return None

"""
System tray application - main entry point for GUI mode.
Runs the assistant loop in a background thread, shows overlay on top of game.
"""

import sys
import os
import threading
import time

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import Qt

from overlay import OverlayWindow
from settings_dialog import SettingsDialog
from config_loader import load_config


def create_default_icon():
    """Create a simple colored icon (no external file needed)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Circle background
    painter.setBrush(QColor(40, 120, 220))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    # "G" letter
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


class AssistantWorker:
    """Runs the push-to-talk loop in a background thread."""

    def __init__(self, overlay: OverlayWindow):
        self.overlay = overlay
        self.running = False
        self.thread = None
        self.config = None
        self.llm = None
        self.stt = None
        self.tts = None
        self.screen = None

    def start(self):
        """Load config and start the background loop."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background loop."""
        self.running = False

    def reload(self):
        """Reload config (after settings change)."""
        self.stop()
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.start()

    def _run(self):
        """Main assistant loop (runs in background thread)."""
        import keyboard
        from llm_client import LLMClient
        from stt_engine import create_stt_engine
        from tts_engine import create_tts_engine
        from screen_capture import ScreenCapture
        from audio_recorder import record_while_pressed

        try:
            self.config = load_config()

            self.overlay.set_status("Loading AI model...")
            self.llm = LLMClient(self.config)

            self.overlay.set_status("Loading speech recognition...")
            self.stt = create_stt_engine(self.config)

            self.tts = create_tts_engine(self.config)
            self.screen = ScreenCapture(self.config)

            ptt_key = self.config.hotkey_push_to_talk
            self.overlay.set_status(f"Ready! Hold [{ptt_key.upper()}] to talk")
            time.sleep(2)
            self.overlay.clear()

        except Exception as e:
            self.overlay.set_status(f"Error: {e}")
            print(f"[Error] Init failed: {e}")
            self.running = False
            return

        # Main loop
        while self.running:
            try:
                # Wait for push-to-talk key
                keyboard.wait(ptt_key)
                if not self.running:
                    break

                time.sleep(0.05)
                if not keyboard.is_pressed(ptt_key):
                    continue

                # Recording
                self.overlay.set_status("Listening...")
                audio_bytes = record_while_pressed(ptt_key)
                if audio_bytes is None:
                    self.overlay.clear()
                    continue

                # Transcribe
                self.overlay.set_status("Transcribing...")
                question = self.stt.transcribe(audio_bytes)
                if not question:
                    self.overlay.set_status("No speech detected")
                    time.sleep(1)
                    self.overlay.clear()
                    continue

                self.overlay.set_question(question)

                # Screenshot
                screenshot_b64 = None
                if self.config.screen_capture_enabled:
                    self.overlay.set_status("Capturing screen...")
                    screenshot_b64 = self.screen.capture()

                # Ask AI
                self.overlay.set_status("Thinking...")
                answer = self.llm.ask(question, screenshot_b64)

                # Show response
                self.overlay.set_status("")
                self.overlay.set_response(answer)

                # Speak
                self.overlay.set_status("Speaking...")
                self.tts.speak(answer)
                self.overlay.set_status("")

            except Exception as e:
                print(f"[Error] Loop: {e}")
                self.overlay.set_status(f"Error: {e}")
                time.sleep(2)
                self.overlay.clear()


class TrayApp:
    """System tray application."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Overlay
        self.overlay = OverlayWindow()

        # Worker
        self.worker = AssistantWorker(self.overlay)

        # System tray
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_default_icon())
        self.tray.setToolTip("Game Assistant")

        # Tray menu
        menu = QMenu()

        status_action = menu.addAction("Game Assistant")
        status_action.setEnabled(False)
        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        toggle_overlay = menu.addAction("Toggle Overlay")
        toggle_overlay.triggered.connect(self._toggle_overlay)

        restart_action = menu.addAction("Restart Assistant")
        restart_action.triggered.connect(self._restart)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)

    def run(self):
        """Start the application."""
        self.tray.show()
        self.tray.showMessage(
            "Game Assistant",
            "Running in system tray. Right-click for options.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

        # Start assistant worker
        self.worker.start()

        return self.app.exec()

    def _open_settings(self):
        dialog = SettingsDialog()
        if dialog.exec():
            # Settings were saved, reload
            self.tray.showMessage(
                "Game Assistant",
                "Settings saved. Restarting assistant...",
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )
            self.worker.reload()

    def _toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.reposition()

    def _restart(self):
        self.worker.reload()
        self.tray.showMessage(
            "Game Assistant",
            "Assistant restarted.",
            QSystemTrayIcon.MessageIcon.Information,
            1500
        )

    def _quit(self):
        self.worker.stop()
        self.tray.hide()
        self.app.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._open_settings()


def main():
    app = TrayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()

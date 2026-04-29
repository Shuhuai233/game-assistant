"""
System tray application — the ONLY entry point.
Pure GUI, no terminal, no console.
Auto-opens Settings on first run if no API key is configured.
"""

import sys
import os
import threading
import time

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer

from overlay import OverlayWindow
from settings_dialog import SettingsDialog
from config_loader import load_config, is_first_run, ensure_config_exists, CONFIG_PATH
from logger import logger


def create_default_icon():
    """Create a simple colored icon (no external file needed)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(40, 120, 220))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
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

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def reload(self):
        self.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.start()

    def _run(self):
        import keyboard
        from llm_client import LLMClient
        from stt_engine import create_stt_engine
        from tts_engine import create_tts_engine
        from screen_capture import ScreenCapture
        from audio_recorder import record_while_pressed

        try:
            config = load_config()

            self.overlay.set_status("Loading AI...")
            llm = LLMClient(config)

            self.overlay.set_status("Loading speech recognition...")
            stt = create_stt_engine(config)

            tts = create_tts_engine(config)
            screen = ScreenCapture(config)

            ptt_key = config.hotkey_push_to_talk
            mic_device = config.audio_input_device
            self.overlay.set_status(f"Ready! Hold [{ptt_key.upper()}] to talk")
            time.sleep(2)
            self.overlay.clear()

        except Exception as e:
            logger.error(f"Init failed: {e}")
            self.overlay.set_status(f"Error: {e}")
            self.running = False
            return

        while self.running:
            try:
                keyboard.wait(ptt_key)
                if not self.running:
                    break

                time.sleep(0.05)
                if not keyboard.is_pressed(ptt_key):
                    continue

                # Recording
                self.overlay.set_status("Listening...")
                audio_bytes = record_while_pressed(ptt_key, device_index=mic_device)
                if audio_bytes is None:
                    self.overlay.clear()
                    continue

                # Transcribe
                self.overlay.set_status("Transcribing...")
                question = stt.transcribe(audio_bytes)
                if not question:
                    self.overlay.set_status("No speech detected")
                    time.sleep(1)
                    self.overlay.clear()
                    continue

                self.overlay.set_question(question)

                # Screenshot
                screenshot_b64 = None
                if config.screen_capture_enabled:
                    self.overlay.set_status("Capturing screen...")
                    screenshot_b64 = screen.capture()

                # Ask AI
                self.overlay.set_status("Thinking...")
                answer = llm.ask(question, screenshot_b64)

                # Show response
                self.overlay.set_status("")
                self.overlay.set_response(answer)

                # Speak
                self.overlay.set_status("Speaking...")
                tts.speak(answer)
                self.overlay.set_status("")

            except Exception as e:
                logger.error(f"Loop error: {e}")
                self.overlay.set_status(f"Error: {e}")
                time.sleep(2)
                self.overlay.clear()


class TrayApp:
    """System tray application."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Game Assistant")

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

        title = menu.addAction("Game Assistant")
        title.setEnabled(False)
        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        toggle_action = menu.addAction("Toggle Overlay")
        toggle_action.triggered.connect(self._toggle_overlay)

        restart_action = menu.addAction("Restart")
        restart_action.triggered.connect(self._restart)

        logs_action = menu.addAction("View Logs")
        logs_action.triggered.connect(self._open_logs)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)

    def run(self):
        """Start the application."""
        # Ensure config exists
        ensure_config_exists()

        self.tray.show()

        # First run? Open settings immediately
        if is_first_run():
            logger.info("First run detected, opening settings")
            # Use a timer to open settings after event loop starts
            QTimer.singleShot(500, self._first_run_settings)
        else:
            # Normal start
            self.tray.showMessage(
                "Game Assistant",
                "Running in system tray. Right-click for options.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            self.worker.start()

        return self.app.exec()

    def _first_run_settings(self):
        """Show welcome message and open settings on first run."""
        msg = QMessageBox()
        msg.setWindowTitle("Game Assistant")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Welcome to Game Assistant!")
        msg.setInformativeText(
            "Please configure your AI provider and push-to-talk key to get started."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

        self._open_settings()

    def _open_settings(self):
        dialog = SettingsDialog()
        if dialog.exec():
            self.tray.showMessage(
                "Game Assistant",
                "Settings saved. Starting assistant...",
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

    def _open_logs(self):
        """Open the log file in the default text editor."""
        import subprocess
        from logger import LOG_FILE
        try:
            os.startfile(LOG_FILE)
        except AttributeError:
            # Not Windows
            subprocess.Popen(["xdg-open", LOG_FILE])
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")

    def _quit(self):
        self.worker.stop()
        self.tray.hide()
        self.app.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._open_settings()


def main():
    logger.info("Game Assistant starting")
    app = TrayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()

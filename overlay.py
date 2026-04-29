"""
Overlay window - transparent floating text on top of the game.
Shows AI responses, status indicators (listening/thinking/speaking).
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont


class OverlayWindow(QWidget):
    """Transparent overlay that sits on top of the game."""

    # Signals for thread-safe UI updates
    update_status_signal = pyqtSignal(str)
    update_response_signal = pyqtSignal(str)
    update_question_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._init_window()
        self._init_ui()
        self._connect_signals()
        self._auto_hide_timer = QTimer()
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._fade_out)

    def _init_window(self):
        """Set up transparent, always-on-top, click-through window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # hide from taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Allow clicks to pass through to the game
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Position: bottom-center of screen
        self.setFixedWidth(600)
        self.setMinimumHeight(50)

    def _init_ui(self):
        """Create the overlay labels."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Status label (Listening... / Thinking... / Speaking...)
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #00ccff; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._add_shadow(self.status_label)
        layout.addWidget(self.status_label)

        # Question label (what the user said)
        self.question_label = QLabel("")
        self.question_label.setFont(QFont("Segoe UI", 10))
        self.question_label.setStyleSheet("color: #aaaaaa; background: transparent;")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setWordWrap(True)
        self._add_shadow(self.question_label)
        layout.addWidget(self.question_label)

        # Response label (AI answer)
        self.response_label = QLabel("")
        self.response_label.setFont(QFont("Segoe UI", 13))
        self.response_label.setStyleSheet(
            "color: #ffffff; background: rgba(0, 0, 0, 180); "
            "border-radius: 10px; padding: 12px;"
        )
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.response_label.setWordWrap(True)
        self.response_label.setMaximumWidth(560)
        self._add_shadow(self.response_label)
        layout.addWidget(self.response_label)

        self.response_label.hide()
        self.question_label.hide()

    def _add_shadow(self, widget):
        """Add drop shadow to make text readable on any background."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(1, 1)
        widget.setGraphicsEffect(shadow)

    def _connect_signals(self):
        """Connect signals for thread-safe updates."""
        self.update_status_signal.connect(self._on_update_status)
        self.update_response_signal.connect(self._on_update_response)
        self.update_question_signal.connect(self._on_update_question)

    def reposition(self):
        """Move overlay to bottom-center of primary screen."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() - self.height() - 80
            self.move(x, y)

    # --- Thread-safe public methods (call from any thread) ---

    def set_status(self, text: str):
        """Update status text (thread-safe)."""
        self.update_status_signal.emit(text)

    def set_response(self, text: str):
        """Update AI response text (thread-safe)."""
        self.update_response_signal.emit(text)

    def set_question(self, text: str):
        """Update user question text (thread-safe)."""
        self.update_question_signal.emit(text)

    def clear(self):
        """Clear all text."""
        self.update_status_signal.emit("")
        self.update_response_signal.emit("")
        self.update_question_signal.emit("")

    # --- Slots (run on UI thread) ---

    @pyqtSlot(str)
    def _on_update_status(self, text: str):
        self.status_label.setText(text)
        if text:
            # Color based on state
            color_map = {
                "Listening": "#ff4444",     # red
                "Transcribing": "#ffaa00",  # orange
                "Thinking": "#00ccff",      # blue
                "Speaking": "#44ff44",      # green
            }
            for key, color in color_map.items():
                if key.lower() in text.lower():
                    self.status_label.setStyleSheet(f"color: {color}; background: transparent;")
                    break

            self.show()
            self.reposition()
            self._auto_hide_timer.stop()
        else:
            self.status_label.setStyleSheet("color: #00ccff; background: transparent;")

    @pyqtSlot(str)
    def _on_update_question(self, text: str):
        if text:
            self.question_label.setText(f"You: {text}")
            self.question_label.show()
        else:
            self.question_label.hide()
        self.adjustSize()
        self.reposition()

    @pyqtSlot(str)
    def _on_update_response(self, text: str):
        if text:
            self.response_label.setText(text)
            self.response_label.show()
            self.show()
            self.adjustSize()
            self.reposition()
            # Auto-hide after some time based on text length
            hide_delay = max(5000, len(text) * 80)  # at least 5s
            self._auto_hide_timer.start(hide_delay)
        else:
            self.response_label.hide()

    def _fade_out(self):
        """Hide the overlay after timeout."""
        self.status_label.setText("")
        self.question_label.hide()
        self.response_label.hide()
        self.hide()

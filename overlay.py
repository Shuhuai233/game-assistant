"""
Overlay window - transparent floating indicator on top of the game.
Shows a small status dot + AI responses. Designed to be unobtrusive.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont


class OverlayWindow(QWidget):
    """Transparent overlay that sits on top of the game."""

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedWidth(500)
        self.setMinimumHeight(30)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(4)

        # Status row: small dot + short text, very compact
        status_row = QHBoxLayout()
        status_row.setSpacing(6)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setStyleSheet(
            "background: transparent; border-radius: 5px;"
        )
        status_row.addWidget(self.status_dot)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: rgba(255,255,255,160); background: transparent;")
        self._add_shadow(self.status_label)
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        layout.addLayout(status_row)

        # Question label (what the user said) — small grey text
        self.question_label = QLabel("")
        self.question_label.setFont(QFont("Segoe UI", 9))
        self.question_label.setStyleSheet("color: rgba(200,200,200,140); background: transparent;")
        self.question_label.setWordWrap(True)
        self._add_shadow(self.question_label)
        layout.addWidget(self.question_label)
        self.question_label.hide()

        # Response label (AI answer) — main content
        self.response_label = QLabel("")
        self.response_label.setFont(QFont("Segoe UI", 12))
        self.response_label.setStyleSheet(
            "color: #ffffff; background: rgba(0, 0, 0, 160); "
            "border-radius: 8px; padding: 10px;"
        )
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.response_label.setWordWrap(True)
        self.response_label.setMaximumWidth(470)
        self._add_shadow(self.response_label)
        layout.addWidget(self.response_label)
        self.response_label.hide()

    def _add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(1, 1)
        widget.setGraphicsEffect(shadow)

    def _connect_signals(self):
        self.update_status_signal.connect(self._on_update_status)
        self.update_response_signal.connect(self._on_update_response)
        self.update_question_signal.connect(self._on_update_question)

    def reposition(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() - self.height() - 60
            self.move(x, y)

    # --- Thread-safe public methods ---

    def set_status(self, text: str):
        self.update_status_signal.emit(text)

    def set_response(self, text: str):
        self.update_response_signal.emit(text)

    def set_question(self, text: str):
        self.update_question_signal.emit(text)

    def clear(self):
        self.update_status_signal.emit("")
        self.update_response_signal.emit("")
        self.update_question_signal.emit("")

    # --- Slots ---

    @pyqtSlot(str)
    def _on_update_status(self, text: str):
        if text:
            self.status_label.setText(text)

            # Small colored dot based on state
            dot_color = "rgba(255,255,255,100)"  # default dim white
            text_lower = text.lower()
            if "listen" in text_lower:
                dot_color = "#ff4444"      # red dot while recording
            elif "transcrib" in text_lower:
                dot_color = "#ffaa00"      # orange
            elif "think" in text_lower:
                dot_color = "#4488ff"      # blue
            elif "speak" in text_lower:
                dot_color = "#44cc44"      # green
            elif "ready" in text_lower:
                dot_color = "#44cc44"      # green
            elif "error" in text_lower:
                dot_color = "#ff4444"      # red

            self.status_dot.setStyleSheet(
                f"background: {dot_color}; border-radius: 5px;"
            )

            self.show()
            self.reposition()
            self._auto_hide_timer.stop()
        else:
            self.status_label.setText("")
            self.status_dot.setStyleSheet("background: transparent; border-radius: 5px;")

    @pyqtSlot(str)
    def _on_update_question(self, text: str):
        if text:
            self.question_label.setText(f"> {text}")
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
            hide_delay = max(6000, len(text) * 80)
            self._auto_hide_timer.start(hide_delay)
        else:
            self.response_label.hide()

    def _fade_out(self):
        self.status_label.setText("")
        self.status_dot.setStyleSheet("background: transparent; border-radius: 5px;")
        self.question_label.hide()
        self.response_label.hide()
        self.hide()

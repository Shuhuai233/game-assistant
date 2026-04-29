"""
Settings dialog — GUI for configuring provider, API key, keybinds, language.
"""

import keyboard as kb_module
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QGroupBox, QTabWidget, QWidget, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import yaml
from config_loader import CONFIG_PATH


PROVIDERS = [
    ("deepseek", "DeepSeek", "https://api.deepseek.com"),
    ("siliconflow", "SiliconFlow (Free Tier)", "https://api.siliconflow.cn/v1"),
    ("openai", "OpenAI", "https://api.openai.com/v1"),
    ("groq", "Groq (Free Tier)", "https://api.groq.com/openai/v1"),
    ("ollama", "Ollama (Local)", "http://localhost:11434/v1"),
    ("custom", "Custom API", ""),
]

LANGUAGES = [
    ("zh", "Chinese / 中文"),
    ("en", "English"),
    ("ja", "Japanese / 日本語"),
    (None, "Auto-detect"),
]

TTS_VOICES = {
    "zh": [("zh-CN-XiaoxiaoNeural", "Xiaoxiao (Female)"), ("zh-CN-YunxiNeural", "Yunxi (Male)")],
    "en": [("en-US-JennyNeural", "Jenny (Female)"), ("en-US-GuyNeural", "Guy (Male)")],
    "ja": [("ja-JP-NanamiNeural", "Nanami (Female)"), ("ja-JP-KeitaNeural", "Keita (Male)")],
    None: [("zh-CN-XiaoxiaoNeural", "Xiaoxiao (Chinese Female)")],
}


class KeyBindButton(QPushButton):
    """A button that captures a key press when clicked."""

    def __init__(self, current_key: str = "", parent=None):
        super().__init__(parent)
        self.bound_key = current_key
        self._update_display()
        self._listening = False

    def _update_display(self):
        if self.bound_key:
            self.setText(f"[{self.bound_key.upper()}]  (click to rebind)")
        else:
            self.setText("(click to bind a key)")
        self.setStyleSheet(
            "QPushButton { padding: 8px 16px; font-size: 13px; }"
            "QPushButton:hover { background-color: #3a3a5a; }"
        )

    def mousePressEvent(self, event):
        if not self._listening:
            self._listening = True
            self.setText(">> Press any key... <<")
            self.setStyleSheet(
                "QPushButton { padding: 8px 16px; font-size: 13px; "
                "background-color: #cc4444; color: white; }"
            )
            # Use a timer to start listening (avoid capturing the mouse click)
            QTimer.singleShot(200, self._start_listening)

    def _start_listening(self):
        """Listen for a key press in a non-blocking way."""
        def on_key(event):
            if event.event_type == kb_module.KEY_DOWN:
                self.bound_key = event.name
                kb_module.unhook(hook)
                self._listening = False
                # Update display on UI thread
                QTimer.singleShot(0, self._update_display)

        hook = kb_module.hook(on_key)
        # Timeout: stop listening after 5 seconds
        QTimer.singleShot(5000, lambda: self._cancel_listening(hook))

    def _cancel_listening(self, hook):
        if self._listening:
            try:
                kb_module.unhook(hook)
            except:
                pass
            self._listening = False
            self._update_display()


class SettingsDialog(QDialog):
    """Settings window with tabs for Provider, Keys, Audio, Game."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Assistant - Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        self._load_config()
        self._init_ui()

    def _load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.raw = yaml.safe_load(f)
        except:
            self.raw = {}

    def _init_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_provider_tab(), "AI Provider")
        tabs.addTab(self._create_keys_tab(), "Key Bindings")
        tabs.addTab(self._create_audio_tab(), "Audio / Voice")
        tabs.addTab(self._create_game_tab(), "Game")
        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("padding: 8px 24px; font-size: 14px;")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 8px 24px; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    # --- Provider Tab ---
    def _create_provider_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Provider selector
        form = QFormLayout()
        self.provider_combo = QComboBox()
        current_provider = self.raw.get("llm", {}).get("provider", "deepseek")
        for i, (key, name, _) in enumerate(PROVIDERS):
            self.provider_combo.addItem(name, key)
            if key == current_provider:
                self.provider_combo.setCurrentIndex(i)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API key...")
        current_key = self.raw.get("llm", {}).get(current_provider, {}).get("api_key", "")
        if current_key and not current_key.startswith("your-"):
            self.api_key_input.setText(current_key)
        form.addRow("API Key:", self.api_key_input)

        # Model
        self.model_input = QLineEdit()
        current_model = self.raw.get("llm", {}).get(current_provider, {}).get("model", "")
        self.model_input.setText(current_model)
        self.model_input.setPlaceholderText("Model name (e.g. deepseek-chat)")
        form.addRow("Model:", self.model_input)

        # Base URL
        self.base_url_input = QLineEdit()
        current_url = self.raw.get("llm", {}).get(current_provider, {}).get("base_url", "")
        self.base_url_input.setText(current_url)
        self.base_url_input.setPlaceholderText("API endpoint URL")
        form.addRow("Base URL:", self.base_url_input)

        layout.addLayout(form)

        # Info label
        self.provider_info = QLabel()
        self.provider_info.setWordWrap(True)
        self.provider_info.setStyleSheet("color: #888; padding: 10px;")
        self._update_provider_info()
        layout.addWidget(self.provider_info)

        layout.addStretch()
        return widget

    def _on_provider_changed(self, index):
        key = self.provider_combo.currentData()
        prov = self.raw.get("llm", {}).get(key, {})
        api_key = prov.get("api_key", "")
        if api_key and not api_key.startswith("your-"):
            self.api_key_input.setText(api_key)
        else:
            self.api_key_input.clear()
        self.model_input.setText(prov.get("model", ""))
        self.base_url_input.setText(prov.get("base_url", ""))
        self._update_provider_info()

    def _update_provider_info(self):
        key = self.provider_combo.currentData()
        info_map = {
            "deepseek": "Recommended for China. Very cheap (~1 yuan/M tokens).\nSign up: platform.deepseek.com",
            "siliconflow": "Free tier available. China accessible.\nSign up: siliconflow.cn",
            "openai": "Requires VPN in China. Paid API.\nSign up: platform.openai.com",
            "groq": "Free tier with rate limits. Very fast.\nMay need VPN in China. Sign up: console.groq.com",
            "ollama": "Runs locally on your GPU. No API key needed.\nInstall: ollama.com",
            "custom": "Any OpenAI-compatible API endpoint.\nEnter your URL, key, and model name.",
        }
        self.provider_info.setText(info_map.get(key, ""))

    # --- Keys Tab ---
    def _create_keys_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        hk = self.raw.get("hotkey", {})

        layout.addWidget(QLabel("Click a button then press the key you want to bind:"))
        layout.addSpacing(10)

        form = QFormLayout()
        self.ptt_btn = KeyBindButton(hk.get("push_to_talk", "caps lock"))
        form.addRow("Push-to-Talk:", self.ptt_btn)

        self.screenshot_btn = KeyBindButton(hk.get("screenshot", "f8"))
        form.addRow("Screenshot + Ask:", self.screenshot_btn)

        self.quit_btn = KeyBindButton(hk.get("quit", "ctrl+shift+q"))
        form.addRow("Quit:", self.quit_btn)

        layout.addLayout(form)

        tip = QLabel("Tip: Use keys that don't conflict with your game.\n"
                      "Good choices: side mouse buttons, tilde (~), F keys, etc.")
        tip.setStyleSheet("color: #888; padding: 10px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        layout.addStretch()
        return widget

    # --- Audio Tab ---
    def _create_audio_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()

        # STT engine
        self.stt_combo = QComboBox()
        self.stt_combo.addItem("Faster Whisper (Local)", "faster_whisper")
        self.stt_combo.addItem("FunASR (Local, better Chinese)", "fun_asr")
        current_stt = self.raw.get("stt", {}).get("engine", "faster_whisper")
        idx = 0 if current_stt == "faster_whisper" else 1
        self.stt_combo.setCurrentIndex(idx)
        form.addRow("Speech Recognition:", self.stt_combo)

        # Language
        self.lang_combo = QComboBox()
        current_lang = self.raw.get("stt", {}).get("faster_whisper", {}).get("language", "zh")
        for i, (code, name) in enumerate(LANGUAGES):
            self.lang_combo.addItem(name, code)
            if code == current_lang:
                self.lang_combo.setCurrentIndex(i)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        form.addRow("Language:", self.lang_combo)

        # TTS voice
        self.voice_combo = QComboBox()
        self._populate_voices()
        form.addRow("TTS Voice:", self.voice_combo)

        # Screen capture
        self.screen_capture_check = QCheckBox("Enable screen capture (send screenshot to AI)")
        self.screen_capture_check.setChecked(
            self.raw.get("screen_capture", {}).get("enabled", False)
        )
        form.addRow("", self.screen_capture_check)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    def _on_language_changed(self):
        self._populate_voices()

    def _populate_voices(self):
        self.voice_combo.clear()
        lang = self.lang_combo.currentData()
        voices = TTS_VOICES.get(lang, TTS_VOICES[None])
        current_voice = self.raw.get("tts", {}).get("edge_tts", {}).get("voice", "")
        for i, (vid, vname) in enumerate(voices):
            self.voice_combo.addItem(vname, vid)
            if vid == current_voice:
                self.voice_combo.setCurrentIndex(i)

    # --- Game Tab ---
    def _create_game_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()

        self.game_name_input = QLineEdit()
        self.game_name_input.setText(self.raw.get("game", {}).get("name", "General"))
        self.game_name_input.setPlaceholderText("e.g. Elden Ring, Genshin Impact, L4D2...")
        form.addRow("Game Name:", self.game_name_input)

        layout.addLayout(form)

        layout.addWidget(QLabel("System Prompt (tells AI how to help you):"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(
            self.raw.get("game", {}).get("system_prompt", "You are a helpful game assistant.")
        )
        self.prompt_edit.setMinimumHeight(150)
        layout.addWidget(self.prompt_edit)

        tip = QLabel("Tip: Be specific! e.g. 'You are an Elden Ring expert. The player is in\n"
                      "Limgrave. Help with boss strategies, item locations, and NPC quests.'")
        tip.setStyleSheet("color: #888; padding: 5px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        return widget

    # --- Save ---
    def _save(self):
        """Save all settings to config.yaml."""
        # Provider
        provider_key = self.provider_combo.currentData()
        self.raw.setdefault("llm", {})
        self.raw["llm"]["provider"] = provider_key
        self.raw["llm"].setdefault(provider_key, {})
        api_key = self.api_key_input.text().strip()
        if api_key:
            self.raw["llm"][provider_key]["api_key"] = api_key
        model = self.model_input.text().strip()
        if model:
            self.raw["llm"][provider_key]["model"] = model
        base_url = self.base_url_input.text().strip()
        if base_url:
            self.raw["llm"][provider_key]["base_url"] = base_url

        # Keys
        self.raw.setdefault("hotkey", {})
        self.raw["hotkey"]["push_to_talk"] = self.ptt_btn.bound_key
        self.raw["hotkey"]["screenshot"] = self.screenshot_btn.bound_key
        self.raw["hotkey"]["quit"] = self.quit_btn.bound_key

        # Audio
        self.raw.setdefault("stt", {})
        self.raw["stt"]["engine"] = self.stt_combo.currentData()
        self.raw["stt"].setdefault("faster_whisper", {})
        self.raw["stt"]["faster_whisper"]["language"] = self.lang_combo.currentData()

        self.raw.setdefault("tts", {}).setdefault("edge_tts", {})
        self.raw["tts"]["edge_tts"]["voice"] = self.voice_combo.currentData()

        # Screen capture
        self.raw.setdefault("screen_capture", {})
        self.raw["screen_capture"]["enabled"] = self.screen_capture_check.isChecked()

        # Game
        self.raw.setdefault("game", {})
        self.raw["game"]["name"] = self.game_name_input.text().strip() or "General"
        self.raw["game"]["system_prompt"] = self.prompt_edit.toPlainText()

        # Write to file
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self.raw, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        self.accept()

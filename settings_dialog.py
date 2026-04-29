"""
Settings dialog — GUI for configuring provider, API key, keybinds, audio devices, language.
"""

import threading
import time
import numpy as np
import keyboard as kb_module
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QGroupBox, QTabWidget, QWidget, QCheckBox, QTextEdit,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
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
            QTimer.singleShot(200, self._start_listening)

    def _start_listening(self):
        def on_key(event):
            if event.event_type == kb_module.KEY_DOWN:
                self.bound_key = event.name
                kb_module.unhook(hook)
                self._listening = False
                QTimer.singleShot(0, self._update_display)

        hook = kb_module.hook(on_key)
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
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._load_config()
        self._init_ui()

    def _load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.raw = yaml.safe_load(f) or {}
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

        form = QFormLayout()
        self.provider_combo = QComboBox()
        current_provider = self.raw.get("llm", {}).get("provider", "deepseek")
        for i, (key, name, _) in enumerate(PROVIDERS):
            self.provider_combo.addItem(name, key)
            if key == current_provider:
                self.provider_combo.setCurrentIndex(i)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API key...")
        current_key = self.raw.get("llm", {}).get(current_provider, {}).get("api_key", "")
        if current_key and not current_key.startswith("your-"):
            self.api_key_input.setText(current_key)
        form.addRow("API Key:", self.api_key_input)

        self.model_input = QLineEdit()
        current_model = self.raw.get("llm", {}).get(current_provider, {}).get("model", "")
        self.model_input.setText(current_model)
        self.model_input.setPlaceholderText("Model name (e.g. deepseek-chat)")
        form.addRow("Model:", self.model_input)

        self.base_url_input = QLineEdit()
        current_url = self.raw.get("llm", {}).get(current_provider, {}).get("base_url", "")
        self.base_url_input.setText(current_url)
        self.base_url_input.setPlaceholderText("API endpoint URL")
        form.addRow("Base URL:", self.base_url_input)

        layout.addLayout(form)

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

        # --- Microphone ---
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("System Default", None)
        current_input = self.raw.get("audio", {}).get("input_device", None)
        try:
            from audio_recorder import get_input_devices
            for dev_idx, dev_name in get_input_devices():
                self.mic_combo.addItem(dev_name, dev_idx)
                if current_input is not None and dev_idx == int(current_input):
                    self.mic_combo.setCurrentIndex(self.mic_combo.count() - 1)
        except Exception:
            pass
        form.addRow("Microphone:", self.mic_combo)

        # --- Mic Test ---
        mic_test_layout = QHBoxLayout()

        self.mic_test_btn = QPushButton("Test Microphone")
        self.mic_test_btn.setStyleSheet("padding: 6px 16px;")
        self.mic_test_btn.clicked.connect(self._start_mic_test)
        mic_test_layout.addWidget(self.mic_test_btn)

        self.mic_stop_btn = QPushButton("Stop")
        self.mic_stop_btn.setStyleSheet("padding: 6px 16px;")
        self.mic_stop_btn.clicked.connect(self._stop_mic_test)
        self.mic_stop_btn.setEnabled(False)
        mic_test_layout.addWidget(self.mic_stop_btn)

        mic_test_layout.addStretch()
        form.addRow("", mic_test_layout)

        # Volume meter
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(True)
        self.volume_bar.setFormat("Volume: %v%")
        self.volume_bar.setFixedHeight(22)
        form.addRow("", self.volume_bar)

        # Mic test status label
        self.mic_status_label = QLabel("")
        self.mic_status_label.setStyleSheet("color: #888; padding: 2px;")
        self.mic_status_label.setWordWrap(True)
        form.addRow("", self.mic_status_label)

        # --- Speaker ---
        self.speaker_combo = QComboBox()
        self.speaker_combo.addItem("System Default", None)
        current_output = self.raw.get("audio", {}).get("output_device", None)
        try:
            from audio_recorder import get_output_devices
            for dev_idx, dev_name in get_output_devices():
                self.speaker_combo.addItem(dev_name, dev_idx)
                if current_output is not None and dev_idx == int(current_output):
                    self.speaker_combo.setCurrentIndex(self.speaker_combo.count() - 1)
        except Exception:
            pass
        form.addRow("Speaker:", self.speaker_combo)

        # --- Separator ---
        form.addRow(QLabel(""))

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

        # Mic test state
        self._mic_testing = False
        self._mic_test_thread = None
        self._volume_timer = QTimer()
        self._volume_timer.timeout.connect(self._update_volume_display)
        self._current_volume = 0
        self._peak_volume = 0
        self._mic_test_audio = None

        return widget

    def _start_mic_test(self):
        """Record from selected mic for 3 seconds, show live volume."""
        if self._mic_testing:
            return

        self._mic_testing = True
        self._peak_volume = 0
        self._mic_test_audio = None
        self.mic_test_btn.setEnabled(False)
        self.mic_stop_btn.setEnabled(True)
        self.mic_status_label.setText("Recording 3 seconds... Speak now!")
        self.mic_status_label.setStyleSheet("color: #ff4444; font-weight: bold; padding: 2px;")
        self.volume_bar.setValue(0)

        # Start volume update timer
        self._volume_timer.start(50)

        # Record in background thread
        self._mic_test_thread = threading.Thread(target=self._mic_test_worker, daemon=True)
        self._mic_test_thread.start()

    def _mic_test_worker(self):
        """Background thread: record 3 seconds and measure volume."""
        import sounddevice as sd

        device_idx = self.mic_combo.currentData()
        sample_rate = 16000
        duration = 3.0
        frames = []

        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                device=device_idx,
            ) as stream:
                start = time.time()
                while self._mic_testing and (time.time() - start) < duration:
                    data, _ = stream.read(1024)
                    frames.append(data.copy())
                    # Update live volume
                    chunk_peak = int(np.max(np.abs(data)))
                    self._current_volume = min(100, int(chunk_peak / 327))  # scale to 0-100
                    if chunk_peak > self._peak_volume:
                        self._peak_volume = chunk_peak
        except Exception as e:
            self._current_volume = -1  # signal error
            self._mic_test_error = str(e)

        if frames:
            self._mic_test_audio = np.concatenate(frames, axis=0)

        self._mic_testing = False
        # Schedule UI update on main thread
        QTimer.singleShot(0, self._mic_test_finished)

    def _update_volume_display(self):
        """Update the volume bar from the background thread's data."""
        if self._current_volume >= 0:
            self.volume_bar.setValue(self._current_volume)

            # Color the bar based on level
            if self._current_volume < 5:
                self.volume_bar.setStyleSheet("QProgressBar::chunk { background: #666; }")
            elif self._current_volume < 30:
                self.volume_bar.setStyleSheet("QProgressBar::chunk { background: #44aa44; }")
            elif self._current_volume < 70:
                self.volume_bar.setStyleSheet("QProgressBar::chunk { background: #44cc44; }")
            else:
                self.volume_bar.setStyleSheet("QProgressBar::chunk { background: #ff4444; }")

        if not self._mic_testing:
            self._volume_timer.stop()

    def _stop_mic_test(self):
        """Stop mic test early."""
        self._mic_testing = False

    def _mic_test_finished(self):
        """Called when mic test recording is done."""
        self.mic_test_btn.setEnabled(True)
        self.mic_stop_btn.setEnabled(False)
        self._volume_timer.stop()

        if self._current_volume < 0:
            # Error occurred
            self.mic_status_label.setText(
                f"Error: {getattr(self, '_mic_test_error', 'Unknown error')}\n"
                f"Check if the microphone is connected and not in use by another app."
            )
            self.mic_status_label.setStyleSheet("color: #ff4444; padding: 2px;")
            return

        peak = self._peak_volume
        peak_pct = min(100, int(peak / 327))

        if peak < 100:
            status = "SILENT — No audio detected!"
            detail = (
                "Your microphone is not picking up any sound.\n"
                "- Check if the correct microphone is selected above\n"
                "- Check if the mic is muted in Windows Sound settings\n"
                "- Try a different microphone"
            )
            color = "#ff4444"
        elif peak < 500:
            status = "VERY QUIET — Barely any audio"
            detail = (
                "The mic is picking up very little sound.\n"
                "- Try speaking louder or moving closer to the mic\n"
                "- Check mic volume in Windows Sound settings"
            )
            color = "#ffaa00"
        elif peak < 3000:
            status = "QUIET — Low volume"
            detail = "Try speaking louder or boost mic volume in Windows settings."
            color = "#ffaa00"
        elif peak < 20000:
            status = "GOOD — Mic is working!"
            detail = "Audio level looks good for speech recognition."
            color = "#44cc44"
        else:
            status = "LOUD — Mic is working! (may be too loud)"
            detail = "Consider lowering mic volume to avoid distortion."
            color = "#44cc44"

        self.mic_status_label.setText(f"{status} (peak: {peak_pct}%)\n{detail}")
        self.mic_status_label.setStyleSheet(f"color: {color}; padding: 2px;")
        self.volume_bar.setValue(peak_pct)

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

        # Audio devices
        self.raw.setdefault("audio", {})
        mic_dev = self.mic_combo.currentData()
        speaker_dev = self.speaker_combo.currentData()
        self.raw["audio"]["input_device"] = mic_dev
        self.raw["audio"]["output_device"] = speaker_dev

        # STT / TTS
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

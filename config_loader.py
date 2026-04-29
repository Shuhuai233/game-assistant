"""
Configuration loader for Game Assistant.
Reads config.yaml and provides typed access to settings.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


@dataclass
class LLMProviderConfig:
    api_key: str = ""
    model: str = ""
    base_url: str = ""


@dataclass
class Config:
    # LLM
    llm_provider: str = "deepseek"
    llm_configs: dict = field(default_factory=dict)

    # STT
    stt_engine: str = "faster_whisper"
    stt_model_size: str = "base"
    stt_language: Optional[str] = "zh"
    stt_device: str = "auto"
    stt_funasr_model: str = "iic/SenseVoiceSmall"

    # TTS
    tts_engine: str = "edge_tts"
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_rate: str = "+0%"
    tts_pyttsx3_rate: int = 180

    # Hotkeys
    hotkey_push_to_talk: str = "caps lock"
    hotkey_screenshot: str = "f8"
    hotkey_quit: str = "ctrl+shift+q"

    # Screen capture
    screen_capture_enabled: bool = False
    screen_capture_monitor: int = 0

    # Game context
    game_name: str = "General"
    game_system_prompt: str = "You are a helpful game assistant."


def load_config(path: str = CONFIG_PATH) -> Config:
    """Load configuration from YAML file."""
    if not os.path.exists(path):
        print(f"[Warning] Config file not found: {path}")
        print("[Warning] Using default settings. Copy config.yaml and edit it.")
        return Config()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    cfg = Config()

    # --- LLM ---
    llm = raw.get("llm", {})
    cfg.llm_provider = llm.get("provider", "deepseek")

    # Parse all provider configs
    for provider_name in ["deepseek", "siliconflow", "openai", "groq", "ollama", "custom"]:
        prov = llm.get(provider_name, {})
        cfg.llm_configs[provider_name] = LLMProviderConfig(
            api_key=prov.get("api_key", ""),
            model=prov.get("model", ""),
            base_url=prov.get("base_url", ""),
        )

    # --- STT ---
    stt = raw.get("stt", {})
    cfg.stt_engine = stt.get("engine", "faster_whisper")

    fw = stt.get("faster_whisper", {})
    cfg.stt_model_size = fw.get("model_size", "base")
    cfg.stt_language = fw.get("language", "zh")
    cfg.stt_device = fw.get("device", "auto")

    fa = stt.get("fun_asr", {})
    cfg.stt_funasr_model = fa.get("model", "iic/SenseVoiceSmall")

    # --- TTS ---
    tts = raw.get("tts", {})
    cfg.tts_engine = tts.get("engine", "edge_tts")

    et = tts.get("edge_tts", {})
    cfg.tts_voice = et.get("voice", "zh-CN-XiaoxiaoNeural")
    cfg.tts_rate = et.get("rate", "+0%")

    pt = tts.get("pyttsx3", {})
    cfg.tts_pyttsx3_rate = pt.get("rate", 180)

    # --- Hotkeys ---
    hk = raw.get("hotkey", {})
    cfg.hotkey_push_to_talk = hk.get("push_to_talk", "caps lock")
    cfg.hotkey_screenshot = hk.get("screenshot", "f8")
    cfg.hotkey_quit = hk.get("quit", "ctrl+shift+q")

    # --- Screen capture ---
    sc = raw.get("screen_capture", {})
    cfg.screen_capture_enabled = sc.get("enabled", False)
    cfg.screen_capture_monitor = sc.get("monitor", 0)

    # --- Game ---
    game = raw.get("game", {})
    cfg.game_name = game.get("name", "General")
    cfg.game_system_prompt = game.get("system_prompt", cfg.game_system_prompt)

    return cfg

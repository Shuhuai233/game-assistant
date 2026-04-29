"""
Configuration loader for Game Assistant.
Reads config.yaml and provides typed access to settings.
Auto-creates default config if missing.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional
from logger import logger


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

DEFAULT_CONFIG = {
    "llm": {
        "provider": "deepseek",
        "deepseek": {
            "api_key": "",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
        },
        "siliconflow": {
            "api_key": "",
            "model": "deepseek-ai/DeepSeek-V2.5",
            "base_url": "https://api.siliconflow.cn/v1",
        },
        "openai": {
            "api_key": "",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
        },
        "groq": {
            "api_key": "",
            "model": "llama-3.1-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1",
        },
        "ollama": {
            "api_key": "",
            "model": "qwen2.5:7b",
            "base_url": "http://localhost:11434/v1",
        },
        "custom": {
            "api_key": "",
            "model": "",
            "base_url": "",
        },
    },
    "stt": {
        "engine": "faster_whisper",
        "faster_whisper": {
            "model_size": "base",
            "language": "zh",
            "device": "auto",
        },
        "fun_asr": {
            "model": "iic/SenseVoiceSmall",
        },
    },
    "tts": {
        "engine": "edge_tts",
        "edge_tts": {
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
        },
        "pyttsx3": {
            "rate": 180,
        },
    },
    "hotkey": {
        "push_to_talk": "caps lock",
        "screenshot": "f8",
        "quit": "ctrl+shift+q",
    },
    "screen_capture": {
        "enabled": False,
        "monitor": 0,
    },
    "game": {
        "name": "General",
        "system_prompt": (
            "You are a helpful game assistant. The player will ask you questions "
            "about their current game. Help them with mission objectives, navigation, "
            "strategy, and tips. Keep answers concise and actionable. "
            "Respond in the same language the player uses."
        ),
    },
}


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

    # Audio devices (None = system default)
    audio_input_device: Optional[int] = None   # microphone device index
    audio_output_device: Optional[int] = None  # speaker device index

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


def is_first_run(path: str = CONFIG_PATH) -> bool:
    """Check if this is the first run (no config or no API key set)."""
    if not os.path.exists(path):
        return True
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        provider = raw.get("llm", {}).get("provider", "deepseek")
        api_key = raw.get("llm", {}).get(provider, {}).get("api_key", "")
        # Ollama doesn't need an API key
        if provider == "ollama":
            return False
        return not api_key or api_key.startswith("your-")
    except:
        return True


def ensure_config_exists(path: str = CONFIG_PATH):
    """Create default config.yaml if it doesn't exist."""
    if not os.path.exists(path):
        logger.info(f"Creating default config at {path}")
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_config(path: str = CONFIG_PATH) -> Config:
    """Load configuration from YAML file."""
    ensure_config_exists(path)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cfg = Config()

    # --- LLM ---
    llm = raw.get("llm", {})
    cfg.llm_provider = llm.get("provider", "deepseek")

    for provider_name in ["deepseek", "siliconflow", "openai", "groq", "ollama", "custom"]:
        prov = llm.get(provider_name, {})
        cfg.llm_configs[provider_name] = LLMProviderConfig(
            api_key=prov.get("api_key", ""),
            model=prov.get("model", ""),
            base_url=prov.get("base_url", ""),
        )

    # --- Audio devices ---
    audio = raw.get("audio", {})
    input_dev = audio.get("input_device", None)
    output_dev = audio.get("output_device", None)
    cfg.audio_input_device = int(input_dev) if input_dev is not None else None
    cfg.audio_output_device = int(output_dev) if output_dev is not None else None

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

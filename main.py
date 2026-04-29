"""
Game Assistant - Main Application
Push-to-talk AI assistant for gamers.

Usage:
    python main.py              # Run GUI (system tray + overlay)
    python main.py --cli        # Run in terminal mode (no GUI)
    python main.py --setup      # Interactive first-time setup (terminal)
    python main.py --rebind     # Re-bind hotkeys (terminal)
"""

import sys
import os
import time
import keyboard
from config_loader import load_config, CONFIG_PATH
from llm_client import LLMClient
from stt_engine import create_stt_engine
from tts_engine import create_tts_engine
from screen_capture import ScreenCapture
from audio_recorder import record_while_pressed


BANNER = """
=============================================
        Game Assistant
   Push-to-talk AI helper for gamers
=============================================
"""


def wait_for_key_press(prompt: str) -> str:
    """Wait for the user to press any key and return its name."""
    print(prompt, end="", flush=True)
    event = keyboard.read_event(suppress=True)
    # Wait for key down event
    while event.event_type != keyboard.KEY_DOWN:
        event = keyboard.read_event(suppress=True)
    key_name = event.name
    print(f" [{key_name}]")
    # Wait for key release to avoid ghost triggers
    time.sleep(0.3)
    return key_name


def run_keybind(raw: dict = None):
    """Interactive key binding. Can be called standalone or as part of setup."""
    import yaml

    if raw is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

    hk = raw.get("hotkey", {})
    current_ptt = hk.get("push_to_talk", "caps lock")
    current_screenshot = hk.get("screenshot", "f8")
    current_quit = hk.get("quit", "ctrl+shift+q")

    print("\n=== Key Binding ===\n")
    print(f"  Current push-to-talk: [{current_ptt}]")
    print(f"  Current screenshot:   [{current_screenshot}]")
    print(f"  Current quit:         [{current_quit}]")
    print()

    change = input("Rebind keys? (y/n, default: y): ").strip().lower()
    if change == "n":
        return raw

    # Push-to-talk
    ptt_key = wait_for_key_press("Press the key you want for PUSH-TO-TALK (hold to record):")

    # Screenshot
    print()
    change_ss = input("Rebind screenshot key? (y/n, default: n): ").strip().lower()
    if change_ss == "y":
        ss_key = wait_for_key_press("Press the key you want for SCREENSHOT + ASK AI:")
    else:
        ss_key = current_screenshot

    # Quit
    print()
    print(f"Quit hotkey stays as [{current_quit}] (edit config.yaml to change)")

    # Validate: warn if keys conflict
    if ptt_key == ss_key:
        print(f"\n[Warning] Push-to-talk and screenshot are both [{ptt_key}]. This will cause conflicts!")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("Key binding cancelled.")
            return raw

    # Save to config
    raw.setdefault("hotkey", {})
    raw["hotkey"]["push_to_talk"] = ptt_key
    raw["hotkey"]["screenshot"] = ss_key

    print(f"\n  Push-to-talk: [{ptt_key}]")
    print(f"  Screenshot:   [{ss_key}]")
    print(f"  Quit:         [{current_quit}]")

    return raw


def run_setup():
    """Interactive first-time setup."""
    import yaml

    print("\n=== Game Assistant Setup ===\n")
    print("This will help you configure your settings.\n")

    # --- Step 1: AI Provider ---
    providers = {
        "1": ("deepseek", "DeepSeek (recommended for China, very cheap)"),
        "2": ("siliconflow", "SiliconFlow (free tier, China accessible)"),
        "3": ("openai", "OpenAI (GPT-4o, needs VPN in China)"),
        "4": ("groq", "Groq (free tier, fast, needs VPN in China)"),
        "5": ("ollama", "Ollama (local, free, needs GPU)"),
        "6": ("custom", "Custom OpenAI-compatible API"),
    }

    print("Step 1: Select your AI provider:")
    for key, (_, desc) in providers.items():
        print(f"  {key}. {desc}")

    choice = input("\nEnter number (1-6): ").strip()
    if choice not in providers:
        print("Invalid choice. Exiting.")
        return

    provider_name, _ = providers[choice]

    if provider_name != "ollama":
        api_key = input(f"\nEnter your {provider_name} API key: ").strip()
    else:
        api_key = ""

    print(f"\n  Provider: {provider_name}")

    # Load existing config
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw["llm"]["provider"] = provider_name
    if api_key:
        raw["llm"][provider_name]["api_key"] = api_key

    # --- Step 2: Key Binding ---
    print("\nStep 2: Key Binding")
    raw = run_keybind(raw)

    # --- Step 3: Language ---
    print("\nStep 3: Voice language")
    print("  1. Chinese (zh)")
    print("  2. English (en)")
    print("  3. Japanese (ja)")
    print("  4. Auto-detect")
    lang_choice = input("Enter number (1-4, default: 1): ").strip()
    lang_map = {"1": "zh", "2": "en", "3": "ja", "4": None}
    lang = lang_map.get(lang_choice, "zh")

    raw.setdefault("stt", {}).setdefault("faster_whisper", {})
    raw["stt"]["faster_whisper"]["language"] = lang

    # Set TTS voice to match language
    voice_map = {
        "zh": "zh-CN-XiaoxiaoNeural",
        "en": "en-US-JennyNeural",
        "ja": "ja-JP-NanamiNeural",
        None: "zh-CN-XiaoxiaoNeural",
    }
    raw.setdefault("tts", {}).setdefault("edge_tts", {})
    raw["tts"]["edge_tts"]["voice"] = voice_map.get(lang, "zh-CN-XiaoxiaoNeural")

    # --- Save ---
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nSetup complete! Config saved to {CONFIG_PATH}")
    print(f"Run: python main.py")


def main():
    if "--setup" in sys.argv:
        run_setup()
        return

    if "--rebind" in sys.argv:
        import yaml
        raw = run_keybind()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"\nKeys saved to {CONFIG_PATH}")
        return

    print(BANNER)

    # Load config
    print("[Init] Loading configuration...")
    config = load_config()

    # Initialize components
    print("[Init] Setting up LLM client...")
    llm = LLMClient(config)

    print("[Init] Setting up Speech-to-Text...")
    stt = create_stt_engine(config)

    print("[Init] Setting up Text-to-Speech...")
    tts = create_tts_engine(config)

    print("[Init] Setting up screen capture...")
    screen = ScreenCapture(config)

    # Print controls
    print()
    print("=" * 45)
    print(f"  Hold [{config.hotkey_push_to_talk.upper()}] to talk")
    if config.screen_capture_enabled:
        print(f"  Press [{config.hotkey_screenshot.upper()}] to screenshot + ask")
    print(f"  Press [{config.hotkey_quit.upper()}] to quit")
    print(f"  AI Provider: {config.llm_provider}")
    print(f"  Game: {config.game_name}")
    print("=" * 45)
    print()
    print("Ready! Hold the push-to-talk key and speak...")
    print()

    # --- Main loop ---
    running = True

    def on_quit():
        nonlocal running
        running = False
        print("\n[App] Shutting down...")

    keyboard.add_hotkey(config.hotkey_quit, on_quit)

    try:
        while running:
            # Wait for push-to-talk key
            keyboard.wait(config.hotkey_push_to_talk)
            if not running:
                break

            # Small delay to ensure key is actually held
            time.sleep(0.05)
            if not keyboard.is_pressed(config.hotkey_push_to_talk):
                continue

            # Record audio
            audio_bytes = record_while_pressed(config.hotkey_push_to_talk)
            if audio_bytes is None:
                print("[Audio] No audio recorded.")
                continue

            # Transcribe
            print("[STT] Transcribing...")
            question = stt.transcribe(audio_bytes)
            if not question:
                print("[STT] No speech detected.")
                continue

            print(f"[You] {question}")

            # Capture screen if enabled
            screenshot_b64 = None
            if config.screen_capture_enabled:
                print("[Screen] Capturing...")
                screenshot_b64 = screen.capture()

            # Ask AI
            print("[AI] Thinking...")
            answer = llm.ask(question, screenshot_b64)
            print(f"[AI] {answer}")

            # Speak response
            print("[TTS] Speaking...")
            tts.speak(answer)
            print()

    except KeyboardInterrupt:
        print("\n[App] Interrupted by user.")
    finally:
        print("[App] Goodbye!")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        main()
    elif "--setup" in sys.argv or "--rebind" in sys.argv:
        main()
    else:
        # Default: launch GUI mode
        from app import main as gui_main
        gui_main()

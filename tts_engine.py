"""
Text-to-Speech module.
Supports edge-tts (free, online) and pyttsx3 (offline, Windows SAPI5).
"""

import asyncio
import tempfile
import os
import threading
from config_loader import Config


class TTSEngine:
    """Base TTS interface."""
    def speak(self, text: str):
        raise NotImplementedError


class EdgeTTSEngine(TTSEngine):
    """Free TTS using Microsoft Edge TTS (works in China)."""

    def __init__(self, config: Config):
        self.voice = config.tts_voice
        self.rate = config.tts_rate
        print(f"[TTS] Using Edge TTS, voice: {self.voice}")

    def speak(self, text: str):
        """Generate speech and play it."""
        asyncio.run(self._speak_async(text))

    async def _speak_async(self, text: str):
        import edge_tts

        tmp_path = os.path.join(tempfile.gettempdir(), "game_assistant_tts.mp3")

        communicate = edge_tts.Communicate(
            text,
            voice=self.voice,
            rate=self.rate
        )
        await communicate.save(tmp_path)

        # Play using pygame
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[TTS] Playback error: {e}")
            print("[TTS] Make sure pygame is installed: pip install pygame")
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass


class Pyttsx3Engine(TTSEngine):
    """Offline TTS using Windows SAPI5 voices via pyttsx3."""

    def __init__(self, config: Config):
        import pyttsx3
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", config.tts_pyttsx3_rate)
        print("[TTS] Using pyttsx3 (Windows SAPI5)")

    def speak(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()


def create_tts_engine(config: Config) -> TTSEngine:
    """Factory function to create the configured TTS engine."""
    engine = config.tts_engine

    if engine == "edge_tts":
        return EdgeTTSEngine(config)
    elif engine == "pyttsx3":
        return Pyttsx3Engine(config)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Supported: edge_tts, pyttsx3")

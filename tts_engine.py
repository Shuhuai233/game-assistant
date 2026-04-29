"""
Text-to-Speech module.
Supports edge-tts (free, online) and pyttsx3 (offline, Windows SAPI5).
Uses winsound/subprocess for playback — no pygame dependency.
"""

import asyncio
import tempfile
import os
import subprocess
import time
import threading
from config_loader import Config


class TTSEngine:
    """Base TTS interface."""
    def speak(self, text: str):
        raise NotImplementedError


def _play_audio_file(filepath: str):
    """
    Play an audio file on Windows without pygame.
    Tries multiple methods in order of preference.
    """
    try:
        # Method 1: Use Windows Media Player via PowerShell (works on all Windows)
        # This is non-blocking friendly and handles mp3 natively
        ps_cmd = (
            f'$player = New-Object System.Media.SoundPlayer; '
            f'Add-Type -AssemblyName presentationCore; '
            f'$media = New-Object System.Windows.Media.MediaPlayer; '
            f'$media.Open([Uri]"{filepath}"); '
            f'Start-Sleep -Milliseconds 300; '
            f'$media.Play(); '
            f'Start-Sleep -Milliseconds ($media.NaturalDuration.TimeSpan.TotalMilliseconds + 500); '
            f'$media.Close()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            timeout=60,
            capture_output=True
        )
        return
    except Exception:
        pass

    try:
        # Method 2: ffplay (if ffmpeg is installed)
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            timeout=60,
            capture_output=True
        )
        return
    except FileNotFoundError:
        pass

    print("[TTS] Warning: No audio player available. Install ffmpeg or use pyttsx3 engine.")


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

        # Play the audio file
        try:
            _play_audio_file(tmp_path)
        except Exception as e:
            print(f"[TTS] Playback error: {e}")
        finally:
            # Small delay before cleanup to ensure file isn't locked
            await asyncio.sleep(0.2)
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

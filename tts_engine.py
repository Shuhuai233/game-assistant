"""
Text-to-Speech module.
Supports edge-tts (free, online) and pyttsx3 (offline, Windows SAPI5).
Uses PowerShell MediaPlayer for playback. Supports output device selection.
"""

import asyncio
import tempfile
import os
import subprocess
from config_loader import Config
from logger import logger


class TTSEngine:
    """Base TTS interface."""
    def speak(self, text: str):
        raise NotImplementedError


def _play_audio_file(filepath: str, device_index: int = None):
    """
    Play an audio file on Windows.
    device_index: output device index (None = system default).
    """
    # If a specific device is requested, try sounddevice first
    if device_index is not None:
        try:
            import sounddevice as sd
            import soundfile as sf
            data, samplerate = sf.read(filepath)
            sd.play(data, samplerate, device=device_index)
            sd.wait()
            return
        except ImportError:
            logger.warning("soundfile not available, falling back to PowerShell")
        except Exception as e:
            logger.warning(f"sounddevice playback failed: {e}")

    # Fallback: PowerShell MediaPlayer (uses system default output)
    try:
        ps_cmd = (
            f'Add-Type -AssemblyName presentationCore; '
            f'$media = New-Object System.Windows.Media.MediaPlayer; '
            f'$media.Open([Uri]"{filepath}"); '
            f'Start-Sleep -Milliseconds 300; '
            f'$media.Play(); '
            f'Start-Sleep -Milliseconds ($media.NaturalDuration.TimeSpan.TotalMilliseconds + 500); '
            f'$media.Close()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            timeout=60,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        return
    except Exception as e:
        logger.warning(f"PowerShell playback failed: {e}")

    try:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath],
            timeout=60,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        return
    except FileNotFoundError:
        pass

    logger.error("No audio player available")


class EdgeTTSEngine(TTSEngine):
    """Free TTS using Microsoft Edge TTS (works in China)."""

    def __init__(self, config: Config):
        self.voice = config.tts_voice
        self.rate = config.tts_rate
        self.output_device = config.audio_output_device
        logger.info(f"TTS init: Edge TTS, voice={self.voice}, output_device={self.output_device}")

    def speak(self, text: str):
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

        try:
            _play_audio_file(tmp_path, self.output_device)
        except Exception as e:
            logger.error(f"TTS playback error: {e}")
        finally:
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
        logger.info("TTS init: pyttsx3")

    def speak(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()


def create_tts_engine(config: Config) -> TTSEngine:
    engine = config.tts_engine
    if engine == "edge_tts":
        return EdgeTTSEngine(config)
    elif engine == "pyttsx3":
        return Pyttsx3Engine(config)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")

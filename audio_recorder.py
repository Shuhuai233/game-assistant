"""
Audio recording module.
Handles push-to-talk recording via hotkey.
Supports selecting a specific microphone device.
"""

import io
import time
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import keyboard
from logger import logger

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"


def get_input_devices() -> list:
    """Return list of (index, name) for available input (microphone) devices."""
    devices = sd.query_devices()
    result = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            result.append((i, d['name']))
    return result


def get_output_devices() -> list:
    """Return list of (index, name) for available output (speaker) devices."""
    devices = sd.query_devices()
    result = []
    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            result.append((i, d['name']))
    return result


def record_while_pressed(hotkey: str, device_index: int = None, max_duration: float = 30.0) -> bytes:
    """
    Record audio while the hotkey is held down.
    Returns WAV file bytes.

    Args:
        hotkey: Key name to hold for recording
        device_index: Microphone device index (None = system default)
        max_duration: Max recording length in seconds
    """
    frames = []
    start_time = time.time()

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            device=device_index,
        ) as stream:
            while keyboard.is_pressed(hotkey):
                if time.time() - start_time > max_duration:
                    logger.info(f"Max recording duration ({max_duration}s) reached")
                    break
                data, _ = stream.read(1024)
                frames.append(data.copy())
    except Exception as e:
        logger.error(f"Recording error: {e}")
        return None

    if not frames:
        return None

    audio_data = np.concatenate(frames, axis=0)
    duration = len(audio_data) / SAMPLE_RATE
    logger.info(f"Recorded {duration:.1f}s of audio")

    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, SAMPLE_RATE, audio_data)
    wav_buffer.seek(0)
    return wav_buffer.read()

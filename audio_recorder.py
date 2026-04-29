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

# Minimum recording length in seconds — ignore accidental taps
MIN_DURATION = 0.5


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
    Returns WAV file bytes, or None if too short / silent.
    """
    frames = []
    start_time = time.time()

    logger.info(f"Recording started (key={hotkey}, mic={device_index})")

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
        logger.error(f"Recording error (mic device={device_index}): {e}")
        return None

    if not frames:
        logger.warning("No audio frames captured")
        return None

    audio_data = np.concatenate(frames, axis=0)
    duration = len(audio_data) / SAMPLE_RATE

    # Check audio level
    peak = np.max(np.abs(audio_data))
    rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
    logger.info(f"Recorded {duration:.1f}s | peak={peak} rms={rms:.0f}")

    # Too short — ignore accidental key taps
    if duration < MIN_DURATION:
        logger.info(f"Recording too short ({duration:.1f}s < {MIN_DURATION}s), ignoring")
        return None

    # Check if audio is essentially silent
    if peak < 100:
        logger.warning(
            f"Audio appears silent (peak={peak}). "
            f"Check microphone selection in Settings."
        )
        # Still return it — let STT decide

    # Convert to WAV bytes
    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, SAMPLE_RATE, audio_data)
    wav_buffer.seek(0)
    return wav_buffer.read()

"""
Audio recording module.
Handles push-to-talk recording via hotkey.
"""

import io
import time
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import keyboard


SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"


def record_while_pressed(hotkey: str, max_duration: float = 30.0) -> bytes:
    """
    Record audio while the hotkey is held down.
    Returns WAV file bytes.
    """
    print(f"[Audio] Recording... (release '{hotkey}' to stop)")
    frames = []
    start_time = time.time()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE) as stream:
        while keyboard.is_pressed(hotkey):
            if time.time() - start_time > max_duration:
                print(f"[Audio] Max duration ({max_duration}s) reached.")
                break
            data, _ = stream.read(1024)
            frames.append(data.copy())

    if not frames:
        return None

    audio_data = np.concatenate(frames, axis=0)
    duration = len(audio_data) / SAMPLE_RATE
    print(f"[Audio] Recorded {duration:.1f}s of audio")

    # Convert to WAV bytes
    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, SAMPLE_RATE, audio_data)
    wav_buffer.seek(0)
    return wav_buffer.read()


def wait_for_hotkey(hotkey: str):
    """Block until the hotkey is pressed."""
    keyboard.wait(hotkey)

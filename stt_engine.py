"""
Speech-to-Text module.
Supports faster-whisper (local) and FunASR (local).

IMPORTANT: ONNX Runtime GPU providers (CUDA, TensorRT) are disabled by default
to avoid crashes on systems without proper GPU drivers. STT runs on CPU which
is fast enough for short voice clips.
"""

import os
import sys
import tempfile
from config_loader import Config
from logger import logger

# ============================================================
# CRITICAL: Disable ONNX Runtime GPU providers BEFORE any import
# that might trigger onnxruntime. This prevents the
# "CUDA/TensorRT provider not available" crash on systems
# without NVIDIA GPU or proper drivers.
# ============================================================
os.environ["ORT_DISABLE_ALL_PROVIDERS"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Also tell ctranslate2 to use CPU
os.environ["CT2_FORCE_CPU"] = "1"

# Suppress ONNX runtime warnings
try:
    import onnxruntime
    # Force CPU execution provider only
    onnxruntime.set_default_logger_severity(3)  # suppress warnings
except ImportError:
    pass


class STTEngine:
    """Base STT interface."""
    def transcribe(self, audio_bytes: bytes) -> str:
        raise NotImplementedError


class FasterWhisperSTT(STTEngine):
    """Local STT using faster-whisper. Always runs on CPU for compatibility."""

    def __init__(self, config: Config):
        model_size = config.stt_model_size
        self.language = config.stt_language

        # Always use CPU to avoid ONNX/CUDA issues on end-user machines
        device = "cpu"
        compute_type = "int8"

        logger.info(f"Loading faster-whisper model '{model_size}' on {device} ({compute_type})")

        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4,
            )
            logger.info("STT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")
            raise RuntimeError(
                f"Speech recognition failed to load: {e}\n"
                f"Try restarting the application."
            )

    def transcribe(self, audio_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            # Try with VAD filter first
            segments, info = self.model.transcribe(
                tmp_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,
            )
            text_parts = []
            for seg in segments:
                logger.info(f"  segment: [{seg.start:.1f}s-{seg.end:.1f}s] '{seg.text}'")
                text_parts.append(seg.text)
            text = "".join(text_parts).strip()
            logger.info(f"Transcribed: lang={info.language} prob={info.language_probability:.2f} text='{text}'")
            return text
        except Exception as e:
            # If VAD fails (missing onnx file), retry without VAD
            if "ONNX" in str(e) or "NO_SUCHFILE" in str(e) or "silero" in str(e).lower():
                logger.warning(f"VAD filter failed ({e}), retrying without VAD...")
                try:
                    segments, info = self.model.transcribe(
                        tmp_path,
                        language=self.language,
                        beam_size=5,
                        vad_filter=False,
                    )
                    text_parts = []
                    for seg in segments:
                        logger.info(f"  segment (no VAD): [{seg.start:.1f}s-{seg.end:.1f}s] '{seg.text}'")
                        text_parts.append(seg.text)
                    text = "".join(text_parts).strip()
                    logger.info(f"Transcribed (no VAD): lang={info.language} text='{text}'")
                    return text
                except Exception as e2:
                    logger.error(f"Transcription failed even without VAD: {e2}")
                    return ""
            else:
                logger.error(f"Transcription failed: {e}")
                return ""
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass


class FunASRSTT(STTEngine):
    """Local STT using Alibaba FunASR (great for Chinese)."""

    def __init__(self, config: Config):
        from funasr import AutoModel

        model_name = config.stt_funasr_model
        logger.info(f"Loading FunASR model '{model_name}'")
        self.model = AutoModel(model=model_name)
        logger.info("FunASR model loaded")

    def transcribe(self, audio_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            result = self.model.generate(input=tmp_path)
            if result and len(result) > 0:
                return result[0].get("text", "").strip()
            return ""
        except Exception as e:
            logger.error(f"FunASR transcription failed: {e}")
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass


def create_stt_engine(config: Config) -> STTEngine:
    """Factory function to create the configured STT engine."""
    engine = config.stt_engine

    if engine == "faster_whisper":
        return FasterWhisperSTT(config)
    elif engine == "fun_asr":
        return FunASRSTT(config)
    else:
        raise ValueError(f"Unknown STT engine: {engine}")

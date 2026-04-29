"""
Speech-to-Text module.
Supports faster-whisper (local) and FunASR (local).
"""

import tempfile
import os
from config_loader import Config
from logger import logger


class STTEngine:
    """Base STT interface."""
    def transcribe(self, audio_bytes: bytes) -> str:
        raise NotImplementedError


class FasterWhisperSTT(STTEngine):
    """Local STT using faster-whisper."""

    def __init__(self, config: Config):
        model_size = config.stt_model_size
        device = config.stt_device

        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        compute_type = "float16" if device == "cuda" else "int8"
        self.language = config.stt_language

        logger.info(f"Loading faster-whisper model '{model_size}' on {device} ({compute_type})")

        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
        except Exception as e:
            # If CUDA/ONNX fails, fallback to CPU with int8
            if device != "cpu":
                logger.warning(f"Failed to load on {device}: {e}. Falling back to CPU.")
                from faster_whisper import WhisperModel
                self.model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8"
                )
            else:
                raise

        logger.info("STT model loaded")

    def transcribe(self, audio_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            segments, info = self.model.transcribe(
                tmp_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,
            )
            text = "".join(seg.text for seg in segments).strip()
            logger.info(f"Transcribed: lang={info.language} prob={info.language_probability:.2f}")
            return text
        except Exception as e:
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

from typing import Optional
from config.settings import Settings
from .utils import load_audio_to_mono_16k

# Whisper (local inference)
from faster_whisper import WhisperModel


class STTService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = settings.STT_ENGINE.upper()
        self._whisper_model = None

    def _load_whisper(self):
        if self._whisper_model is None:
            model_size = self.settings.WHISPER_MODEL_SIZE  # tiny/base/small
            self._whisper_model = WhisperModel(model_size, compute_type="int8")
        return self._whisper_model


    def transcribe(self, file_bytes: bytes, language: Optional[str] = "en") -> str:
        mono, sr = load_audio_to_mono_16k(file_bytes)
        if self.engine == "WHISPER":
            model = self._load_whisper()
            segments, info = model.transcribe(mono, language=language, beam_size=1)
            text = "".join([seg.text for seg in segments]).strip()
            return text
        else:
            return ""

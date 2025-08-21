import io
import pyttsx3
import numpy as np
import wave
import tempfile
from config.settings import Settings


class TTSService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine_name = settings.TTS_ENGINE.upper()
        self._pyttsx3 = None

    def _init_pyttsx3(self):
        if self._pyttsx3 is None:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.settings.VOICE_RATE)
            engine.setProperty("volume", self.settings.VOICE_VOLUME)
            self._pyttsx3 = engine
        return self._pyttsx3


    def synthesize(self, text: str) -> bytes:
        if self.engine_name == "PYTTSX3":
            return self._synthesize_pyttsx3(text)
        return self._synthesize_pyttsx3(text)

    def _synthesize_pyttsx3(self, text: str) -> bytes:
        engine = self._init_pyttsx3()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
            tmp_path = tf.name
        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                data = f.read()
            return data
        finally:
            try:
                import os
                os.unlink(tmp_path)
            except Exception:
                pass

    def _float32_to_wav_bytes(self, mono: np.ndarray, sr: int) -> bytes:
        mono_i16 = np.clip(mono, -1.0, 1.0)
        mono_i16 = (mono_i16 * 32767).astype(np.int16)
        with io.BytesIO() as buf:
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(mono_i16.tobytes())
            return buf.getvalue()

from config.settings import Settings
from tts.tts_service import TTSService

def test_tts_pyttsx3_runs():
s = Settings()
s.TTS_ENGINE = "PYTTSX3"
tts = TTSService(s)
data = tts.synthesize("Hello from the voice tutor.")
assert isinstance(data, (bytes, bytearray))
assert len(data) > 1000

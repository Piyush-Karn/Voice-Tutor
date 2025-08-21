from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Settings:
    # LLM
    LLM_PROVIDER: str = "MISTRAL_API"   # MISTRAL_API, OLLAMA, FALLBACK
    MISTRAL_API_KEY: str = ""
    MISTRAL_API_BASE: str = "https://api.mistral.ai/v1"
    MISTRAL_MODEL: str = "mistral-small-latest"
    OLLAMA_HOST: str = "http://localhost:11434" 

    # STT
    STT_ENGINE: str = "WHISPER"        
    WHISPER_MODEL_SIZE: str = "base"    # tiny, base, small

    # TTS
    TTS_ENGINE: str = "PYTTSX3"       
    VOICE_RATE: int = 160
    VOICE_VOLUME: float = 0.9

    # General
    LANGUAGE: str = "en"
    CHILD_MIN_AGE: int = 6
    CHILD_MAX_AGE: int = 12

    @staticmethod
    def load():
        load_dotenv()
        s = Settings()

        # LLM
        s.LLM_PROVIDER = os.getenv("LLM_PROVIDER", s.LLM_PROVIDER)
        s.MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", s.MISTRAL_API_KEY)
        s.MISTRAL_API_BASE = os.getenv("MISTRAL_API_BASE", s.MISTRAL_API_BASE)
        s.MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", s.MISTRAL_MODEL)
        s.OLLAMA_HOST = os.getenv("OLLAMA_HOST", s.OLLAMA_HOST)

        # STT
        s.STT_ENGINE = os.getenv("STT_ENGINE", s.STT_ENGINE)
        s.WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", s.WHISPER_MODEL_SIZE)

        # TTS
        s.TTS_ENGINE = os.getenv("TTS_ENGINE", s.TTS_ENGINE)
        s.VOICE_RATE = int(os.getenv("VOICE_RATE", s.VOICE_RATE))
        s.VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", s.VOICE_VOLUME))

        # General
        s.LANGUAGE = os.getenv("LANGUAGE", s.LANGUAGE)
        s.CHILD_MIN_AGE = int(os.getenv("CHILD_MIN_AGE", s.CHILD_MIN_AGE))
        s.CHILD_MAX_AGE = int(os.getenv("CHILD_MAX_AGE", s.CHILD_MAX_AGE))
        return s

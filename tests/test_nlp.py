from config.settings import Settings
from nlp.mistral_service import LLMService

def test_llm_fallback():
s = Settings()
s.LLM_PROVIDER = "FALLBACK"
llm = LLMService(s)
out = llm.generate("What is a noun?")
assert "noun" in out.lower()


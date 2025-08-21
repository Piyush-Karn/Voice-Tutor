from typing import Optional, List, Tuple
import requests
from config.settings import Settings
from .prompt_templates import kid_tutor_system_prompt, few_shots

class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _mistral_chat(self, system: str, user: str) -> Optional[str]:
        try:
            url = f"{self.settings.MISTRAL_API_BASE}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.settings.MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.settings.MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 200,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if not r.ok:
                return None
            data = r.json()
            choices = data.get("choices", [])
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content", "")
            return (content or "").strip()
        except Exception:
            return None

    def _ollama_complete(self, system: str, user: str) -> Optional[str]:
        try:
            url = f"{self.settings.OLLAMA_HOST}/api/generate"
            prompt = f"System: {system}\nUser: {user}\nAssistant:"
            payload = {
                "model": self.settings.MISTRAL_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 200}
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.ok:
                data = r.json()
                return data.get("response", "").strip()
            return None
        except Exception:
            return None

    def _fallback_answer(self, user: str) -> str:
        user_lc = user.lower().strip()
        pairs: List[Tuple[str, str]] = few_shots()
        for q, a in pairs:
            if q.lower().rstrip("?") in user_lc:
                return a
        if "noun" in user_lc:
            return "A noun names a person, place, or thing. For example: teacher, park, or pencil. Can you give one?"
        if "verb" in user_lc:
            return "A verb is an action word, like run, jump, or read. What action can you think of?"
        if "planet" in user_lc:
            return "We live on Earth. It is one of eight planets that orbit the Sun. Which planet do you know?"
        return "That’s a great question! Can you tell me a bit more, or give an example, so I can help better?"

    def generate(self, user_text: str) -> str:
        system = kid_tutor_system_prompt(
            lang=self.settings.LANGUAGE,
            min_age=self.settings.CHILD_MIN_AGE,
            max_age=self.settings.CHILD_MAX_AGE
        )
        provider = self.settings.LLM_PROVIDER.upper()
        if provider == "MISTRAL_API" and self.settings.MISTRAL_API_KEY:
            out = self._mistral_chat(system, user_text)
            if out:
                return out
        if provider == "OLLAMA":
            out = self._ollama_complete(system, user_text)
            if out:
                return out
        return self._fallback_answer(user_text)

from typing import Optional, List, Tuple
import requests
from config.settings import Settings
from .prompt_templates import kid_tutor_system_prompt, few_shots

class LLMService:
    def __init__(self, settings: Settings, strict_api: bool = False):
        self.settings = settings
        self.strict_api = strict_api

    def _mistral_chat(self, system: str, user: str) -> Optional[str]:
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
            "temperature": 0.6,
            "max_tokens": 220,
            "top_p": 0.9,
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if not r.ok:
                print("Mistral API error", r.status_code, r.text)
                return None
            data = r.json()
            choices = data.get("choices", [])
            if not choices:
                print("Mistral API no choices", data)
                return None
            content = choices[0].get("message", {}).get("content", "")
            return (content or "").strip()
        except Exception as e:
            print("Mistral API exception", e)
            return None

    def _ollama_complete(self, system: str, user: str) -> Optional[str]:
        try:
            url = f"{self.settings.OLLAMA_HOST}/api/generate"
            prompt = f"System: {system}\nUser: {user}\nAssistant:"
            payload = {
                "model": self.settings.MISTRAL_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.6, "num_predict": 220}
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.ok:
                data = r.json()
                return data.get("response", "").strip()
            return None
        except Exception as e:
            print("Ollama exception", e)
            return None

    def _fallback_answer(self, user: str) -> str:
        user_lc = user.lower().strip()
        pairs: List[Tuple[str, str]] = few_shots()
        for q, a in pairs:
            if q.lower().rstrip("?") in user_lc:
                return a
        if "noun" in user_lc:
            return "A noun names a person, place, or thing. For example: teacher, park, or pencil. Can you give one?"
        if "adjective" in user_lc:
            return "An adjective describes a noun, like red, small, or happy. Can you describe your favorite toy?"
        if "verb" in user_lc:
            return "A verb is an action word, like run, jump, or read. What action can you think of?"
        return "Good question! Tell me a bit more, or give an example, so I can help better."

    def _safe_prompt(self, user_text: str) -> str:
        banned = ["gun", "drug", "sex", "suicide", "violence"]
        if any(w in user_text.lower() for w in banned):
            return "I’m here to help with safe learning topics. Let’s choose a school subject like math, reading, or science."
        return ""

    def generate(self, user_text: str) -> str:
        redirect = self._safe_prompt(user_text)
        if redirect:
            return redirect

        system = (
            kid_tutor_system_prompt(
                lang=self.settings.LANGUAGE,
                min_age=self.settings.CHILD_MIN_AGE,
                max_age=self.settings.CHILD_MAX_AGE
            )
            + " Answer in 2–5 short sentences, using only plain text and basic punctuation (.,!?). "
              "Do not include emojis, emoticons, markdown, lists, or any special symbols."
        )

        provider = self.settings.LLM_PROVIDER.upper()
        if provider == "MISTRAL_API" and self.settings.MISTRAL_API_KEY:
            out = self._mistral_chat(system, user_text)
            if out:
                return out
            if self.strict_api:
                return "I couldn’t reach the AI service (Mistral). Please check your API key, model name, and internet connection."

        if provider == "OLLAMA":
            out = self._ollama_complete(system, user_text)
            if out:
                return out
            if self.strict_api:
                return "Local model is unavailable."

        if self.strict_api:
            return "No AI provider is configured."
        return self._fallback_answer(user_text)

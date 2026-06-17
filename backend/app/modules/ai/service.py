import litellm

from app.config import get_settings

settings = get_settings()


class AIService:
    """Internal AI service — wraps LiteLLM. Never imported from outside this module."""

    async def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await litellm.acompletion(
            model=settings.active_llm_model,
            messages=messages,
            api_base=settings.ollama_base_url if settings.llm_profile == "dev" else None,
            api_key=self._get_api_key(),
        )
        return response.choices[0].message.content or ""

    def _get_api_key(self) -> str | None:
        if settings.llm_profile == "prod":
            return settings.groq_api_key
        if settings.llm_profile == "fallback":
            return settings.openrouter_api_key
        return None

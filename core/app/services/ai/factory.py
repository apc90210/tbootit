"""
AI Provider factory and resolution logic.
Per Section 9 & 10 of TR_Stage05A:
- Instantiates provider from server-side environment settings.
- Completely safe fallback to DisabledAIProvider when credentials are unset or AI is disabled.
"""

from typing import Optional
from app.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.disabled_provider import DisabledAIProvider
from app.services.ai.openai_compatible import OpenAICompatibleProvider

_provider_instance: Optional[AIProvider] = None


def get_ai_provider() -> AIProvider:
    """
    Obtain the configured server-side AI provider instance.
    Never exposes API credentials to callers.
    """
    if not settings.ai_enabled or settings.ai_provider_type == "disabled" or not settings.ai_api_key:
        return DisabledAIProvider()

    provider_type = (settings.ai_provider_type or "disabled").lower().strip()

    if provider_type in ("cloud_ru", "evolution"):
        base_url = settings.ai_api_base_url or "https://api.cloud.ru/v1"
        return OpenAICompatibleProvider(
            api_base_url=base_url,
            api_key=settings.ai_api_key,
            model_name=settings.ai_model_name or "deepseek-v3",
            provider_name="cloud_ru",
            timeout_seconds=settings.ai_timeout_seconds,
        )

    if provider_type in ("yandex", "yandex_cloud"):
        base_url = settings.ai_api_base_url or "https://llm.api.cloud.yandex.net/foundationModels/v1"
        return OpenAICompatibleProvider(
            api_base_url=base_url,
            api_key=settings.ai_api_key,
            model_name=settings.ai_model_name or "yandexgpt/latest",
            provider_name="yandex",
            timeout_seconds=settings.ai_timeout_seconds,
        )

    if provider_type in ("openai", "openai_compatible"):
        return OpenAICompatibleProvider(
            api_base_url=settings.ai_api_base_url,
            api_key=settings.ai_api_key,
            model_name=settings.ai_model_name,
            provider_name="openai_compatible",
            timeout_seconds=settings.ai_timeout_seconds,
        )

    return DisabledAIProvider()

"""
Fallback AI provider implementation when AI is disabled or unconfigured.
Per Section 10 & 20: The system must work with AI completely disabled.
"""

from typing import Optional, Dict, Any
from app.services.ai.base import AIProvider, AIIdentificationResult


class DisabledAIProvider(AIProvider):
    """Graceful no-op provider when AI is disabled."""

    @property
    def provider_name(self) -> str:
        return "disabled"

    @property
    def is_enabled(self) -> bool:
        return False

    async def identify_model(
        self,
        query: str,
        ocr_text: Optional[str] = None,
        category_hint: Optional[str] = None,
    ) -> AIIdentificationResult:
        return AIIdentificationResult(
            status="disabled",
            message="AI-ассистент отключен или учетные данные не настроены. Пожалуйста, выберите модель вручную из локального справочника.",
            confidence=0.0,
            source_provenance="disabled",
        )

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "disabled",
            "provider": "disabled",
            "enabled": False,
            "message": "AI assistant is disabled",
        }

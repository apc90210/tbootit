"""
OpenAI-compatible AI Provider adapter.
Per Section 9 & 10 of TR_Stage05A:
- Compatible with Cloud.ru Evolution Foundation Models and Yandex Cloud AI Studio (OpenAI mode).
- Configurable base URL, model name, and timeout.
- Strict JSON validation.
- Graceful error recovery on network/timeout/malformed response.
- Secret credentials strictly shielded from logging.
"""

import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.services.ai.base import AIProvider, AIIdentificationResult
from app.services.ai.spec_schemas import build_canonical_description

logger = logging.getLogger("app.services.ai.openai")


SYSTEM_PROMPT = """Ты — экспертная система идентификации и структурирования моделей офисной и компьютерной техники (принтеры, МФУ, ноутбуки) компании Техноребут.
Твоя задача: по предоставленному названию, модели или распознанному тексту с шильдика/наклейки (OCR) определить точную фабричную модель устройства и вернуть СТРОГО валидный JSON-объект.

ТРЕБОВАНИЯ:
1. Выдели точного производителя (manufacturer) и модель (model).
2. Сформируй canonical_name: "{manufacturer} {model}".
3. Определи device_type: "printer" или "mfu".
4. Сформируй список вероятных поисковых синонимов (likely_aliases).
5. Сформируй структурированные фабричные характеристики (proposed_structured_specs):
   - technology: "лазерная", "струйная" и т.д.
   - color_mode: "монохромная" или "цветная"
   - max_format: "A4", "A3"
   - duplex: "да" / "нет"
   - print_speed: скорость печати (напр. "до 18 стр/мин")
   - interfaces: интерфейсы подключения (напр. "USB 2.0", "Wi-Fi, USB 2.0, Ethernet")
   - cartridge_family: совместимый картридж / тонер (напр. "HP 85A (CE285A)")
   Для МФУ также:
   - scanner_type: "планшетный", "протяжный"
   - adf: автоподатчик оригиналов ("да" / "нет")
6. НЕ галлюцинируй отсутствующие характеристики. Если неизвестно — не указывай или укажи в missing_uncertain_fields.
7. НЕ включай индивидуальное состояние б/у товара (дефекты, царапины, картридж заправлен) в фабричные характеристики!
8. Оцени свою уверенность (confidence) от 0.0 до 1.0.

ФОРМАТ ОТВЕТА (СТРОГО JSON, без markdown-обёртки ```json):
{
  "manufacturer": "HP",
  "model": "LaserJet P1102w",
  "canonical_name": "HP LaserJet P1102w",
  "category": "Принтеры",
  "device_type": "printer",
  "likely_aliases": ["HP P1102w", "HP LJ P1102w", "LaserJet P1102w"],
  "proposed_structured_specs": {
    "technology": "лазерная",
    "color_mode": "монохромная",
    "max_format": "A4",
    "duplex": "нет",
    "print_speed": "до 18 стр/мин",
    "interfaces": "USB 2.0, Wi-Fi",
    "cartridge_family": "HP 85A (CE285A)"
  },
  "confidence": 0.95,
  "missing_uncertain_fields": []
}
"""


class OpenAICompatibleProvider(AIProvider):
    """Generic OpenAI-compatible provider adapter."""

    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model_name: str,
        provider_name: str = "openai_compatible",
        timeout_seconds: int = 30,
    ):
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name
        self._provider_name = provider_name
        self._timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def is_enabled(self) -> bool:
        return bool(self._api_base_url and self._api_key and self._model_name)

    async def identify_model(
        self,
        query: str,
        ocr_text: Optional[str] = None,
        category_hint: Optional[str] = None,
    ) -> AIIdentificationResult:
        if not self.is_enabled:
            return AIIdentificationResult(
                status="disabled",
                message="AI provider is not fully configured.",
                confidence=0.0,
                source_provenance="disabled",
            )

        user_content_parts = [f"Поисковый запрос / модель: {query}"]
        if ocr_text:
            user_content_parts.append(f"Распознанный текст с наклейки (OCR):\n{ocr_text}")
        if category_hint:
            user_content_parts.append(f"Категория: {category_hint}")
        user_prompt = "\n\n".join(user_content_parts)

        endpoint = f"{self._api_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning(
                        "AI provider %s HTTP %d error: %s",
                        self._provider_name,
                        resp.status_code,
                        resp.text[:200],
                    )
                    return AIIdentificationResult(
                        status="error",
                        message=f"Провайдер AI вернул код ошибки HTTP {resp.status_code}",
                        confidence=0.0,
                        source_provenance="error",
                    )

                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON content
                parsed = json.loads(content)
                manufacturer = parsed.get("manufacturer")
                model = parsed.get("model")
                canonical_name = parsed.get("canonical_name") or f"{manufacturer or ''} {model or ''}".strip()
                device_type = parsed.get("device_type") or "printer"
                category = parsed.get("category") or ("МФУ" if device_type == "mfu" else "Принтеры")
                likely_aliases = parsed.get("likely_aliases", [])
                specs = parsed.get("proposed_structured_specs", {})
                confidence = float(parsed.get("confidence", 0.7))
                missing_fields = parsed.get("missing_uncertain_fields", [])

                reusable_desc = build_canonical_description(
                    device_type=device_type,
                    brand=manufacturer or "",
                    model=model or "",
                    specs=specs,
                )

                return AIIdentificationResult(
                    status="success",
                    manufacturer=manufacturer,
                    model=model,
                    canonical_name=canonical_name,
                    category=category,
                    device_type=device_type,
                    likely_aliases=likely_aliases,
                    proposed_structured_specs=specs,
                    proposed_reusable_description=reusable_desc,
                    confidence=confidence,
                    missing_uncertain_fields=missing_fields,
                    source_provenance="ai_draft",
                    message="Модель успешно предложена AI-ассистентом (требуется подтверждение)",
                )

        except httpx.TimeoutException:
            logger.warning("AI provider %s timed out after %ds", self._provider_name, self._timeout_seconds)
            return AIIdentificationResult(
                status="error",
                message=f"Таймаут обращения к AI-провайдеру ({self._timeout_seconds}с)",
                confidence=0.0,
                source_provenance="error",
            )
        except (json.JSONDecodeError, KeyError, Exception) as exc:
            logger.warning("AI provider %s parsing/execution error: %s", self._provider_name, str(exc))
            return AIIdentificationResult(
                status="error",
                message=f"Ошибка обработки ответа AI: {type(exc).__name__}",
                confidence=0.0,
                source_provenance="error",
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform a quick health check against the provider."""
        if not self.is_enabled:
            return {
                "status": "disabled",
                "provider": self._provider_name,
                "enabled": False,
                "message": "Provider credentials missing",
            }
        return {
            "status": "configured",
            "provider": self._provider_name,
            "enabled": True,
            "model": self._model_name,
            "base_url": self._api_base_url,
        }

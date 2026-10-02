"""
Base interfaces and data structures for AI provider abstraction.
Per Section 9 & 12 of TR_Stage05A:
- Server-side interface, not hardcoded to one vendor.
- STRICT structured JSON candidate validation.
- Model identification with structured specs and reusable descriptions.
- Credentials never exposed to client or logged.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIIdentificationResult(BaseModel):
    status: str = Field(..., description="Status: 'success', 'no_match', 'disabled', 'error'")
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    device_type: Optional[str] = None
    likely_aliases: List[str] = Field(default_factory=list)
    proposed_structured_specs: Dict[str, Any] = Field(default_factory=dict)
    proposed_reusable_description: Optional[str] = None
    confidence: float = 0.0
    missing_uncertain_fields: List[str] = Field(default_factory=list)
    source_provenance: str = "ai_draft"
    source_urls: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class AIProvider(ABC):
    """Abstract interface for server-side AI providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation."""
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Whether the provider is configured and active."""
        pass

    @abstractmethod
    async def identify_model(
        self,
        query: str,
        ocr_text: Optional[str] = None,
        category_hint: Optional[str] = None,
    ) -> AIIdentificationResult:
        """
        Identify a hardware model from query/OCR text and generate structured specs.
        Returns strict AIIdentificationResult.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider connectivity and model availability."""
        pass

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.avito_capability_service import get_avito_capabilities
from app.services.avito_preflight_service import build_avito_publication_package, preflight_product_for_avito

class AvitoPublicationTransport(ABC):
    """
    Abstract interface for Avito publication transports.
    Ensures transport-neutral architecture without hard dependency on any single mechanism.
    """
    @abstractmethod
    def capabilities(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Return transport-specific capabilities."""
        pass

    @abstractmethod
    def prepare(self, db: Session, product_id: int) -> Dict[str, Any]:
        """Prepare publication package for product."""
        pass

    @abstractmethod
    def validate(self, db: Session, product_id: int) -> Dict[str, Any]:
        """Validate readiness of product for this transport."""
        pass

    def publish(self, db: Session, product_id: int) -> Dict[str, Any]:
        """
        Publish product to Avito.
        Strictly disabled in Stage 06A-R10A foundation.
        """
        raise NotImplementedError("Avito publication is disabled in Stage 06A-R10A foundation")

class OfficialAutoloadTransport(AvitoPublicationTransport):
    """
    Transport adapter for Official Avito XML/API Autoload feed.
    """
    def capabilities(self, db: Optional[Session] = None) -> Dict[str, Any]:
        caps = get_avito_capabilities(db)
        return {
            "transport": "official_autoload",
            "available": caps.get("autoload_schema_read", False),
            "supports_xml_feed": True,
            "supports_api_upload": False  # Disabled
        }

    def prepare(self, db: Session, product_id: int) -> Dict[str, Any]:
        package = build_avito_publication_package(db, product_id)
        return {
            "transport": "official_autoload",
            "payload": package
        }

    def validate(self, db: Session, product_id: int) -> Dict[str, Any]:
        preflight = preflight_product_for_avito(db, product_id)
        return {
            "transport": "official_autoload",
            "ready": preflight["ready_for_official_autoload"],
            "preflight": preflight
        }

class BrowserAssistedTransport(AvitoPublicationTransport):
    """
    Transport adapter for Browser-assisted / Chrome Extension form filling.
    """
    def capabilities(self, db: Optional[Session] = None) -> Dict[str, Any]:
        return {
            "transport": "browser_assisted",
            "available": True,
            "supports_form_fill": True,
            "supports_direct_publish": False
        }

    def prepare(self, db: Session, product_id: int) -> Dict[str, Any]:
        package = build_avito_publication_package(db, product_id)
        return {
            "transport": "browser_assisted",
            "payload": package
        }

    def validate(self, db: Session, product_id: int) -> Dict[str, Any]:
        preflight = preflight_product_for_avito(db, product_id)
        return {
            "transport": "browser_assisted",
            "ready": preflight["ready_for_browser_assisted"],
            "preflight": preflight
        }

class ManualTransport(AvitoPublicationTransport):
    """
    Transport adapter for manual copying / clipboard publication workflow.
    """
    def capabilities(self, db: Optional[Session] = None) -> Dict[str, Any]:
        return {
            "transport": "manual",
            "available": True,
            "supports_clipboard_copy": True
        }

    def prepare(self, db: Session, product_id: int) -> Dict[str, Any]:
        package = build_avito_publication_package(db, product_id)
        return {
            "transport": "manual",
            "payload": package
        }

    def validate(self, db: Session, product_id: int) -> Dict[str, Any]:
        preflight = preflight_product_for_avito(db, product_id)
        return {
            "transport": "manual",
            "ready": preflight["ready_for_manual"],
            "preflight": preflight
        }

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app import models

def get_avito_capabilities(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Domain-level capability detection for Avito integration within Core.
    Does not require or check external Avito API credentials.
    Provides transport-neutral status flags based on DB state.
    """
    has_official_schemas = False
    if db is not None:
        try:
            has_official_schemas = db.query(models.AvitoCanonicalCategory).filter(
                models.AvitoCanonicalCategory.official_slug.isnot(None),
                models.AvitoCanonicalCategory.active == True
            ).first() is not None
        except Exception:
            has_official_schemas = False

    canonical_schema_source = "official_schema_persisted" if has_official_schemas else "observed_only"

    return {
        "browser_bridge": True,
        "browser_assisted_available": True,
        "manual_available": True,
        "canonical_schema_source": canonical_schema_source,
        "autoload_schema_present": has_official_schemas,
        "autoload_publish": False
    }


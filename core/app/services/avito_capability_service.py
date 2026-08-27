from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings

def get_avito_capabilities(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Capability-based detection for Avito integration.
    Never assumes paid or official API availability.
    Provides transport-neutral status flags.
    """
    api_configured = bool(settings.avito_client_id and settings.avito_client_secret)
    
    canonical_schema_source = "observed_only"
    if api_configured:
        canonical_schema_source = "official_api_ready"
    
    return {
        "browser_bridge": True,
        "browser_assisted_available": True,
        "manual_available": True,
        "api_configured": api_configured,
        "api_authenticated": False,
        "autoload_schema_read": api_configured,
        "autoload_publish": False,  # Publishing is disabled in Stage 06A-R10A
        "canonical_schema_source": canonical_schema_source
    }

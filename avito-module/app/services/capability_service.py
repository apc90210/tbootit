from typing import Dict, Any
from app.config import settings

def get_avito_external_capabilities() -> Dict[str, Any]:
    """
    Probe external Avito API and Autoload capabilities.
    Owned exclusively by avito-module.
    """
    api_configured = bool(settings.AVITO_CLIENT_ID and settings.AVITO_CLIENT_SECRET)
    return {
        "api_configured": api_configured,
        "api_authenticated": False,
        "autoload_schema_endpoint_accessible": api_configured,
        "autoload_publish_accessible": False,  # disabled in Stage 06A-R10A
        "browser_bridge_active": True
    }

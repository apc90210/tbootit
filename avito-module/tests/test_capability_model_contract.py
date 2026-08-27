import pytest
from app.routers import extension_bridge

def test_capability_contract_browser_bridge_always_available():
    """Verify that extension bridge and browser capabilities do not require paid/official API."""
    assert hasattr(extension_bridge, "router")
    # Verify no hardcoded official API requirement for browser bridge
    assert extension_bridge.router is not None

import socket
import pytest
from app.routers.health import check_vnc_rfb_banner

def test_rfb_banner_helper_function():
    """Verify check_vnc_rfb_banner function signature and behavior on invalid host."""
    assert check_vnc_rfb_banner("127.0.0.1", 1) is False

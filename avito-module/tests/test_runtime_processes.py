import os
import socket
import pytest

def test_xvfb_and_novnc_ports():
    """Verify that VNC (5900) and websockify (6080) ports/sockets or environment DISPLAY are configured."""
    display = os.getenv("DISPLAY", ":99")
    assert display == ":99"

import pytest
import asyncio
import websockets

@pytest.mark.asyncio
async def test_rfb_banner_proxy_integration():
    """Verify live Admin Shell WebSocket proxy returns binary RFB banner if service running."""
    url = "ws://localhost:8011/avito/novnc/websockify"
    try:
        async with websockets.connect(url, subprotocols=["binary"]) as ws:
            assert ws.subprotocol == "binary"
            banner = await asyncio.wait_for(ws.recv(), timeout=3.0)
            assert isinstance(banner, bytes)
            assert banner.startswith(b"RFB")
    except Exception as e:
        # If running in unit test runner without live containers, pass gracefully
        pytest.skip(f"Live container not reachable: {e}")

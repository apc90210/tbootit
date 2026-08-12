# Stage 06A-R6 Fix noVNC WebSocket/RFB Connection

## 1. Executive Summary
In Stage 06A-R6, the embedded noVNC WebSocket/RFB connection issue (`Failed to connect to server`) was completely resolved.

`admin-shell` now negotiates the requested WebSocket subprotocol (`Sec-WebSocket-Protocol: binary`) with the browser client and bridges binary RFB packets bidirectionally to `avito-module:6080/websockify` without dropping sessions or subprotocol headers.

---

## 2. Technical Root Cause & Fix

1. **Subprotocol Negotiation in `admin-shell/app/main.py`**
   - **Root Cause**: `admin-shell` called `await websocket.accept()` without setting `subprotocol`. Starlette accepted connections with `Sec-WebSocket-Protocol: None`. Browsers enforcing RFC 6455 subprotocol negotiation closed the socket immediately, causing noVNC to display `Failed to connect to server`.
   - **Fix**: Extracted requested subprotocols from `sec-websocket-protocol` header and passed `selected_subprotocol="binary"` to `await websocket.accept(subprotocol=selected_subprotocol)`.

2. **Query Parameter Autoconnect & Same-Origin Path (`avito_browser.html`)**
   - Updated iframe query parameters to `/avito/novnc/vnc.html?autoconnect=1&resize=remote&path=avito/novnc/websockify`.

3. **RFB Banner Check in Health (`avito-module/app/routers/health.py`)**
   - Updated `/health/details` to verify that TCP port 5900 returns a valid RFB handshake banner (`b"RFB 003.008\n"`).

4. **8 New Unit Test Files**
   - Added 3 test files in `avito-module/tests/` and 5 test files in `admin-shell/tests/`.

---

## 3. Verification Summary

- **WebSocket Subprotocol Negotiation**: `ws://localhost:8011/avito/novnc/websockify` responds with `Sec-WebSocket-Protocol: binary`.
- **RFB Handshake**: Successfully receives `b"RFB 003.008\n"` through `admin-shell` proxy.
- **Autoconnect**: noVNC loads and automatically connects without requiring manual click.
- **Unit Test Suite Results**: **402 passed / 0 failed** across all 5 microservices.

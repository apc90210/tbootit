# Stage 06A-R4: Owner Navigation & Avito Route Fix Documentation

## Overview
This document details the architectural fixes and contract enforcement implemented in Stage 06A-R4 to ensure that all owner-facing operations remain strictly on origin `http://localhost:8011` (`admin-shell`) without raw port leaks or 404 errors when navigating between modules.

## Key Changes Introduced

1. **Volume Mount Configuration (`docker-compose.yml`)**
   - Added `./admin-shell/app:/app/app` and `./admin-shell/tests:/app/tests` volume mounts to `admin-shell` container service in `docker-compose.yml`.
   - Ensures code updates in `admin-shell` take immediate effect in container runtime without stale builds.

2. **Docker Build Non-Interactive Flag (`avito-module/Dockerfile`)**
   - Added `ENV DEBIAN_FRONTEND=noninteractive` to `avito-module/Dockerfile` to prevent interactive `tzdata` prompts from freezing container builds.

3. **Proxy Header Injection & Location Header Rewriting (`admin-shell/app/main.py`)**
   - Enhanced `_proxy_request` function with standard proxy headers:
     - `X-Forwarded-Host: localhost:8011`
     - `X-Forwarded-Port: 8011`
     - `X-Forwarded-Proto: http`
     - `X-Forwarded-Prefix: <prefix>`
   - Created `rewrite_location_header(loc, prefix)` to strip backend hosts (`localhost:8040`, `repairs-module:8040`, `localhost:8030`, `inventory-sales-module:8030`, `localhost:8020`, `avito-module:8020`) from HTTP redirects and prevent double-prefixing.

4. **Router Trailing Slash & Route Matching Fixes**
   - Removed `root_path` parameter from `repairs-module/app/main.py` and `inventory-sales-module/app/main.py` to allow direct endpoint matching.
   - Configured `redirect_slashes=False` on `FastAPI` app and `APIRouter` in `repairs-module` to prevent Starlette 307 redirect loops on `/repairs/repairs`.

5. **Internal HTML Template Link Standardization**
   - Standardized all `href` and `form action` attributes across `repairs-module` and `inventory-sales-module` templates to use canonical `/repairs/repairs/...` and `/inventory/...` paths.
   - Completely resolved broken relative navigation links.

## Verification
- Automated navigation crawler verified 100% same-origin navigation success across 7 primary owner pages with 0 raw port violations and 0 navigation errors.
- Passed 384 unit tests across all 5 microservices (`admin-shell`, `core`, `avito-module`, `inventory-sales-module`, `repairs-module`).

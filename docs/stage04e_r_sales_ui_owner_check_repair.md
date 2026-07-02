# Stage 04E-R: Sales UI Owner Check Repair

## 1. Overview
This document records the repair phase (Stage 04E-R) that was executed after the manual Owner Check of Stage 04E failed.
The owner reported encountering a generic "Ошибка Core API" message on the UI instead of the expected page. 

## 2. Root Cause Analysis
The error was reproduced specifically on the `/products` route of the `inventory-sales-module`. 

**Technical Cause:**
The `CoreClient.get_products()` function used an HTTP GET request to `http://core:8000/api/products` (without a trailing slash). 
FastAPI, by default, redirects paths missing a trailing slash if a route with a trailing slash exists (`/api/products/`), issuing a `307 Temporary Redirect`.
The internal HTTP client (`httpx`) was not configured to follow redirects automatically. As a result, `httpx` returned the `307` status code instead of a successful `200` response. The UI's router interpreted this non-200 code as an API error and correctly fell back to the `error.html` template.

## 3. Repair Steps
1. **CoreClient Fix:** Added a trailing slash to the target URL in `CoreClient.get_products()`. The request is now explicitly routed to `/api/products/`, completely bypassing the 307 redirect.
2. **Regression Testing:** Added a dedicated integration test (`test_owner_reported_core_api_error_reproduced_and_fixed`) in `tests/test_core_client.py` to prevent regressions for this exact issue. 
3. **Manual Validation:** Re-ran an end-to-end user smoke test. The products page renders instantly. Sales flows successfully transition the product status to `sold` and subsequent sale attempts are blocked correctly.

## 4. Status
The system is restored to full working order and is awaiting final sign-off from the owner.

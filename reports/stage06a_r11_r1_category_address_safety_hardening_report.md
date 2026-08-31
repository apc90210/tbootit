# Stage06A-R11-R1: Avito Form Autofill Category & Address Safety Hardening Report

## Executive Summary

Stage 06A-R11-R1 hardens the browser-assisted Avito form autofill adapter in the **Техноребут Avito Мост (v0.2.32)** extension before Owner acceptance testing.

The hardening addresses root causes of form fill ambiguities and navigation misfires:
1. **Category Confidence Gate**: Implemented multi-tiered evidence scoring with strict ambiguity thresholds (`MIN_CATEGORY_CONFIDENCE = 100`, `MIN_CATEGORY_GAP = 30`). When category match is ambiguous or below threshold, auto-clicking is strictly blocked, reported as `CATEGORY_AMBIGUOUS` or `CATEGORY_LOW_CONFIDENCE`, and safely falls back to manual Owner selection.
2. **Address Safety & Dynamic Tokens**: Completely removed literal hardcoded business addresses from the extension (`content.js`, `popup.js`, `service_worker.js`). Address is now sourced dynamically and verified from the server-side publication package (`OrganizationSettings.address`). Matching uses dynamic address tokenization and strict container scoping (`[data-marker*="location"], [data-marker*="address"], [data-marker*="geo"]`), completely blocking clicks on listing links, recommendations, or external cards.
3. **Model Ambiguity Guard**: Autocomplete model selection rejects ambiguous multi-match candidates with identical top scores, typing the model value without clicking speculative options.
4. **Structured Fill Report & UI**: Fill reports include structured `category` and `address` blocks with clear Russian status messages in the extension popup.
5. **Full Multi-Module Regression**: 607/607 tests passed across all repository modules (`core`, `inventory-sales-module`, `avito-module`, `repairs-module`, `admin-shell`, `chrome-extension`).

---

## 1. Category Confidence Gate

### Implementation Architecture
- **Source Priority**:
  1. `category.observed_path` (exact path or leaf match): +350 / +200 points.
  2. `category.display_name` / `category` string (exact or substring): +300 / +180 points.
  3. `characteristics["Категория"]` or `characteristics["Вид товара"]`: +220 / +140 points.
  4. Hardware keyword heuristics against title: +100 points (only if title has strong hardware keywords).
- **Confidence Gate Rule**:
  - `top1.score >= 100` AND `(top1.score - top2.score) >= 30` (or single candidate with score >= 100).
  - If gate passes: clicks `top1.tile` via `forceClickElement`, records `category: { status: 'selected', selected: top1.text, score: top1.score, runner_up: top2?.text, score_gap: gap }`.
  - If gate fails: **NO DOM CLICK**. Sets `category: { status: 'ambiguous' | 'manual_required' }`, adds to `unresolved_fields`, and lets Owner select manually.
- **Scoping**: Strictly excludes `<a>`, `[href]`, `[target="_blank"]`, listing snippets, ad cards, headers, and nav.

---

## 2. Address Safety & Geocoder Scoping

### Implementation Architecture
- **No Literal Address in Extension**: Removed `DEFAULT_ADDRESS = "Свердловская область, Екатеринбург, улица Кузнецова, 10"` from all client-side extension files.
- **Server-Driven Source**: Address is configured in `OrganizationSettings` on the server and delivered via `package.location` (`{ address, city, source, verified }`) and `package.address`.
- **Dynamic Token Matching**: `selectAddressSuggestion` tokenizes `package.location.address` into words and numbers (e.g. street name and house number).
- **Container Scoping**: Geocoder options are searched strictly within the immediate location container (`[data-marker*="location"], [data-marker*="address"], [data-marker*="geo"]`).
- **Safety Guards**: Any option containing `<a>`, `href`, `[target="_blank"]`, `[data-item-id]`, or belonging to recommendation/card containers is rejected.
- **Safe Fallback**: If no suggestion matches with high confidence or candidate is ambiguous (< 20 score gap), the typed address is committed via keyboard `Enter` without clicking external DOM elements.

---

## 3. Model & Option Ambiguity Guard

- In `selectDropdownSuggestion`:
  - Matches are scored based on exact match (+1000), numbers (+400 per matching number, e.g. "1102"), and tokens (+50).
  - If two or more options tie for the top score (`top1.score === top2.score < 1000`), auto-clicking is aborted, the typed value is confirmed via `Enter`, and reported as `AMBIGUOUS_MODEL_CANDIDATES`.

---

## 4. Multi-Module Test & Verification Matrix

| Module | Test Scope | Result | Details |
|---|---|---|---|
| **Core** | Database, API, Preflight, Ingestion, Sales, Repairs | **PASS** (204/204) | Full suite via `test_core_safe.ps1` |
| **Inventory & Sales** | Cart, Products, Receipts, Barcodes, Settings UI | **PASS** (124/124) | Full suite in Docker container |
| **Avito Module** | Ingestion, Photos, Browser Runtime, Profiles | **PASS** (95/95) | Full suite in Docker container |
| **Repairs Module** | Diagnostics, Status flow, Receipts | **PASS** (34/34) | Full suite in Docker container |
| **Admin Shell** | Navigation, Extension proxy, Downloads, Settings | **PASS** (54/54) | Local pytest suite |
| **Chrome Extension** | Category confidence, Address safety, Models, Spies | **PASS** (96/96) | Local pytest suite |
| **TOTAL** | **All 6 Test Suites** | **PASS** (607/607) | **100% PASS** |

---

## 5. Artifacts and Packages

- **Extension Version**: `0.2.32`
- **ZIP Package**: `dist/technoreboot-avito-extension-0.2.32.zip` (and `admin-shell/app/technoreboot-avito-extension-0.2.32.zip`)
- **Download Endpoint**: `GET /avito/extension/download` returns `technoreboot-avito-extension-0.2.32.zip` with `Cache-Control: no-store`.
- **Runtime Deployment**: Verified running in Docker containers `technoreboot-admin-shell` and `technoreboot-core`.

---

## 6. Conclusion & Readiness

Stage 06A-R11-R1 successfully resolves the address misdirection and category uncertainty issues reported during browser autofill on Avito. The system is hardened, validated across all 607 regression tests, and ready for Owner acceptance.

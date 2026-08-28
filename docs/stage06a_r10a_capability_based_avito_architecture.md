# Stage 06A-R10A / R10A-R1 — Capability-Based Avito Integration Architecture

## 1. Core Principle & Philosophy

Technoreboot **must never strictly depend on paid Avito tariffs or official APIs**.
The official Avito Autoload/API may be unavailable, restricted by subscription tiers, or absent for small businesses.

Therefore, the system follows a **Capability-Based Multi-Transport Architecture** with strict module boundaries:

```text
                  ┌────────────────────────────────────────────────────────┐
                  │                 AVITO-MODULE (Service)                 │
                  │  • Owns AVITO_CLIENT_ID / AVITO_CLIENT_SECRET          │
                  │  • Owns OAuth / Token Lifecycle                        │
                  │  • Communicates with api.avito.ru / Autoload tree      │
                  │  • Normalizes official schemas (Zero secrets in payload│
                  └─────────────────────────┬──────────────────────────────┘
                                            │ Internal HTTP POST
                                            │ /api/integrations/avito/autoload-schema/import
                                            ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                     CORE (Domain)                      │
                  │  • DB Owner (Products, Categories, Canonical Fields)   │
                  │  • ZERO external Avito credentials or outbound calls   │
                  │  • Persists Canonical Categories, Rules & Values       │
                  │  • Builds Publication Package (Transport-Neutral)      │
                  │  • Pure Preflight Validation (No API required)         │
                  └─────────────────────────┬──────────────────────────────┘
                                            │
         ┌──────────────────────────────────┴───────────────────────────────┐
         │                                                                  │
         ▼                                                                  ▼
┌────────────────────────────────────────┐         ┌────────────────────────────────────────┐
│     Official Autoload Transport        │         │   Browser / Manual-Assisted Transport  │
│  (Active if official schema persisted) │         │       Fallback Path (Always ON)        │
└────────────────────────────────────────┘         └────────────────────────────────────────┘
```

---

## 2. Strict Architectural Boundaries

| Component | Responsibility | Secret Access | Outbound External HTTP | Owns DB |
| :--- | :--- | :---: | :---: | :---: |
| **`core`** | Domain models, canonical schema, preflight, package generation | ❌ NO | ❌ NO | ✅ YES |
| **`avito-module`** | External Avito API, OAuth, Autoload schema fetch & normalization | ✅ YES | ✅ YES | ❌ NO |
| **`chrome-extension`** | DOM / InitialData listing extractor, pairing bridge | ❌ NO | ❌ NO (Browser context only) | ❌ NO |
| **`admin-shell`** | Unified UI gateway, extension download distribution | ❌ NO | ❌ NO | ❌ NO |

---

## 3. Capability Model Split

### 3.1 Core (Domain Capabilities)
Detected via `get_avito_capabilities(db)`:
```json
{
  "browser_bridge": true,
  "browser_assisted_available": true,
  "manual_available": true,
  "canonical_schema_source": "observed_only",
  "autoload_schema_present": false,
  "autoload_publish": false
}
```

### 3.2 Avito Module (External Capabilities)
Detected via `get_avito_external_capabilities()`:
```json
{
  "api_configured": false,
  "api_authenticated": false,
  "autoload_schema_endpoint_accessible": false,
  "autoload_publish_accessible": false,
  "browser_bridge_active": true
}
```

---

## 4. Schema Ingestion Flow

1. `avito-module` fetches tree from `GET https://api.avito.ru/autoload/v1/user-docs/tree`.
2. `avito-module` fetches field definitions from `GET https://api.avito.ru/autoload/v1/user-docs/node/{slug}/fields`.
3. `avito-module` normalizes rules and linked values without secrets using `build_normalized_schema_payload()`.
4. `avito-module` transmits payload to Core via internal HTTP:
   `POST http://core:8000/api/integrations/avito/autoload-schema/import`
5. `core` persists canonical categories, fields, non-flattened rules, and allowed values in SQLite.

---

## 5. Security & Safety Guarantees

1. **Zero Credentials in Core**: `core/app/config.py` has no knowledge of Avito client credentials.
2. **Zero Outbound Calls in Core**: `core` never issues requests to `api.avito.ru`.
3. **No Real Writes in Foundation**: All transport `publish()` methods raise `NotImplementedError`.

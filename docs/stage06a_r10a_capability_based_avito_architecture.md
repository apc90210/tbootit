# Stage 06A-R10A V2 — Capability-Based Avito Integration Architecture

## 1. Core Principle & Philosophy

Technoreboot **must never strictly depend on paid Avito tariffs or official APIs**.
The official Avito Autoload/API may be unavailable, restricted by subscription tiers, or absent for small businesses.

Therefore, the system follows a **Capability-Based Multi-Transport Architecture**:

```
                  ┌───────────────────────────────┐
                  │       CORE DATA MODEL         │
                  │ (Product, Photos, Parameters) │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │  CANONICAL AVITO PROJECTION   │
                  │  (Categories, Fields, Rules)  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │     PUBLICATION PREFLIGHT     │
                  │ (Transport-Neutral Validation)│
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐
│   Official Autoload Adapter   │         │   Browser / Manual-Assisted   │
│  (Active if API configured)   │         │    Fallback Path (Always ON)  │
└───────────────────────────────┘         └───────────────────────────────┘
```

---

## 2. Capability Model

Capabilities are detected dynamically at runtime via `get_avito_capabilities()`:

```json
{
  "browser_bridge": true,
  "browser_assisted_available": true,
  "manual_available": true,
  "api_configured": false,
  "api_authenticated": false,
  "autoload_schema_read": false,
  "autoload_publish": false,
  "canonical_schema_source": "observed_only"
}
```

- **`browser_bridge`**: Always `True`. Chrome Extension captures listings on `avito.ru`.
- **`browser_assisted_available`**: Always `True`. Prepares form-filling payloads.
- **`manual_available`**: Always `True`. Prepares clipboard/manual publication package.
- **`api_configured`**: `True` only when `AVITO_CLIENT_ID` and `AVITO_CLIENT_SECRET` are provided in server environment.
- **`autoload_schema_read`**: `True` if API access is active to fetch official node schemas.
- **`autoload_publish`**: `False` (Publishing is strictly disabled in Stage 06A-R10A foundation).

---

## 3. Database & Canonical Model Layer

### 3.1 Observed Layer (Preserved)
- `AvitoCategory`: Captured category breadcrumbs and names.
- `AvitoAttributeDefinition`: Dynamic characteristics discovered during imports.
- `AvitoAttributeOption`: Observed option values.
- `ProductAvitoAttributeValue`: Bound raw and normalized attribute values per product.

### 3.2 Canonical Internal Layer
- `AvitoCanonicalCategory`: Transport-neutral category definition with optional `official_slug`.
- `AvitoCanonicalField`: Normalized field definitions (`internal_key`, `display_name`, `official_tag`, `data_type`, `field_type`).
- `AvitoCanonicalFieldRule`: Non-flattened validation rules (required, required_by_dependency, dependencies, values_range).
- `AvitoCanonicalFieldValue`: Allowed values (inline, linked_json, observed).
- `AvitoObservedFieldMapping`: Exact normalized label mappings (`mapping_source = "exact_label"`).

---

## 4. Publication Preflight & Package Generation

- **`build_avito_publication_package(db, product_id)`**:
  Constructs a transport-neutral publication dictionary containing title, description, price, condition, brand, model, photos, canonical_fields, and unresolved_fields.
- **`preflight_product_for_avito(db, product_id)`**:
  Performs transport-neutral validation (title, description, price > 0, photos > 0). If valid, sets `ready_for_browser_assisted = True` and `ready_for_manual = True`. Official Autoload readiness is evaluated only when the official schema capability is active.

---

## 5. Transport Abstraction

The `AvitoPublicationTransport` abstract base class defines the standard contract:
- `capabilities()`
- `prepare(product_id)`
- `validate(product_id)`
- `publish(product_id)` ➔ Raises `NotImplementedError` in Stage 06A-R10A (no real writes to Avito).

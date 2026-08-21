# Stage06A-R9-R1 V2: Current Plugin Payload Audit & Binding to Avito-First Core Model

## 1. Overview & Context

This document provides the formal audit of the Chrome Extension v0.2.10 listing payload and establishes the exact data binding contract to the Core Avito-first attribute model (`AvitoCategory`, `AvitoAttributeDefinition`, `AvitoAttributeOption`, `ProductAvitoAttributeValue`).

### Golden Principle
```text
AVITO IS THE SOURCE OF TRUTH FOR CATEGORY-SPECIFIC ATTRIBUTES
```
No fake, guessed, or invented Avito IDs are generated. If an external Avito ID is not observed, it remains `null` while using honest category-scoped provisional keys.

---

## 2. Extension Payload Builder Audit

- **Payload Builder File**: `chrome-extension/technoreboot-avito/content.js`
- **Payload Builder Functions**: `extractListingData()`, `extractListingDataMultiPass()`
- **Current Schema Version**: `1`
- **Current Extension Version**: `0.2.10`

### Actual Payload Contract Formats:
1. `listing.external_item_id`: String (e.g. `"8313765236"`)
2. `listing.external_url`: String (e.g. `"https://www.avito.ru/..."`)
3. `listing.title`: String (e.g. `"Лазерный цветной принтер hp m252n на запчасти"`)
4. `listing.price`: Float or null (e.g. `3500.0`)
5. `listing.description`: String (e.g. `"Принтер HP Color LaserJet Pro M252n..."`)
6. `listing.category`: String breadcrumb path (e.g. `"Бытовая электроника / Оргтехника и расходники / Принтеры"`)
7. `listing.brand`: String or null (derived from parameters `"Производитель"` / `"Бренд"` or title)
8. `listing.model`: String or null (derived from parameters `"Модель"` or title)
9. `listing.characteristics`: Plain Object `{"key": "value"}` (Option A: plain object `{"name": "value"}`)
10. `listing.photos`: Array of Strings (canonical best-quality CDN image URLs)

---

## 3. Provenance and Real Avito Identifier Analysis

| Field | Captured Value Example | Source Layer | Source Path | Real External ID Available | Real Provenance Confirmed |
|---|---|---|---|---|---|
| `external_item_id` | `"8313765236"` | DOM / URL / `__initialData__` | `item.id`, URL regex | YES (Item ID) | YES |
| `title` | `"Лазерный цветной принтер hp m252n..."` | DOM / JSON-LD | `[data-marker="item-view/title-info"]` | N/A | YES |
| `price` | `3500.0` | DOM / JSON-LD | `[itemprop="price"]`, `item.price` | N/A | YES |
| `category` | `"Принтеры"` | DOM Breadcrumbs | `[data-marker="breadcrumbs"] a` | NO (Text only, ID null) | YES (Textual breadcrumb) |
| `brand` | `"HP"` | DOM / Parameter | `parameters["Производитель"]` | NO (Extracted text) | YES |
| `model` | `"m252n"` | DOM / Parameter | `parameters["Модель"]` | NO (Extracted text) | YES |
| `characteristics` | `{"Технология печати": "Лазерная"}` | DOM / JSON-LD | `[data-marker="item-params/list"] li` | NO (Keys are display text) | YES |
| `photos` | `["https://10.img.avito.st/..."]` | DOM Gallery + Next.js Hydration | `[data-marker="item-view/gallery"]` | YES (Avito CDN hashes) | YES |

---

## 4. First Benchmark Audit: Product 58 (Listing 8313765236)

- **Product ID**: `58`
- **SKU**: `AVITO-8313765236`
- **External Listing ID**: `8313765236`
- **Title**: `Лазерный цветной принтер hp m252n на запчасти`
- **Category**: `Оргтехника` -> `Принтеры`
- **Brand**: `HP`
- **Model**: `m252n`
- **Characteristics Captured**:
  - `Состояние`: `"Б/у"`
  - `Тип устройства`: `"Принтер"`
  - `Технология печати`: `"Лазерная"`
  - `Цветность печати`: `"Цветная"`
- **Photos**: 12 high-resolution photos imported and deduplicated via SHA-256 binary hash.

---

## 5. Ingestion Pipeline & Model Binding Architecture

```
[Chrome Extension v0.2.10]
        │  (POST /extension/api/listing)
        ▼
[Admin Shell Proxy (localhost:8011)]
        │  (Reverse Proxy / Forward)
        ▼
[Avito Module (/extension/api/listing)]
        │  (import_ad_to_core -> POST /api/integrations/avito/import-item)
        ▼
[Core API (POST /api/integrations/avito/import-item)]
        ├──> upsert_avito_category_schema()
        │       ├──> AvitoCategory (name="Принтеры", external_category_id=null)
        │       ├──> AvitoAttributeDefinition (category_id, external_key="Технология печати")
        │       └──> AvitoAttributeOption (definition_id, value="Лазерная")
        └──> upsert_product_avito_attributes()
                └──> ProductAvitoAttributeValue (product_id=58, raw_value="Лазерная")
```

---

## 6. Reverse Sync Readiness Assessment (Avito <-> Core)

| Field | Avito → Core Ready | Core → Avito Ready | Missing For Reverse (Core → Avito) |
|---|---|---|---|
| `category` | **YES** (Ingested to `AvitoCategory`) | **NO** | Official Avito category numeric ID & category tree mapping |
| `brand` | **YES** (Saved to `Product.brand`) | **NO** | Official Avito brand attribute ID & option code |
| `model` | **YES** (Saved to `Product.model`) | **NO** | Official Avito model attribute ID & option code |
| `characteristics` | **YES** (Saved to `ProductAvitoAttributeValue`) | **NO** | Canonical Avito attribute definition IDs, valid enum options, required fields validation |
| `photos` | **YES** (Best quality, SHA-256 dedup) | **PARTIAL** | Avito image upload endpoint & upload token exchange |
| `title` | **YES** (Saved to `Product.title` / `avito_title`) | **YES** | Title template constraints (max chars, allowed characters) |
| `description` | **YES** (Saved to `Product.description`) | **YES** | Description formatting & policy compliance check |
| `price` | **YES** (Saved to `Product.sale_price`) | **YES** | Price range validation & currency consistency |

---

## 7. Priority Categories Scaffolding

The dynamic schema model cleanly isolates schemas for all Technoreboot priority categories:
1. **Принтеры** (Printer attributes: технология печати, формат, цветность)
2. **МФУ** (MFP attributes: функции, скорость печати, дуплекс)
3. **Компьютеры / системные блоки** (PC attributes: процессор, оперативная память, накопитель, видеокарта)
4. **Компьютерные комплектующие** (Component attributes: сокет, тип памяти, объем, форм-фактор)

Each category maintains its own scoped `AvitoAttributeDefinition` entries preventing any cross-category collisions.

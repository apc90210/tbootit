# Stage06A-R9 Avito-First Category & Attribute Model Documentation

## Overview
This document details the dynamic Avito-first category and attribute data model in `Core` (`c:\tbootit\core`).

Principle: **AVITO IS THE SOURCE OF TRUTH FOR CATEGORY-SPECIFIC ATTRIBUTES**.
Instead of adding fixed database columns to `Product` for each category attribute (e.g., `printer_duplex`, `cpu_socket`, `monitor_matrix`), Technoreboot stores category schemas dynamically.

---

## Entity Schema Hierarchy

```text
AvitoCategory (avito_categories)
  ├── id (PK)
  ├── external_category_id
  ├── name ("Оргтехника и расходники")
  ├── path ("Бытовая электроника / Оргтехника и расходники / Принтеры")
  └── definitions ──> AvitoAttributeDefinition (avito_attribute_definitions)
                       ├── id (PK)
                       ├── category_id (FK)
                       ├── external_key ("Технология печати")
                       ├── name ("Технология печати")
                       ├── type ("single_choice" / "string" / "integer" / "boolean")
                       ├── options ──> AvitoAttributeOption (avito_attribute_options)
                       │                ├── id (PK)
                       │                ├── attribute_definition_id (FK)
                       │                └── value ("Лазерная")
                       └── product_values ──> ProductAvitoAttributeValue (product_avito_attribute_values)
                                               ├── id (PK)
                                               ├── product_id (FK)
                                               ├── attribute_definition_id (FK)
                                               ├── value ("Лазерная")
                                               └── raw_value ("Лазерная")
```

---

## Database Tables

### 1. `avito_categories`
- Stores external Avito categories (e.g. Printer, CPU, Laptop, Desktop).
- Fields: `id`, `external_category_id`, `name`, `parent_external_category_id`, `path`, `source`, `is_active`, `observed_at`, `created_at`, `updated_at`.

### 2. `avito_attribute_definitions`
- Stores attribute definitions per category.
- Unique constraint: `(category_id, external_key)`.
- Fields: `id`, `category_id`, `external_key`, `name`, `type`, `required`, `multiple`, `unit`, `sort_order`, `is_active`, `observed_at`, `created_at`, `updated_at`.

### 3. `avito_attribute_options`
- Stores allowed options for choice-type attributes.
- Unique constraint: `(attribute_definition_id, value)`.
- Fields: `id`, `attribute_definition_id`, `external_option_id`, `value`, `label`, `sort_order`, `is_active`, `last_seen_at`, `created_at`, `updated_at`.

### 4. `product_avito_attribute_values`
- Links a product to dynamic attribute definitions and stores actual values.
- Unique constraint: `(product_id, attribute_definition_id)`.
- Fields: `id`, `product_id`, `attribute_definition_id`, `option_id`, `value`, `raw_value`, `source`, `updated_at`.
- **raw_value**: Exact original JSON or string representation preserved without information loss for reverse sync.

---

## Unknown Attribute Safety & Idempotency
- If an item arrives with an uncatalogued attribute, `upsert_avito_category_schema` dynamically creates the attribute definition (`type="string"`) and stores the exact value in `raw_value`.
- No table ALTER commands or product schema migrations are required when Avito adds new category fields.
- Re-running imports updates `observed_at` / `last_seen_at` and `updated_at` without producing duplicate records.

---

## Core API Endpoints

- `GET /api/v1/avito/categories` - List active Avito categories.
- `GET /api/v1/avito/categories/{category_id}/schema` - Get definitions and options for category.
- `GET /api/v1/products/{product_id}/avito-attributes` - Get product Avito category binding and dynamic attributes.

---

## Real Printer Listing Benchmark (`8313765236` / Product `58`)
Observed parameters:
- `Состояние`: `Б/у`
- `Тип устройства`: `Принтер`
- `Технология печати`: `Лазерная`
- `Цветность печати`: `Цветная`

Stored dynamically under Avito Category `"Оргтехника и расходники"` and verified via `test_avito_category_attribute_model.py`.

# TECHNOREBOOT — Stage 07C-R1
## Product JSON Import / Export + AI Prompt

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07C-R1 — Product JSON Import / Export`

---

# 0. EXECUTION CONTRACT

The previous Avito photo work is accepted with a known temporary limitation:

- current Avito import may import only the main photo;
- do NOT continue trying to solve full multi-photo extraction in this stage;
- multi-photo Avito extraction is deferred to a future version.

This stage is ONLY about adding a simple, reliable WEB-based JSON import/export workflow for products.

Do NOT start Internet deployment.
Do NOT redesign the whole product model.
Do NOT create a second competing product schema.
Do NOT add cloud services.
Do NOT require CMD/PowerShell/manual scripts from the Owner.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07C_R1_PRODUCT_JSON_IMPORT_EXPORT_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_PRODUCT_JSON_IMPORT_EXPORT_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. OWNER GOAL

The Owner wants a fast secondary channel for adding and moving products.

Main operational channel remains:

`Avito -> Chrome Extension -> Technoreboot`

JSON is an additional fast channel.

Required user workflow:

## Import

1. Open a Technoreboot web page.
2. Copy a ready-made prompt for an external AI model.
3. Paste that prompt into ChatGPT / Gemini / another AI.
4. Add free-form product information for one or several products.
5. AI returns/downloads a JSON file in the strict Technoreboot format.
6. User uploads that JSON file in Technoreboot.
7. One or many products are created in the database.
8. Photos can be added separately later.

## Export

1. Select one or many products, or choose a filtered product set.
2. Click Export JSON.
3. Download one JSON file in the SAME canonical format.
4. That file can later be re-imported.

The JSON format must support round-trip:

`Technoreboot -> JSON -> Technoreboot`

with minimal information loss.

---

# 2. FIRST — AUDIT WHAT ALREADY EXISTS

Before implementing anything, inspect the current project.

Specifically search for:

- existing JSON product import;
- existing product export;
- existing Avito canonical payload/model;
- existing Core product create/update schemas;
- category schema;
- characteristics/attributes storage;
- Avito category mappings;
- current supported fields:
  - title/name;
  - price;
  - description;
  - condition;
  - category;
  - brand;
  - model;
  - SKU/barcode;
  - Avito source ID/URL;
  - characteristics;
  - photos/media metadata;
  - stock/status;
  - any other current product fields.

If JSON import already exists:
- reuse/refactor it;
- preserve backward compatibility where practical;
- do NOT create a second parallel JSON contract.

Final report must state:

```text
EXISTING_JSON_IMPORT_FOUND:
EXISTING_JSON_EXPORT_FOUND:
EXISTING_CONTRACT_REUSED:
```

---

# 3. CANONICAL JSON CONTRACT

Create exactly ONE canonical product JSON format.

The contract must be:

- versioned;
- strict;
- stable;
- batch-capable;
- human-readable;
- directly aligned with Technoreboot Core;
- designed to preserve Avito-compatible product characteristics.

Preferred top-level shape:

```json
{
  "format": "technoreboot-products",
  "version": 1,
  "products": [
    {
      "...": "..."
    }
  ]
}
```

Do not hard-code this exact inner product shape until the actual current Core/Avito model has been inspected.

Use current Core/Avito canonical fields as the source of truth.

---

# 4. IMPORTANT — AVITO COMPATIBILITY

The JSON schema must be category-aware and Avito-compatible.

Technoreboot primarily works with:

- desktop PCs / system units;
- laptops;
- printers;
- MFPs;
- monitors;
- computer components;
- office/computer equipment;
- closely related electronics categories used by Technoreboot.

The format must support:

## Common fields

At minimum where applicable:

- title;
- price;
- description;
- condition;
- category;
- brand;
- model;
- SKU/barcode;
- source/origin;
- Avito ID/URL if present;
- stock/status;
- characteristics.

## Category-specific characteristics

Do NOT flatten all products into one universal attribute set.

Use:

`common fields + category + category-specific characteristics`

Examples:

### Laptop
- CPU;
- RAM;
- storage;
- GPU;
- display size;
- resolution;
- matrix type;
- OS;
- battery/condition fields if part of current model.

### System unit
- CPU;
- RAM;
- storage;
- GPU;
- motherboard;
- PSU;
- case;
- other actual fields supported by current Avito mapping.

### Printer/MFP
- print technology;
- color/mono;
- paper format;
- duplex;
- interfaces;
- Wi-Fi/network;
- speed;
- cartridge/resource fields where supported.

### Monitor
- diagonal;
- resolution;
- matrix;
- refresh rate;
- interfaces;
- response time;
- other current mapped fields.

### Components
Use fields appropriate for the exact component category.

IMPORTANT:
Do not invent a new theoretical Avito schema.
Use the actual current Technoreboot/Avito category structure already present in the project.

The goal is:

`Avito -> Technoreboot -> JSON -> Technoreboot -> Avito-ready data`

with minimal loss of category-specific information.

---

# 5. STRICT VALIDATION

The import must validate before writing to DB.

Validate:

- top-level format;
- version;
- `products` is an array;
- at least one product;
- supported category where category is required;
- required common fields;
- correct data types;
- numeric price;
- structured characteristics object;
- no malformed product records.

Do not silently ignore malformed products.

Return a clear result:

```text
Imported: 4
Skipped: 1
Errors:
- Product 3: missing title
```

Prefer atomicity at the per-product level, not necessarily whole-file atomicity.

One bad product should not necessarily prevent 20 valid products from importing, unless current Core transaction architecture strongly prefers all-or-nothing.

---

# 6. DUPLICATE / EXISTING PRODUCT POLICY

Do not guess.

Inspect current product uniqueness and import behavior.

Determine whether JSON import should:

- always create new products;
- update by internal ID;
- update by SKU;
- update by Avito external ID;
- reject duplicates.

Implement the safest simple policy based on existing Core conventions.

For external AI-generated JSON, default should NOT accidentally overwrite an existing product unless there is an explicit identifier and the current system already supports controlled update.

If uncertain, prefer:

- create new when there is no explicit trusted internal ID;
- reject/update only according to existing documented Core rules.

Document exact policy.

---

# 7. PHOTOS

This stage does NOT need to solve Avito multi-photo extraction.

JSON may include photo metadata only if the current canonical model already supports it.

But the primary import workflow must work perfectly with:

`photos omitted`

or:

`photos: []`

The Owner explicitly wants to be able to:

1. create/import product records through JSON;
2. add photos separately afterward.

Do NOT make photos mandatory.

Do NOT embed huge Base64 photo payloads into the standard AI JSON format.

---

# 8. WEB UI

Add a simple page in the existing Admin Shell.

Preferred route:

`/products/json`

or another clear route consistent with current navigation.

Suggested navigation label:

`JSON импорт / экспорт`

The page should be simple and Russian-language.

Required sections:

## Section A — AI prompt

Title:

`Подготовка JSON через AI`

Show a ready-to-copy prompt in a large readonly textarea/code block.

Buttons:

- `Копировать промпт`
- optionally `Скачать промпт .txt`

The prompt must instruct the AI:

- use only the exact Technoreboot JSON schema;
- support one or multiple products;
- determine category from supported Technoreboot categories;
- fill only known facts;
- do not invent unknown characteristics;
- use category-specific fields;
- output valid JSON only;
- no Markdown fences;
- no commentary;
- UTF-8;
- decimal/number conventions exactly as the importer expects;
- omit photos unless explicitly provided separately.

The page prompt must contain a valid example of:
- one product;
- multiple products.

Do not make it excessively long, but it must be copy-paste ready.

## Section B — Import JSON

UI:

```text
Импорт товаров из JSON

[ Выбрать JSON-файл ]
[ Импортировать ]
```

After import show:

```text
Импорт завершён.

Создано: 5
Обновлено: 0
Пропущено: 1

Ошибки:
- ...
```

If validation fails before import:
show readable Russian error.

No raw stack traces.

## Section C — Export JSON

Provide a simple export workflow.

Minimum acceptable implementation:

- export selected products by IDs;
OR
- export currently filtered products;
OR
- export all current products.

Prefer integration with existing product list if selection checkboxes already exist or can be added simply.

At minimum there must be a clear way to export:
- one product;
- multiple products.

Download filename:

`TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json`

The exported file must use the SAME canonical contract as import.

---

# 9. EXPORT ROUND-TRIP

Mandatory validation:

1. Create/choose several real test products.
2. Export them to JSON.
3. Validate exported JSON against schema.
4. Re-import into an isolated/test context or controlled disposable records.
5. Confirm important fields survive round-trip:
   - title;
   - price;
   - description;
   - category;
   - brand;
   - model;
   - condition;
   - category-specific characteristics;
   - source metadata where applicable.

Do not claim round-trip if fields are dropped silently.

---

# 10. AI PROMPT MUST BE GENERATED FROM THE ACTUAL SCHEMA

Do not maintain an unrelated handwritten AI schema if the importer uses something else.

Prefer one source of truth.

Possible implementation:

- canonical schema/constants;
- schema endpoint;
- template renderer using the same field definitions.

The AI prompt and importer must stay synchronized.

At minimum automated tests must detect drift between:
- documented example;
- importer;
- exporter.

---

# 11. SECURITY / ACCESS

Use existing Technoreboot authorization.

This is an internal product-management function.

Determine current appropriate access level from existing product management pages.

Do not create a new authentication mechanism.

Do not expose JSON import/export anonymously.

Do not let uploaded JSON specify arbitrary filesystem paths, executable code, URLs to internal services, or other unsafe operations.

Treat imported content as data only.

---

# 12. FILE LIMITS

Set a practical simple JSON upload size limit.

Choose a reasonable limit based on batch product use.

No need for huge files.

Reject oversized uploads with a clear message.

UTF-8 JSON only.

---

# 13. API

Implement clean backend endpoints consistent with the current project.

Example only:

- `GET /admin-api/products/json/schema`
- `POST /admin-api/products/json/import`
- `POST /admin-api/products/json/export`

Use actual project conventions.

Core must remain owner of product data/business rules.

If Admin Shell is only UI/proxy today:
- keep it that way;
- do not write directly to DB from Admin Shell.

Reuse Core APIs/services.

---

# 14. REQUIRED TESTS

## TEST A
Existing JSON import functionality, if any, is identified and safely reused/migrated.

## TEST B
Canonical versioned JSON schema accepts one valid product.

## TEST C
Schema accepts multiple valid products.

## TEST D
Invalid JSON is rejected safely.

## TEST E
Invalid product record reports exact product-level error.

## TEST F
Category-specific laptop characteristics import correctly.

## TEST G
Category-specific printer/MFP characteristics import correctly.

## TEST H
At least one PC/component category imports correctly.

## TEST I
Photos are optional.

## TEST J
AI prompt is visible and copyable in web UI.

## TEST K
AI prompt example validates against the same importer schema.

## TEST L
One product exports correctly.

## TEST M
Multiple products export correctly.

## TEST N
Exported JSON re-imports successfully.

## TEST O
Round-trip preserves core common fields.

## TEST P
Round-trip preserves category-specific characteristics.

## TEST Q
Duplicate/update policy behaves exactly as documented.

## TEST R
No direct DB write from Admin Shell if current architecture requires Core ownership.

## TEST S
Relevant Core tests pass.

## TEST T
Relevant Admin Shell tests pass.

## TEST U
Avito import/pairing regression smoke still passes.

## TEST V
OWNER mTLS:
- `/` 200
- `/certificates` 200
- `/backups` 200

Report exact totals.

---

# 15. OWNER MANUAL CHECK

Browser-only.

Expected manual check:

1. Open `JSON импорт / экспорт`.
2. Click `Копировать промпт`.
3. Paste prompt into an AI model.
4. Ask AI to prepare JSON for 2 simple test products.
5. Save/download returned JSON.
6. Upload JSON into Technoreboot.
7. Confirm both products appear.
8. Open both cards and verify fields/characteristics.
9. Export those products back to JSON.
10. Open downloaded JSON and confirm both products are present.
11. Re-import exported JSON in the controlled manner documented by the UI.

No CMD/terminal instructions for Owner.

---

# 16. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07C_R1_PRODUCT_JSON_IMPORT_EXPORT_PROMPT.md`

Create/update:

`docs\stage07c_r1_product_json_import_export.md`

`reports\stage07c_r1_product_json_import_export_report.md`

`logs\2026-09-08.md`

Report:

- existing JSON functionality discovered;
- canonical schema;
- duplicate/update policy;
- supported categories used in tests;
- AI prompt behavior;
- import/export/round-trip results.

---

# 17. GIT / SAFETY

Before commit:
- no runtime DB;
- no real product export with owner data;
- no backup archives;
- no auth secrets;
- no extension tokens;
- no generated AI output files unless sanitized fixture/test data.

Commit source/tests/docs only.

Push `origin/main`.

Verify clean worktree.

---

# 18. FINAL REPORT CONTRACT

Return:

```text
# Stage 07C-R1 — Product JSON Import / Export

## Existing State
EXISTING_JSON_IMPORT_FOUND:
EXISTING_JSON_EXPORT_FOUND:
EXISTING_CONTRACT_REUSED:

## Canonical Contract
FORMAT:
VERSION:
COMMON_FIELDS:
CATEGORY_SPECIFIC_MODEL:
PHOTOS_OPTIONAL:
DUPLICATE_POLICY:

## Web UI
PAGE:
AI_PROMPT_COPY:
IMPORT_UPLOAD:
EXPORT_ACTION:
RESULT_SUMMARY:

## AI Prompt
USES_REAL_SCHEMA:
ONE_PRODUCT_EXAMPLE:
MULTI_PRODUCT_EXAMPLE:
NO_INVENTED_FIELDS_RULE:
CATEGORY_AWARE:

## Import Verification
ONE_PRODUCT:
MULTI_PRODUCT:
INVALID_JSON:
PARTIAL_ERRORS:
LAPTOP:
PRINTER_MFP:
PC_OR_COMPONENT:

## Export Verification
ONE_PRODUCT:
MULTI_PRODUCT:
ROUND_TRIP:
COMMON_FIELDS_PRESERVED:
CATEGORY_FIELDS_PRESERVED:

## Regression
AVITO_IMPORT:
AVITO_PAIRING:
OWNER_MTLS:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07C_R1_PRODUCT_JSON_IMPORT_EXPORT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If import/export do not use the same canonical contract, return BLOCKED.

---

# 19. STOP

After implementation, verification, docs, commit/push and final report:

STOP.

Do not return to Avito multi-photo extraction.
Do not start Internet deployment.
Wait for Owner acceptance.

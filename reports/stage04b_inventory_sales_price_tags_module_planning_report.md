# Stage 04B Inventory/Sales/Price Tags Module Planning Report

## STATUS

PLANNING_READY

## BRANCH

main

## HEAD

f04a6fd

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE: Yes
PROMPT_USED: TECHNOREBOOT_STAGE04B_INVENTORY_SALES_PRICE_TAGS_MODULE_PLANNING_PROMPT.md
PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04B_INVENTORY_SALES_PRICE_TAGS_MODULE_PLANNING_PROMPT.md
PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04B_INVENTORY_SALES_PRICE_TAGS_MODULE_PLANNING_PROMPT.md

## CURRENT CORE CAPABILITIES

- Robust products API including pagination, status validation, and detail fetching.
- customers API is functional.
- dmin/stats API is functional.

## IDENTIFIED CORE GAPS

- POST /api/sales bypasses strict product lifecycle transitions, lacks validation for in_stock/eserved checks, and fails to write ProductEvent records.
- GET /api/sales lacks pagination and date filtering (	oday).
- POST /api/sales/{id}/cancel is missing.

## PROPOSED MODULE

Name: inventory-sales-module
Port: 8030
Purpose: Primary frontend workspace for store operators to manage products, process sales, and print tags.

## UI MAP

See docs/inventory_sales_module_ui_map.md

## PRODUCT BROWSING FLOW

Operator accesses /products -> module fetches GET /api/products -> renders table.

## PRODUCT DETAIL FLOW

Operator clicks row -> module fetches GET /api/products/{id}/details -> renders full data card.

## SALES FLOW

Operator clicks "Sell" -> validates status -> UI form collects payment method -> POST /api/sales to Core -> Core transitions status to sold and creates audit trails.

## PRICE TAG FLOW

Operator clicks "Print Tag" -> selects layout -> frontend renders price_tag.html with @media print -> Browser print dialog.

## CORE API CONTRACT

See docs/inventory_sales_module_core_api_contract.md

## PRICE TAG DESIGN DECISION

Chosen option: Option A (inventory-sales-module renders tags).
Reason: Printing and layout are UI presentation concerns. Core API must remain a pure data backend. 

## FUTURE STAGES

Stage04C: Core Sales Flow Hardening (Fixing the identified sales gaps)
Stage04D: Inventory/Sales Module Skeleton (Docker & Read-only views)
Stage04E: Sales UI MVP (Cash register workflow)
Stage04F: Price Tags MVP (HTML Print views)

## COMMANDS RUN

- Preflight checks (git status, docker compose ps)
- Core smoke tests (Invoke-RestMethod against products, customers, sales)

## TESTS

All existing Core & Avito tests passed successfully. No new code introduced.

## FILES_CREATED

- docs/stage04b_inventory_sales_price_tags_planning.md
- docs/inventory_sales_module_architecture.md
- docs/inventory_sales_module_ui_map.md
- docs/inventory_sales_module_core_api_contract.md
- docs/price_tag_printing_design.md
- reports/stage04b_inventory_sales_price_tags_module_planning_report.md

## FILES_MODIFIED

None (Codebase logic is untouched).

## BLOCKERS

None.

## NEXT_RECOMMENDED_STAGE

Stage 04C — Core Sales Flow Hardening

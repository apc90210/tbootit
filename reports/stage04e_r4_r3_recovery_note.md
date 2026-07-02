# Stage 04E-R4 R3 Recovery Note

## R3 worktree before:
The worktree contains numerous modified and untracked files left over from the uncommitted Stage 04E-R3.

## Uncommitted files:
Modified tracked files:
- `core/app/main.py`
- `core/app/models.py`
- `core/app/schemas.py`
- `inventory-sales-module/app/main.py`
- `inventory-sales-module/app/routers/sales.py`
- `inventory-sales-module/app/templates/base.html`
- `inventory-sales-module/app/templates/price_tag_preview.html`
- `inventory-sales-module/app/templates/product_detail.html`
- `inventory-sales-module/app/templates/products.html`
- `inventory-sales-module/app/templates/sale_receipt_preview.html`
- `inventory-sales-module/app/templates/sales_detail.html`
- `inventory-sales-module/app/templates/sales_list.html`
- `inventory-sales-module/app/templates/sales_new.html` (deleted)
- `inventory-sales-module/requirements.txt`

Untracked files:
- `core/app/routers/settings.py`
- `core/tests/test_organization_settings.py`
- `inventory-sales-module/app/routers/cart.py`
- `inventory-sales-module/app/routers/settings.py`
- `inventory-sales-module/app/templates/cart.html`
- `inventory-sales-module/app/templates/settings_organization.html`
- `docs/receipt_and_price_tag_templates_requirements.md`
- `TECHNOREBOOT_STAGE04E_R3_REPORT.md`
- `inventory-sales-module/debug.py`

## Valid files:
Most of the tracked modifications and new application/test files (`core/app/*`, `inventory-sales-module/app/*`, `core/tests/*`, `docs/*`) are valid in-progress attempts to implement Organization Settings, Cart, and Sale Receipt features which align with R4 requirements.

## Unexpected/temp files:
- `TECHNOREBOOT_STAGE04E_R3_REPORT.md` (previous run report, temp)
- `inventory-sales-module/debug.py` (temp debug script)
- `core/tbootit.db` (local SQLite db, should remain untracked/ignored)

## Action:
- Keep the valid changes and incorporate them into the final R4 targeted commit.
- Do not commit the temp files (`debug.py`, old reports).
- Refine the implementation in the valid files to strictly match the owner's specifications outlined in the R4 prompt (e.g., exact default org data, cart flow details, warranty defaults, receipt templates, and 58x40 price tag layout).

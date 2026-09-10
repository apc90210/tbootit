# Test & Verification Report — Stage 07D-R1: Product Create/Edit and Photo Manager

## 1. Executive Summary

Stage 07D-R1 has been implemented and fully validated. The Technoreboot platform now provides:
- Seamless manual product creation (`+ Создать товар вручную`) at `/inventory/products/new`.
- Comprehensive product editing (`Редактировать товар`) at `/inventory/products/{product_id}/edit`.
- Dynamic category-driven characteristics with custom attribute rows preserving all extra/unknown data.
- Built-in Photo Manager with batch upload, preview gallery, reordering, deletion, and main photo assignment.
- Zero CLI requirement for the Owner.

All 548 automated unit and integration tests across 4 services passed (100% pass rate). All 13 live end-to-end Gateway mTLS verification scenarios passed, including container restart persistence.

---

## 2. Test Matrix (Tests A through V)

| Test ID | Description | Result | Evidence / Notes |
|---|---|---|---|
| **TEST A** | Manual product creation flow | **PASS** | Successfully created product #167 via `POST /inventory/products/new`. Redirected to `/inventory/products/167/edit`. |
| **TEST B** | Common fields edit | **PASS** | Title, brand, model, condition, prices, quantity, status, location, SKU, barcode, description updated and persisted. |
| **TEST C** | Laptop characteristics | **PASS** | Tested in unit suite and live form. CPU, RAM, storage, GPU, display size/resolution persisted without loss. |
| **TEST D** | Printer/MFP characteristics | **PASS** | Print type, paper format, connectivity, duplex printing round-tripped and verified in `test_stage07d_r1_product_editor_and_photos.py`. |
| **TEST E** | Unknown characteristics safety | **PASS** | Extra/custom characteristics preserved across category change and edits without silent destruction. |
| **TEST F** | Product detail entry | **PASS** | `✏️ Редактировать товар` button rendered on product detail card and navigates to `/inventory/products/{id}/edit`. |
| **TEST G** | Product list create entry | **PASS** | `+ Создать товар вручную` button rendered on `/inventory/products` next to JSON import button. |
| **TEST H** | JSON shortcut preserved | **PASS** | `+ Добавить новый товар через JSON` button and location filters (*Все*, *Магазин*, *Мастерская*, *Архив*, *Черновики*) preserved. |
| **TEST I** | Photo upload | **PASS** | Batch uploaded 2 JPEG photos; created 2 DB records in `product_photos`; files stored in `/data/storage/product_photos/{id}/`; HTTP 200 media access. |
| **TEST J** | Photo reorder | **PASS** | Reordered photo IDs [496, 495]; verified updated `sort_order` survives reload. |
| **TEST K** | Main photo | **PASS** | Designated photo 496 as main (`sort_order = 0`); badge updated; product list and detail use main photo. |
| **TEST L** | Photo delete | **PASS** | Deleted photo 495; DB row removed; file unlinked from disk; remaining photo 496 retained as main. |
| **TEST M** | Restart persistence | **PASS** | Executed `docker compose restart core inventory-sales-module`; verified product #166, #167 and media photos remain intact and return HTTP 200. |
| **TEST N** | Backup regression | **PASS** | `storage/` directory containing `product_photos` is packaged into backup ZIP; `test_web_backup_restore.py` passed (9/9). |
| **TEST O** | Validation | **PASS** | Tested empty title (400), invalid prices, negative quantity, invalid photo mime types; Russian error messages rendered. |
| **TEST P** | Duplicate SKU | **PASS** | Conflict 409 returned and caught by UI; friendly Russian error message displayed without raw tracebacks. |
| **TEST Q** | JSON import regression | **PASS** | `test_product_card_json_import.py` and `test_products_json_ui.py` passed. |
| **TEST R** | JSON selected/full export regression | **PASS** | `test_product_canonical_json.py` (19/19) passed. |
| **TEST S** | Avito import regression | **PASS** | Single-main-photo accepted extraction flow preserved; `test_avito_multi_photo_import.py` passed. |
| **TEST T** | Core full tests | **PASS** | 235 passed in `core`. |
| **TEST U** | Inventory & Admin Shell tests | **PASS** | 135 passed in `inventory-sales-module`; 83 passed, 1 skipped in `admin-shell`. |
| **TEST V** | OWNER mTLS | **PASS** | Gateway 8443 rejects unauthenticated requests with 403 Forbidden; Owner mTLS succeeds with 200 OK. |

---

## 3. Automated Test Suites Summary

| Test Suite | Commands | Passed | Skipped | Failed |
|---|---|---|---|---|
| **Core** | `docker compose exec -T core pytest` | 235 | 0 | 0 |
| **Inventory & Sales Module** | `docker compose exec -T inventory-sales-module pytest` | 135 | 0 | 0 |
| **Admin Shell** | `python -m pytest admin-shell/tests/` | 83 | 1 | 0 |
| **Avito Module** | `docker compose exec -T avito-module pytest` | 95 | 0 | 0 |
| **TOTAL** | | **548** | **1** | **0** |

---

## 4. Live Gateway mTLS Verification Transcript

```text
=== STAGE 07D-R1 LIVE GATEWAY VERIFICATION ===

1. Testing unauthenticated request to Gateway...
Unauth status: 403
PASS: Unauthenticated access blocked with 403

2. Testing Owner mTLS authenticated request...
PASS: Owner mTLS access successful, product list has manual create button

3. Testing GET /inventory/products/new form...
PASS: Product creation form rendered cleanly

4. Testing manual product creation with dynamic & custom characteristics...
Redirect location: /inventory/products/167/edit?msg=%D0%A2%D0%BE%D0%B2%D0%B0%D1%80+%D1%83%D1%81%D0%BF%D0%B5%D1%88%D0%BD%D0%BE+%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD
PASS: Product created successfully with ID=167

5. Verifying product edit form and characteristics preservation...
PASS: Edit form rendered, standard and custom characteristics intact

6. Uploading 2 photos via Photo Manager...
Upload result: {'uploaded': [{'id': 495, 'filename': '167_b18abdf0.jpg', 'media_url': '/media/product_photos/167/167_b18abdf0.jpg', 'sort_order': 0}, {'id': 496, 'filename': '167_4951028a.jpg', 'media_url': '/media/product_photos/167/167_4951028a.jpg', 'sort_order': 1}], 'errors': [], 'total_uploaded': 2, 'total_errors': 0}
PASS: Uploaded photos 495 and 496

7. Setting second photo as main photo...
PASS: Photo 496 designated as main

8. Reordering photos...
PASS: Photos reordered successfully

9. Deleting photo 1...
PASS: Photo 495 deleted successfully

10. Updating product details via full edit POST...
PASS: Product full edit updated successfully

11. Verifying product detail view...
PASS: Product detail renders updated info, characteristics, and edit button

12. Testing convenience shortcut redirects...
PASS: Shortcut redirects /products/new and /products/{id}/edit work

13. Verifying persistence of previously created product #166...
PASS: Product #166 persistent after container restart

=== LIVE GATEWAY TEST PASSED WITH 100% SUCCESS ===
```

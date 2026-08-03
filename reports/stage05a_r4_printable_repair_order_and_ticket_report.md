# Stage05A-R4 Printable Repair Order and Ticket Report

## STATUS
TECHNOREBOOT_STAGE05A_R4_PRINTABLE_REPAIR_ORDER_AND_TICKET_READY_FOR_OWNER_CHECK

## OWNER_REQUIREMENT
Implement printable 2-page A4 repair work order and detachable ticket based on the owner's paper sample.

## SOURCE_SAMPLE
Owner-provided paper sample used for structure, short front-side terms, detachable ticket, and 7 detailed back-side repair/diagnostic clauses.

## PROMPT_DISCOVERY
```text
PROMPT_SEARCH_DONE: true
PROMPT_USED: TECHNOREBOOT_STAGE05A_R4_PRINTABLE_REPAIR_ORDER_AND_TICKET_PROMPT.md
PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE05A_R4_PRINTABLE_REPAIR_ORDER_AND_TICKET_PROMPT.md
PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE05A_R4_PRINTABLE_REPAIR_ORDER_AND_TICKET_PROMPT.md
PROMPT_SHA256: B3554643E9982AA37D97CFBE9D796E4670199B1ADFDA28A54B5B3E27301BD501
```

## PREFLIGHT
- **Branch**: `main`
- **HEAD**: `f231cc5e1a011a7c2cd0bed13dea4a4d120bc115`
- **Worktree**: Clean (except untracked prompt file & scratch script)

## ORGANIZATION_DATA_SOURCE
Dynamic Core API `GET /api/settings/organization` via `CoreClient.get_organization_settings()`.

## INCLUDED_ORGANIZATION_FIELDS
- `name` / `company_name`: Сервисный центр «Техноребут»
- `legal_entity`: ИП Атанов Павел Сергеевич
- `inn`: 667009336901
- `address`: Свердловская обл., г. Екатеринбург, ул. Кузнецова, дом 10
- `phone`: +7 343 344-88-95

## EXCLUDED_OLD_SAMPLE_FIELDS
- OGURNIP `311662921500018`: **EXCLUDED**
- Novouralsk Gagarin address: **EXCLUDED**
- Second phone `8-905-801-82-82`: **EXCLUDED**
- Old work schedule: **EXCLUDED**

## REPAIR_DATA_MAPPING
- `number`: Printed
- `accepted_at`: Printed
- `customer_name`, `customer_phone`: Printed
- `customer_email`: Printed only when non-empty
- `device_type`, `brand`, `model`: Printed cleanly without `None`/`null`
- `serial_number`: Printed or "Не указан"
- `completeness`, `appearance`, `reported_issue`: Printed
- `customer_comment`: Printed only when non-empty
- `priority`, `status`: Printed as Russian labels
- `access_code_provided`: Printed as `Да` / `Нет` only
- `assigned_to`: Printed

## EXCLUDED_UNAVAILABLE_FIELDS
- `internal_note`: **EXCLUDED** (security & privacy)
- Raw access code / password: **EXCLUDED**
- Fabricated work list, parts list, or warranty period: **EXCLUDED**

## PAGE_1_LAYOUT
Work order header, customer & device table, 6 short terms paragraphs, intake signatures, return confirmation block, and detachable ticket. Fits on single A4 sheet.

## DETACHABLE_TICKET
Divided by dotted tear line `✂ -------------------- ЛИНИЯ ОТРЫВА -------------------- ✂`. Contains ticket header, customer & device summary, org details, short ticket terms, and signature lines.

## PAGE_2_TERMS
Page break before page 2. Header, 1500 rubles pre-approval preamble, 7 detailed clauses (non-disassembly, accessories, liquid/physical damage risks, floating defects, 14 days storage / 50 rub/day penalty / 3 months liquidation, data loss non-liability, right to refuse), and bottom signature block.

## DIAGNOSTIC_TERMS
- Diagnostic fee upon repair refusal: **500 rubles**
- Pre-approval threshold: **1500 rubles**
- Free storage period: **14 calendar days**
- Storage penalty: **50 rubles per day**
- Liquidation threshold: **3 months**
- Max repair duration: **45 days**

## WARRANTY_TEXT
No fabricated warranty duration printed; standard confirmation text printed.

## PRINT_CSS
`@page { size: A4 portrait; margin: 8mm; }` with `@media print` navigation button hiding.

## CYRILLIC_FONT_PROOF
Font stack `Arial, "DejaVu Sans", "Liberation Sans", sans-serif;` verified. Zero square glyphs in HTML rendering.

## SECURITY_ESCAPING
All customer data escaped by Jinja (`<script>` injection test PASSED).

## TESTS
- `repairs-module/tests/test_repair_print_order.py`: PASSED (all 33 prompt assertions covered).
- **Core Safe Tests**: PASSED (140/140)
- **Inventory Sales Tests**: PASSED (110/110)
- **Avito Module Tests**: PASSED (12/12)
- **Repairs Module Tests**: PASSED (12/12)
- **Total Test Suite**: 274 passed, 0 failed.

## LIVE_DB_TEST_ISOLATION
- `LIVE_DB_SHA256_BEFORE_TESTS`: `8c8b99c4f1b9c4c7949e1cbbbffe6ae3d9a672e242ebf302361e23445387b9df`
- `LIVE_DB_SHA256_AFTER_TESTS`: `8c8b99c4f1b9c4c7949e1cbbbffe6ae3d9a672e242ebf302361e23445387b9df` (100% IDENTICAL)
- `PRODUCT_COUNT`: 56 ➔ 56
- `SALE_COUNT`: 43 ➔ 43
- `CUSTOMER_COUNT`: 12 ➔ 12
- `REPAIR_COUNT`: 19 ➔ 19
- `HISTORY_COUNT`: 46 ➔ 46

## RUNTIME_PRINT_PREVIEW
- Created test repair ID 19 (`R-20260803-0019`).
- `GET http://localhost:8040/repairs/19/print` returned HTTP 200 OK with all customer data, org details, detachable ticket, and 2-page detailed terms.

## SAFETY_SCANS
- **PRODUCTION_EXECUTABLE_MATCHES (drop_all/DROP TABLE)**: 0
- **REPAIRS DIRECT DB ACCESS (`repairs-module/app`)**: 0
- **TRACKED DB/CACHE FILES**: 0 tracked files.

## LEGAL_DISCLAIMS
LEGAL_TEXT_SOURCE: OWNER_PROVIDED_PAPER_SAMPLE
LEGAL_REVIEW_PERFORMED: false
OWNER_TEXT_ACCEPTANCE_REQUIRED: true

## FILES_CHANGED
- `repairs-module/app/core_client.py`
- `repairs-module/app/routers/repairs.py`
- `repairs-module/app/templates/repair_detail.html`
- `repairs-module/app/templates/repair_print_order.html`
- `repairs-module/app/static/repair_print.css`
- `repairs-module/tests/test_repair_print_order.py`
- `docs/stage05a_r4_printable_repair_order_and_ticket.md`
- `reports/stage05a_r4_printable_repair_order_and_ticket_report.md`
- `logs/2026-08-03.md`

## COMMIT
Commit: `Add printable repair work order and ticket`

## PUSH
Pushed to `origin/main`.

## FINAL_GIT_STATUS
Worktree clean.

## OWNER_CHECK_GUIDE
1. Open `http://localhost:8040/repairs`.
2. Open any repair detail page.
3. Click `🖨️ Печать наряд-заказа`.
4. Verify organization details (Yekaterinburg, Kuznetsova 10, INN 667009336901).
5. Verify customer & device details, missing internal notes, and missing access code raw password.
6. Verify Page 1 layout, short terms, signatures, and detachable ticket.
7. Verify Page 2 detailed terms (7 clauses, 500 rub fee, 1500 rub threshold, 14 days storage, 50 rub/day penalty, 3 months liquidation, 45 days max repair).
8. Open Print Preview (`Ctrl+P`): verify 2 A4 pages, no squares, hidden navigation buttons.

## FINAL_STATUS
FINAL_STATUS:
TECHNOREBOOT_STAGE05A_R4_PRINTABLE_REPAIR_ORDER_AND_TICKET_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_STAGE05B_WITHOUT_OWNER_ACCEPTANCE: true

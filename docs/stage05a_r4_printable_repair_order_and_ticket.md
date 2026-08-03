# Stage 05A-R4: Printable Repair Work Order and Detachable Ticket Documentation

## 1. Overview
Stage 05A-R4 implements the **Printable Repair Work Order and Detachable Ticket** feature for **Stage 05A (Repair Intake & Registry MVP)** based on the paper sample provided by the owner.

The document is rendered as a clean, 2-page A4 HTML document with print CSS and automatic data binding via Core HTTP API.

---

## 2. Print Route & UI Integration
- **Route**: `GET /repairs/{repair_id}/print` in `repairs-module`.
- **UI Button**: `🖨️ Печать наряд-заказа` on `repair_detail.html` (opens `/repairs/{id}/print` in a new tab).
- **Architecture**: `repairs-module` fetches repair order details (`GET /api/repairs/{id}`) and organization settings (`GET /api/settings/organization`) exclusively via HTTP through `CoreClient`. **Zero direct DB connections**.

---

## 3. Document Structure & Layout

### Page 1: Work Order & Detachable Ticket
- **Header**:
  - Dynamic Organization Settings (`org.name`, `org.legal_entity`, `org.inn`, `org.address`, `org.phone`). Old photo data (Novouralsk address, OGURNIP 311662921500018, old phone number) are strictly **excluded**.
  - Document title: `НАРЯД-ЗАКАЗ НА РЕМОНТ № <number>`.
  - Intake date: `Дата приема: <accepted_at>`.
- **Data Table**:
  - Customer Name, Phone, Email (only if present).
  - Device Type, Brand/Model, Serial Number (or "Не указан"), Completeness, Appearance, Reported Issue, Customer Comment (only if present), Priority, Status, Access code provided (`Да` / `Нет`), Assigned to / Accepted by.
  - **SECURITY & PRIVACY**: `internal_note` and raw access code passwords are strictly **excluded**.
- **Short Front-Side Terms**: 6 paragraphs detailing non-disassembly agreement, lost receipt rules, 3 to 45 days repair duration, 500 rubles diagnostic fee upon repair refusal, personal data processing consent, and equipment condition acceptance.
- **Intake Signatures**: Lines for Customer signature and Accepted by signature.
- **Issue & Guarantee Confirmation Block**: Standard text confirming receipt in working order, no claims, and receipt date/signature lines.
- **Detachable Ticket (Отрывной талон)**: Separated by a dotted line (`✂ -------------------- ЛИНИЯ ОТРЫВА -------------------- ✂`). Contains ticket header, customer & device info summary, org info, short ticket terms, and intake signature lines.

### Page 2: Detailed Repair, Storage & Diagnostic Terms
- Starts with `page-break-before: always;`.
- Header: `УСЛОВИЯ ПРИЕМА ОБОРУДОВАНИЯ, ПРОВЕДЕНИЯ РЕМОНТНЫХ РАБОТ, ДИАГНОСТИКИ, ХРАНЕНИЯ И ВЫДАЧИ`.
- Preamble: Repairs up to 1500 rubles pre-approved without additional customer confirmation.
- **7 Detailed Clauses**:
  1. Intake without disassembly & presumption of pre-existing internal defects.
  2. Accessories policy & non-liability for unrecorded items.
  3. Risk warning regarding pre-existing liquid/physical damage degradation.
  4. Non-liability for user misuse & floating defects diagnostic extension.
  5. Responsible storage: 14 calendar days pickup after notification, 50 rubles/day penalty, 3 months liquidation threshold.
  6. Data loss non-liability during board/storage replacement.
  7. Right to refuse repair due to lack of spare parts/resources.
- Bottom signatures: Terms acceptance agreement, date, and customer signature line.

---

## 4. Typography & Print CSS
- **Print CSS**: `@page { size: A4 portrait; margin: 8mm; }`.
- **Font Stack**: `font-family: Arial, "DejaVu Sans", "Liberation Sans", sans-serif;`. Ensures 100% clean Cyrillic text without squares or missing glyphs.
- **Page Break Control**: `break-inside: avoid` and `page-break-inside: avoid` on critical blocks; `page-break-before: always` for Page 2.
- **Print Media Query**: `@media print` hides navigation buttons (`.no-print`).

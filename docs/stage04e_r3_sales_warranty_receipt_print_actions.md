# Stage 04E-R3 Sales Warranty Receipt & Product Print Actions Documentation

## Overview
This document describes the design and user flow implementation of Stage 04E-R3 for project "Technoreboot": Sales Quantity, Warranty Options, Product Price Tag Actions, and Receipt Preview.

---

## 1. UI Navigation Updates
- **Removed:** Standalone "Ценники — скоро" navigation link.
- **Added:** Product-level price tag print action button ("Печать ценника") available directly on `/products` table rows and `/products/{id}` detail pages for `in_stock` products.

---

## 2. Product Price Tag Action (`GET /products/{id}/price-tag`)
- Opens print preview page (`price_tag_preview.html`).
- Renders product title, SKU, price, category, and placeholder barcode.
- Provides `window.print()` action button.
- Displays explicit disclaimer: *"Предварительная форма ценника. Финальный шаблон будет подключен после утверждения."*

---

## 3. Direct Sales Form (`GET /sales/new?product_id=<id>`)
- Form fields:
  - Product details (Title, SKU, status, card price)
  - Editable sale price (`price`)
  - Quantity input (`quantity`, default 1)
  - Payment method selector (`payment_method`: Cash, Card, SBP, Legal Entity Account)
  - Warranty duration (`warranty_days`, default 30)
  - "Без гарантии" checkbox (`no_warranty`): when checked, disables warranty duration input and sets `warranty_enabled=False`.
  - Additional notes (`notes`)
- On submission (`POST /sales/create`), validates input data and calls Core API `POST /api/sales/`.

---

## 4. Warranty & Receipt Preview (`GET /sales/{sale_id}/receipt`)
- Accessible from sale details page (`/sales/{sale_id}`).
- Renders sales receipt (`sale_receipt_preview.html`).
- If warranty is enabled, displays: *"Гарантия: {warranty_days} дней"*.
- If warranty is disabled ("Без гарантии"), displays disclaimer: *"Товар продаётся без гарантии, в том состоянии, в котором есть. Покупатель внимательно осмотрел товар при покупке."*
- Displays explicit disclaimer: *"Предварительная форма товарного чека. Финальный шаблон будет подключен после утверждения."*

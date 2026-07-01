# Price Tag Printing Design Decision

## 1. The Problem
The store operators need to print physical price tags for inventory. The system needs a way to format product details into printable layouts (individual tags or A4 sheets) without complicating the core business logic.

## 2. Analyzed Options

**Option A:** inventory-sales-module handles rendering.
- The module fetches product details via GET /api/products/{id}.
- It uses its own Jinja2 templates (price_tag.html, price_tag_sheet.html) to render the UI.
- Browser's native window.print() is used to send to the printer.

**Option B:** Core API stores templates and renders PDF/HTML.
- Core holds template strings in the DB or files.
- The module requests a rendered file via GET /api/products/{id}/price-tag.

## 3. Decision
**Chosen Option:** Option A (Render in inventory-sales-module).

**Reasoning:**
1. **Separation of Concerns:** Core API should remain a pure data provider. Formatting, HTML, and printing are strictly presentation layer concerns.
2. **Flexibility:** Store managers can tweak CSS and HTML layouts in the frontend module much faster without altering Core backend services.
3. **Simplicity for MVP:** Generating a clean HTML page with CSS @media print rules and using window.print() requires zero additional backend dependencies (like WeasyPrint or PDF generators) in the Core.

## 4. Required Data
The Core API already provides all necessary fields via /api/products/{id}:
- 	itle
- sku
- sale_price
- rand & model
- condition
- description (shortened for tag)

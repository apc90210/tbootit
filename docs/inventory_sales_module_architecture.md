# Inventory, Sales & Price Tags Module Architecture

## 1. Overview
The inventory-sales-module is the primary workspace for store operators. It acts as an API client connecting to the Core API to manage products, process sales, and print price tags. It does NOT have its own database and DOES NOT access the Core DB directly.

## 2. Infrastructure
- **Container Name:** 	echnoreboot-inventory-sales-module (planned)
- **Port:** 8030
- **Framework:** FastAPI with Jinja2 templates (similar to dmin-shell, but intended for production business use)
- **Environment Variables:** CORE_API_BASE_URL=http://core:8000

## 3. Directory Structure
`
inventory-sales-module/
  Dockerfile
  requirements.txt
  README.md
  app/
    main.py
    config.py
    core_client.py
    schemas.py
    routers/
      health.py
      products.py
      sales.py
      price_tags.py
    templates/
      index.html
      products.html
      product_detail.html
      sale.html
      price_tag.html
      price_tag_sheet.html
    static/
      app.css
      app.js
  tests/
    test_health.py
    test_core_client.py
    test_products_ui_contract.py
    test_sales_contract.py
    test_price_tag_render.py
`

## 4. Components
- **Core Client (core_client.py):** Encapsulates HTTP requests to the Core API (products, sales, customers). Handles errors and translates JSON into local Pydantic schemas.
- **Routers:** Handle incoming HTTP requests from the browser, fetch data via the Core Client, and return rendered HTML.
- **Templates:** Jinja2 templates using TailwindCSS (or equivalent standard CSS) for the operator UI.

## 5. Security & Isolation
- **Stateless:** The module maintains no state. All state is in the Core API.
- **No DB Access:** The module has no database credentials.

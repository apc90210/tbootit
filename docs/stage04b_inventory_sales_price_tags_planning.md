# Stage 04B: Inventory, Sales & Price Tags Planning Master Plan

## 1. Objective
Design the operational store module (inventory-sales-module) and outline the sequential implementation stages to realize it.

## 2. Planned Module Details
- **Name:** inventory-sales-module
- **Architecture:** FastAPI frontend, Jinja2 templates, communicating with Core API. No direct DB access.
- **Port:** 8030

## 3. Staged Implementation Plan

### Stage 04C: Core Sales Flow Hardening
Before building the UI, the Core API must safely support the business logic.
- Rewrite POST /api/sales to validate product states (in_stock, eserved).
- Ensure POST /api/sales logs ProductEvent and properly executes the sold status transition.
- Add pagination and date filtering to GET /api/sales.
- Add POST /api/sales/{id}/cancel to reverse a transaction safely.

### Stage 04D: Inventory/Sales Module Skeleton
Build the basic framework for the new module.
- Scaffold the FastAPI app in inventory-sales-module/.
- Setup Docker configurations (Port 8030).
- Implement the Core API Client.
- Build the "Products List" (read-only table) and "Product Details" views using Jinja2.

### Stage 04E: Sales UI MVP
Implement the cash register workflow.
- Build the "New Sale" screen.
- Implement forms to capture price, payment method, and customer.
- Wire up the frontend to POST /api/sales on the Core API.
- Ensure the UI reflects the status change to "Sold".

### Stage 04F: Price Tags MVP
Implement printing capabilities.
- Create print-optimized HTML templates using @media print.
- Implement a screen to preview price tags for a single product.
- Add a button to print via window.print().
- Add bulk print (A4 sheet) support.

## 4. Current State
Planning is complete. Ready to proceed with implementation starting from Stage 04C.

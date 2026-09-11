# Owner Request: Unified Top Navigation Bar Across All Pages

**Date:** 2026-09-11T21:57:20+03:00  
**Source:** User Voice Message  

## Instruction Summary
The Owner noticed that when navigating between different pages and modules (Admin Shell, Products / Inventory, Sales, Reports, Repairs, Avito, Backups, Certificates), the top navigation bar changes appearance, and key menu items disappear or differ.

Required:
1. Ensure the standard top navigation bar is 100% unified, consistent, and identical across all pages in all modules.
2. The top bar must include all key system links:
   - Панель управления (`/`)
   - Товары (`/inventory/products`)
   - JSON импорт / экспорт (`/products/json`)
   - Продажи (`/inventory/sales`)
   - Корзина (`/inventory/cart`)
   - Отчёты (`/inventory/reports/sales`)
   - Ремонты (`/repairs/repairs`)
   - Расширение Avito (`/avito/extension`)
   - Резервные копии (`/backups`)
   - Сертификаты / Доступ (`/certificates`)
3. The visual design, styling, and menu items of the top navbar must be uniform everywhere across the application so that switching pages feels seamless without jarring layout jumps or disappearing items.
4. Keep all existing backend routes and automated tests passing (806+ tests).
5. Verify live via Gateway 8443.

# TECHNOREBOOT — Owner Voice Request: Product Detail Action Buttons (Top & Bottom Duplication)

**Date:** 2026-09-11 14:31:59+03:00  
**Source:** Audio file attached to user request at 14:31:59+03:00  
**Target:** `inventory-sales-module/app/templates/product_detail.html`

## Transcript of Owner Voice Request
> "Так, нужно изменить карточку товара. То есть когда открываешь карточку товара, чтобы кнопки 'Редактировать товар', 'Продать', 'В корзину', 'Ценник' дублировались и сверху обязательно, все эти... и снизу были, и сверху."

## Requirements
1. In the product detail card (`/inventory/products/{product_id}`), duplicate all key action buttons both at the top (under or within the header) and at the bottom:
   - "Редактировать товар" (✏️ Редактировать товар)
   - "Продать" (Продать)
   - "В корзину" (В корзину + cart quantity indicator + go to cart link)
   - "Ценник 58×40" (Ценник 58×40)
   - "Назад к товарам" (Назад к товарам)
2. Ensure both top and bottom toolbars are styled cleanly, consistently, and responsively.
3. Ensure cart quick-add logic in `cart_quick_add.js` handles both top and bottom buttons so adding to cart from either updates both indicators and the header counter.
4. Keep all button state conditions identical (disabled when out of stock / not store location / etc.).
5. Run full test suites across `inventory-sales-module`, `admin-shell`, and `core`.
6. Live verification via Gateway 8443 (mTLS) with Owner certificate.

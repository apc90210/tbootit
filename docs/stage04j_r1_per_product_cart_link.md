# Stage04J-R1: Per-Product Cart Link UX Enhancement

## Overview
Stage04J-R1 adds dedicated "Перейти в корзину" links and "В корзине: N" badges directly beside products that have been added to the session cart, while maintaining the global top cart navigation button "Перейти в корзину (N)".

## Features & Implementation Details
1. **Server-Side Template Context (`products.py`)**:
   - `cart_quantities_by_product_id`: Mapping of `product_id -> quantity` for all items currently in the session cart.
   - `cart_product_ids`: Set of `product_id`s in cart for set membership testing.
   - Applied to both `/products` (`list_products`) and `/products/{product_id}` (`product_detail`).

2. **Template Layout & Markup (`products.html`, `product_detail.html`)**:
   - Wrapped per-product actions in a `.product-cart-actions` container with `data-product-id="{{ item.id }}"`.
   - Included `<a href="/cart" class="btn btn-success product-go-to-cart">Перейти в корзину</a>` conditionally hidden if the product is not in `cart_product_ids`.
   - Included `<span class="product-cart-quantity" aria-live="polite">В корзине: <span class="product-cart-quantity-value">N</span></span>` conditionally hidden if the product is not in `cart_product_ids`.

3. **Dynamic Client Updates (`cart_quick_add.js`)**:
   - Upon successful AJAX `POST /cart/add-quick`:
     - Updates header total cart button (`#go-to-cart-button`) counter.
     - Locates all `.product-cart-actions[data-product-id="..."]` matching `data.product_id`.
     - Reveals `.product-go-to-cart` button and `.product-cart-quantity` label.
     - Updates `.product-cart-quantity-value` to `data.product_quantity_in_cart`.
   - On error or failed validation:
     - Local cart button remains hidden for non-cart products.
     - Russian error toast is displayed.

4. **Lifecycle & Session State Consistency**:
   - Upon full page reload (`/products` or `/products/{id}`), server-rendered Jinja2 template checks session cart state and displays local cart links and quantities accurately.
   - After checkout or cart clear (`POST /cart/clear` or `POST /cart/checkout`), cart is emptied, hiding top header button and per-product local cart buttons across all views.

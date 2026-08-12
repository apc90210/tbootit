document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('.quick-add-form');
    const cartBtn = document.getElementById('go-to-cart-button');

    // Create toast notification element if not exists
    let toast = document.getElementById('quick-add-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'quick-add-toast';
        toast.setAttribute('aria-live', 'polite');
        toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; background: #333; color: #fff; padding: 12px 20px; border-radius: 6px; z-index: 9999; display: none; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);';
        document.body.appendChild(toast);
    }

    function showToast(msg, isError) {
        toast.textContent = msg;
        toast.style.background = isError ? '#dc3545' : '#28a745';
        toast.style.display = 'block';
        setTimeout(function () {
            toast.style.display = 'none';
        }, 3000);
    }

    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const submitBtn = form.querySelector('.quick-add-btn') || form.querySelector('button[type="submit"]');
            if (!submitBtn || submitBtn.disabled) return;

            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Добавляем...';

            const formData = new FormData(form);

            fetch('/inventory/cart/add-quick', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function (res) {
                return res.json().then(function (data) {
                    return { status: res.status, data: data };
                });
            })
            .then(function (result) {
                const data = result.data;
                if (data && data.ok) {
                    // Update header cart button counter
                    if (cartBtn) {
                        const span = cartBtn.querySelector('span');
                        if (span) span.textContent = data.cart_items_count;
                        cartBtn.style.display = 'inline-block';
                    }

                    // Update per-product cart button & quantity for all containers matching product_id
                    const prodId = data.product_id;
                    if (prodId !== undefined && prodId !== null) {
                        const containers = document.querySelectorAll('[data-product-id="' + prodId + '"]');
                        containers.forEach(function (container) {
                            const localCartBtn = container.querySelector('.product-go-to-cart') ||
                                (container.classList.contains('product-go-to-cart') ? container : null) ||
                                (container.parentElement ? container.parentElement.querySelector('.product-go-to-cart') : null);
                            if (localCartBtn) {
                                localCartBtn.style.display = 'inline-block';
                            }
                            const localQtyWrap = container.querySelector('.product-cart-quantity') ||
                                (container.parentElement ? container.parentElement.querySelector('.product-cart-quantity') : null);
                            if (localQtyWrap) {
                                localQtyWrap.style.display = 'inline-block';
                            }
                            const localQtyVal = container.querySelector('.product-cart-quantity-value') ||
                                (container.parentElement ? container.parentElement.querySelector('.product-cart-quantity-value') : null);
                            if (localQtyVal && data.product_quantity_in_cart !== undefined) {
                                localQtyVal.textContent = data.product_quantity_in_cart;
                            }
                        });
                    }

                    submitBtn.textContent = '✓ Добавлено';
                    showToast(data.message || 'Товар добавлен в корзину', false);
                    setTimeout(function () {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                    }, 1500);
                } else {
                    const errMsg = (data && data.message) ? data.message : 'Не удалось добавить товар в корзину';
                    showToast(errMsg, true);
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            })
            .catch(function (err) {
                showToast('Ошибка сети при добавлении в корзину', true);
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    });
});

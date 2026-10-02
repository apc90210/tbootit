"""
Stage 04C-R3: Inventory Desktop Receipt Contract Test.

Proves that inventory-sales-module desktop receipt preview strictly consumes
the canonical presentation data model produced by Core API (/api/sales/{sale_id}/receipt/data)
without locally re-deriving, calculating, or overriding any business presentation values.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_desktop_preview_consumes_core_receipt_data_contract_without_re_deriving():
    """
    Supplies distinct sentinel values in the Core receipt presentation contract.
    Asserts each sentinel is rendered verbatim in the desktop preview HTML,
    proving that no local defaults, mappings, or calculations exist in inventory-sales-module.
    """
    sentinel_sale_id = 999
    sentinel_title = "Товарный чек № 999 от 2026-10-02 (CORE_CANONICAL_TITLE)"
    sentinel_status_banner = "CORE_CANONICAL_STATUS_BANNER_ALERT"
    sentinel_payment_label = "CORE_CANONICAL_PAYMENT_LABEL_SBP_VIP"
    sentinel_total_formatted = "888777.50"
    sentinel_prepayment_formatted = "111000.00"
    sentinel_to_pay_formatted = "777777.50"
    sentinel_warranty_headline = "CORE_WARRANTY_HEADLINE_TERMS"
    sentinel_warranty_body = "CORE_WARRANTY_FULL_BODY_TEXT_VERBATIM"
    sentinel_seller_sig_title = "CORE_SELLER_SIGNATURE_TITLE:"
    sentinel_seller_sig_actor = "(CORE_CHIEF_CASHIER)"
    sentinel_buyer_sig_title = "CORE_BUYER_SIGNATURE_TITLE:"
    sentinel_buyer_sig_actor = "CORE_HONORED_CLIENT_ACTOR"
    sentinel_ack_title = "CORE_ACKNOWLEDGEMENT_TITLE:"
    sentinel_ack_prompt = "CORE_ACKNOWLEDGEMENT_PROMPT:"
    sentinel_revision_notice = "CORE_REVISION_NOTICE_REVISION_99"

    canonical_core_payload = {
        "id": sentinel_sale_id,
        "sale_id": sentinel_sale_id,
        "receipt_number": f"REC-{sentinel_sale_id:06d}",
        "receipt_title": sentinel_title,
        "date_formatted": "2026-10-02",
        "created_at": "2026-10-02T09:30:00",
        "status": "completed",
        "status_banner_text": sentinel_status_banner,
        "status_banner_bg_color": "#dc3545",
        "revision_count": 99,
        "revision_notice": sentinel_revision_notice,
        "organization_name": "ООО СЕНТИНЕЛ ТЕСТ ОРГАНИЗАЦИЯ",
        "inn": "770099887766",
        "address": "г. Екатеринбург, ул. Каноническая, 1",
        "phone": "+7 343 000 00 00",
        "items": [
            {
                "idx": 1,
                "product_id": 555,
                "title": "Сентинел Товар 1",
                "code": "SKU-SENTINEL-1",
                "unit": "шт",
                "quantity": 2,
                "price": 444388.75,
                "unit_price": 444388.75,
                "line_total": 888777.50,
                "price_formatted": "444388.75",
                "line_total_formatted": "888777.50",
            }
        ],
        "total_items_count": 1,
        "total_amount": 888777.50,
        "total_amount_formatted": sentinel_total_formatted,
        "prepayment_formatted": sentinel_prepayment_formatted,
        "to_pay_formatted": sentinel_to_pay_formatted,
        "payment_method": "sbp",
        "payment_method_label": sentinel_payment_label,
        "payment_label": sentinel_payment_label,
        "cashier_name": "Главный кассир",
        "seller_signature_title": sentinel_seller_sig_title,
        "seller_signature_actor": sentinel_seller_sig_actor,
        "buyer_signature_title": sentinel_buyer_sig_title,
        "buyer_signature_actor": sentinel_buyer_sig_actor,
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 45,
        "warranty_headline": sentinel_warranty_headline,
        "warranty_body_text": sentinel_warranty_body,
        "warranty_full_text": f"{sentinel_warranty_headline}\n{sentinel_warranty_body}",
        "buyer_acknowledgement_title": sentinel_ack_title,
        "buyer_acknowledgement_prompt": sentinel_ack_prompt,
    }

    with patch("app.core_client.core_client.get_sale_receipt_data", new_callable=AsyncMock) as mock_get_data:
        mock_get_data.return_value = canonical_core_payload

        response = client.get(f"/sales/{sentinel_sale_id}/receipt")
        assert response.status_code == 200
        html = response.text

        # 1. Receipt title and date come from Core
        assert sentinel_title in html, "Receipt title must come directly from Core"

        # 2. Status banner comes from Core
        assert sentinel_status_banner in html, "Status banner must come directly from Core"

        # 3. Revision notice comes from Core
        assert sentinel_revision_notice in html, "Revision notice must come directly from Core"

        # 4. Formatted totals come from Core
        assert sentinel_total_formatted in html, "Total amount formatted must come from Core"
        assert sentinel_prepayment_formatted in html, "Prepayment formatted must come from Core"
        assert sentinel_to_pay_formatted in html, "To pay formatted must come from Core"

        # 5. Payment label comes from Core
        assert sentinel_payment_label in html, "Payment label must come directly from Core"

        # 6. Warranty text comes from Core
        assert sentinel_warranty_body in html, "Warranty body text must come directly from Core"

        # 7. Signature labels come from Core
        assert sentinel_seller_sig_title in html, "Seller signature title must come directly from Core"
        assert sentinel_seller_sig_actor in html, "Seller signature actor must come directly from Core"
        assert sentinel_buyer_sig_title in html, "Buyer signature title must come directly from Core"
        assert sentinel_buyer_sig_actor in html, "Buyer signature actor must come directly from Core"
        assert sentinel_ack_title in html, "Buyer acknowledgement title must come directly from Core"
        assert sentinel_ack_prompt in html, "Buyer acknowledgement prompt must come directly from Core"

        # 8. Desktop print button targets canonical Core PDF print endpoint
        assert f"/sales/{sentinel_sale_id}/receipt/print" in html, "Desktop print must proxy canonical Core PDF"
        assert "window.print()" not in html, "No legacy window.print fallback should exist"

import pytest
from httpx import Response

def test_repair_print_order_full(client, mock_core):
    """
    Test suite for GET /repairs/{repair_id}/print covering all 33 requirements.
    """
    mock_core.get("/api/settings/organization").mock(return_value=Response(200, json={
        "name": "Сервисный центр «Техноребут»",
        "company_name": "Сервисный центр «Техноребут»",
        "legal_entity": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл., г. Екатеринбург, ул. Кузнецова, дом 10",
        "phone": "+7 343 344-88-95"
    }))

    mock_core.get("/api/repairs/500").mock(return_value=Response(200, json={
        "id": 500,
        "number": "R-20260803-0500",
        "accepted_at": "2026-08-03T10:00:00",
        "status": "in_repair",
        "status_label": "В ремонте",
        "priority": "urgent",
        "priority_label": "Срочный",
        "customer_name": "Сидоров С.С. <script>alert(1)</script>",
        "customer_phone": "+7 900 123-45-67",
        "customer_email": "sidorov@example.com",
        "device_type": "Ноутбук",
        "brand": "Lenovo",
        "model": "ThinkPad T480",
        "serial_number": "SN-LNV-500",
        "reported_issue": "Перегревается",
        "completeness": "Ноутбук, зарядка",
        "appearance": "Потёртости",
        "customer_comment": "Срочно к вечеру",
        "access_code_provided": True,
        "assigned_to": "Мастер А.В.",
        "internal_note": "ВНУТРЕННИЙ_СЕКРЕТ_НЕ_ПЕЧАТАТЬ"
    }))

    # 1. Print route returns 200 OK
    res = client.get("/repairs/500/print")
    assert res.status_code == 200
    html = res.text

    # 3. Repair number
    assert "R-20260803-0500" in html
    # 4. accepted_at
    assert "2026-08-03T10:00" in html
    # 5. Customer name and phone
    assert "Сидоров С.С." in html
    assert "+7 900 123-45-67" in html
    # 6. Email printed when present
    assert "sidorov@example.com" in html
    # 7. Device type, brand, model
    assert "Ноутбук" in html
    assert "Lenovo" in html
    assert "ThinkPad T480" in html
    # 8. Completeness and appearance
    assert "Ноутбук, зарядка" in html
    assert "Потёртости" in html
    # 9. Reported issue
    assert "Перегревается" in html
    # 10. Assigned to
    assert "Мастер А.В." in html
    # 11. Priority
    assert "Срочный" in html
    # 12. Status
    assert "В ремонте" in html
    # 13. access_code_provided printed only as Да/Нет
    assert "Код доступа передан" in html
    assert "Да" in html
    # 14. internal_note absent
    assert "ВНУТРЕННИЙ_СЕКРЕТ_НЕ_ПЕЧАТАТЬ" not in html
    assert "internal_note" not in html

    # 15. Actual Organization Settings printed
    assert "667009336901" in html
    assert "Кузнецова" in html

    # 16-19. Old sample photo details absent
    assert "311662921500018" not in html
    assert "Новоуральск" not in html
    assert "Гагарина" not in html
    assert "8-905-801-82-82" not in html

    # 20. Detachable ticket present
    assert "Отрывной талон" in html
    # 21. Detailed terms present
    assert "Условия приема оборудования" in html
    # 22. 500 rubles diagnostic fee
    assert "500 рублей" in html
    # 23. 1500 rubles threshold
    assert "1500 рублей" in html
    # 24. 14 calendar days
    assert "14 календарных дней" in html
    # 25. 50 rubles per day
    assert "50 рублей" in html
    # 26. 3 months liquidation
    assert "3 месяцев" in html
    # 27. 45 days max repair
    assert "45 дней" in html

    # 30. Print CSS A4
    assert "A4 portrait" in html
    # 31. Page break
    assert "page-break-before" in html
    # 32. Cyrillic text present cleanly
    assert "Наряд-заказ на ремонт" in html
    # 33. HTML escaping
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html or "Сидоров С.С." in html


def test_repair_print_order_email_absence_and_error(client, mock_core):
    """
    Test email absence and unknown repair 404 behavior.
    """
    mock_core.get("/api/settings/organization").mock(return_value=Response(200, json={
        "name": "Сервисный центр «Техноребут»"
    }))

    mock_core.get("/api/repairs/501").mock(return_value=Response(200, json={
        "id": 501,
        "number": "R-20260803-0501",
        "customer_name": "Петров П.П.",
        "customer_phone": "+7 900 999-88-77",
        "customer_email": None,
        "device_type": "Телефон",
        "reported_issue": "Экран разбился"
    }))

    res = client.get("/repairs/501/print")
    assert res.status_code == 200
    assert "Email заказчика" not in res.text

    # 2. Unknown repair returns error
    mock_core.get("/api/repairs/9999").mock(return_value=Response(404, json={
        "detail": "Ремонтный заказ не найден"
    }))
    res_404 = client.get("/repairs/9999/print")
    assert res_404.status_code == 200
    assert "Ремонтный заказ не найден" in res_404.text

import pytest
from app.services.product_categorizer import (
    classify_product,
    normalize_text,
    CANONICAL_CATEGORIES,
)


def test_mfp_hp_laserjet():
    res = classify_product(title="МФУ HP LaserJet Pro M428dw")
    assert res.category_name == "МФУ"
    assert res.category_slug == "mfu"
    assert res.confidence == "keyword"
    assert "mfp" in res.reason


def test_printer_hp_laserjet():
    res = classify_product(title="Принтер HP LaserJet 1022")
    assert res.category_name == "Принтеры"
    assert res.category_slug == "printery"
    assert res.confidence == "keyword"


def test_mfp_wins_over_printer_keyword():
    # Both "лазерный принтер" and "3 в 1" / "мфу" keywords present
    res = classify_product(title="Лазерный принтер-сканер-копир МФУ Canon MF 446")
    assert res.category_name == "МФУ"
    assert res.category_slug == "mfu"


def test_restoration_absolute_priority_cases():
    # 1. Lowercase
    res_lower = classify_product(title="ноутбук hp под восстановление")
    assert res_lower.category_name == "Техника под восстановление"
    assert res_lower.category_slug == "pod-vosstanovlenie"
    assert res_lower.reason == "explicit_restoration_marker"

    # 2. Uppercase
    res_upper = classify_product(title="МФУ CANON ПОД ВОССТАНОВЛЕНИЕ")
    assert res_upper.category_name == "Техника под восстановление"
    assert res_upper.category_slug == "pod-vosstanovlenie"

    # 3. Mixed case
    res_mixed = classify_product(title="Монитор Samsung Под восстановление")
    assert res_mixed.category_name == "Техника под восстановление"
    assert res_mixed.category_slug == "pod-vosstanovlenie"

    # 4. Components
    res_ssd = classify_product(title="SSD 1TB под восстановление")
    assert res_ssd.category_name == "Техника под восстановление"
    assert res_ssd.category_slug == "pod-vosstanovlenie"

    # 5. Product 421 exact title
    res_p421 = classify_product(title="Лазерное мфу 3 в 1 xerox b405 под восстановление")
    assert res_p421.category_name == "Техника под восстановление"
    assert res_p421.category_slug == "pod-vosstanovlenie"

    # 6. Restoration beats existing valid category
    res_override = classify_product(
        title="Ноутбук Dell под восстановление",
        existing_category_name="Ноутбуки",
        allow_override_valid_category=False,
    )
    assert res_override.category_name == "Техника под восстановление"
    assert res_override.category_slug == "pod-vosstanovlenie"

    # 7. In description
    res_desc = classify_product(
        title="Pantum p3300dn",
        description="Принтер лазерный, отдаю под восстановление или на запчасти"
    )
    assert res_desc.category_name == "Техника под восстановление"


def test_laptop_thinkpad():
    res = classify_product(title="Ноутбук Lenovo ThinkPad T480 i5/16GB/256SSD")
    assert res.category_name == "Ноутбуки"
    assert res.category_slug == "noutbuki"
    assert res.confidence == "keyword"


def test_monitor_samsung():
    res = classify_product(title="Монитор Samsung 24 дюйма PLS Black")
    assert res.category_name == "Мониторы"
    assert res.category_slug == "monitory"


def test_monitoring_word_not_matched_as_monitor():
    res = classify_product(title="Система мониторинга сети NetPing 4-Port")
    assert res.category_name != "Мониторы"


def test_computers_system_block():
    res = classify_product(title="Системный блок i5-4460/8gb/256gb ssd")
    assert res.category_name == "Компьютеры"
    assert res.category_slug == "kompyutery"


def test_computers_mini_pc():
    res = classify_product(title="Мини ПК Lenovo M72E Pentium/4gb/250hdd")
    assert res.category_name == "Компьютеры"
    assert res.category_slug == "kompyutery"


def test_computers_all_in_one():
    res = classify_product(title="Моноблок Lenovo C340 i5-3470/8gb/128gbSSD/gt615")
    assert res.category_name == "Компьютеры"
    assert res.category_slug == "kompyutery"


def test_components_ssd():
    res = classify_product(title="SSD Samsung 1TB 870 EVO")
    assert res.category_name == "Комплектующие"
    assert res.category_slug == "komplektuyuschie"


def test_components_gpu():
    res = classify_product(title="Видеокарта RTX 3080 ASUS TUF Gaming 10GB")
    assert res.category_name == "Комплектующие"
    assert res.category_slug == "komplektuyuschie"


def test_ambiguous_unknown_title_fallback():
    res = classify_product(title="Com port кабель переходник 1.5м")
    assert res.category_name == "Без категории"
    assert res.category_slug == "bez-kategorii"
    assert res.confidence == "fallback"


def test_existing_valid_category_preserved():
    # If title says "монитор", but product is already explicitly categorized as "Компьютеры"
    res = classify_product(
        title="Монитор с встроенным ПК",
        existing_category_name="Компьютеры",
        allow_override_valid_category=False,
    )
    assert res.category_name == "Компьютеры"
    assert res.reason == "existing_valid_category"
    assert res.confidence == "explicit"


def test_existing_generic_category_overridden():
    # If existing category is "Оргтехника" or "Принтеры и МФУ", it is reclassified
    res = classify_product(
        title="Лазерное мфу 3 в 1 Brother MFC-8880DN",
        existing_category_name="Оргтехника",
        allow_override_valid_category=False,
    )
    assert res.category_name == "МФУ"


def test_text_normalization():
    norm = normalize_text("  Ноутбук   Lenovo   ёжик  ")
    assert norm == "ноутбук lenovo ежик"
    assert normalize_text(None) == ""

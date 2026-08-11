import os
from app.parser import _parse_profile_page, _parse_item_page

def test_parse_profile():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "samples", "avito_profile_sample.html")
    with open(sample_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    urls = _parse_profile_page(html, "sample://profile")
    assert len(urls) == 2
    assert "mock-item-111111" in urls[0]
    assert "mock-item-222222" in urls[1]

def test_parse_item():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "samples", "avito_item_sample.html")
    with open(sample_path, "r", encoding="utf-8") as f:
        html = f.read()

        
    ad = _parse_item_page(html, "https://www.avito.ru/mock-item-111111", "mock-run-id", "path.html")
    assert ad.title == "Ноутбук Lenovo ThinkPad T480"
    assert ad.price == 25000.0
    assert ad.external_id == "111111"
    assert "Отличный ноутбук" in ad.description
    assert ad.parameters["Производитель"] == "Lenovo"

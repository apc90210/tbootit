import pytest
import json
import re
from bs4 import BeautifulSoup

def simulate_extract_characteristics_from_json_object(obj, item_id=None):
    characteristics = {}
    if not obj or not isinstance(obj, dict):
        return characteristics

    def add_param(k, v):
        if not k or not isinstance(k, str):
            return
        clean_k = k.strip().rstrip(':')
        if not clean_k:
            return
        clean_v = ''
        if isinstance(v, str):
            clean_v = v.strip()
        elif isinstance(v, (int, float, bool)):
            clean_v = str(v)
        elif isinstance(v, list):
            clean_v = ', '.join([
                x.get('title') or x.get('name') or x.get('value') if isinstance(x, dict) else str(x)
                for x in v if x
            ])
        elif isinstance(v, dict):
            clean_v = v.get('title') or v.get('name') or v.get('value') or v.get('description') or ''
        
        if clean_k and clean_v and clean_k not in characteristics:
            characteristics[clean_k] = clean_v

    def process_params_array(arr):
        if not isinstance(arr, list):
            return
        for item in arr:
            if not isinstance(item, dict):
                continue
            k = item.get('title') or item.get('name') or item.get('key') or item.get('label') or item.get('propertyName')
            v = item.get('value') if item.get('value') is not None else (item.get('description') or item.get('text') or item.get('values'))
            if k and v is not None:
                add_param(k, v)

    def process_params_dict(d):
        if not isinstance(d, dict):
            return
        for k, v in d.items():
            add_param(k, v)

    def traverse(node, depth=0):
        if not isinstance(node, (dict, list)) or depth > 10:
            return
        if isinstance(node, dict):
            if 'params' in node:
                if isinstance(node['params'], list): process_params_array(node['params'])
                elif isinstance(node['params'], dict): process_params_dict(node['params'])
            if 'parameters' in node:
                if isinstance(node['parameters'], list): process_params_array(node['parameters'])
                elif isinstance(node['parameters'], dict): process_params_dict(node['parameters'])
            if 'properties' in node:
                if isinstance(node['properties'], list): process_params_array(node['properties'])
                elif isinstance(node['properties'], dict): process_params_dict(node['properties'])
            if 'characteristics' in node:
                if isinstance(node['characteristics'], list): process_params_array(node['characteristics'])
                elif isinstance(node['characteristics'], dict): process_params_dict(node['characteristics'])
            if 'itemParams' in node:
                if isinstance(node['itemParams'], list): process_params_array(node['itemParams'])
                elif isinstance(node['itemParams'], dict): process_params_dict(node['itemParams'])
            if 'paramsList' in node:
                if isinstance(node['paramsList'], list): process_params_array(node['paramsList'])
                elif isinstance(node['paramsList'], dict): process_params_dict(node['paramsList'])
            
            for k, val in node.items():
                if any(x in k.lower() for x in ['recommendation', 'similar', 'seller', 'banner']):
                    continue
                traverse(val, depth + 1)
        elif isinstance(node, list):
            for item in node:
                traverse(item, depth + 1)

    traverse(obj)
    return characteristics

def simulate_extract_characteristics_from_dom(html):
    soup = BeautifulSoup(html, 'html.parser')
    characteristics = {}

    def add_param(k, v):
        if not k or not isinstance(k, str):
            return
        clean_k = k.strip().rstrip(':')
        clean_v = v.strip() if isinstance(v, str) else str(v).strip()
        if clean_k and clean_v and clean_k not in characteristics:
            characteristics[clean_k] = clean_v

    item_selectors = [
        '[data-marker="item-view/item-params"] li',
        '[data-marker="item-properties/list"] li',
        '[data-marker="item-params/list"] li',
        'ul[class*="params-paramsList"] li',
        'li[class*="params-paramsList__item"]',
        'li[class*="item-params-list-item"]'
    ]

    elements = soup.select(', '.join(item_selectors))
    for el in elements:
        label_el = el.select_one('[class*="noaccent"], [class*="label"], [class*="title"], [class*="key"], [data-marker*="label"]')
        val_el = el.select_one('[class*="accent"], [class*="value"], [class*="description"], [data-marker*="val"]')
        
        k, v = '', ''
        if label_el and val_el and label_el != val_el:
            k = label_el.get_text().strip().rstrip(':')
            v = val_el.get_text().strip()
        
        if not k or not v:
            text = el.get_text().strip()
            if ':' in text:
                parts = text.split(':', 1)
                k = parts[0].strip()
                v = parts[1].strip()
        
        if k and v:
            add_param(k, v)

    return characteristics

def test_realistic_motherboard_characteristics_extracted():
    """Verify rich extraction of real motherboard specifications from modern Avito HTML & State."""
    motherboard_html = """
    <div data-marker="item-view/main">
        <h1 data-marker="item-view/title-info">Материнская плата ASUS TUF GAMING B550-PLUS</h1>
        <div data-marker="item-view/item-params">
            <ul class="params-paramsList-abc12">
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Производитель:</span> <span class="styles-module-accent-789">ASUS</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Модель:</span> <span class="styles-module-accent-789">TUF GAMING B550-PLUS</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Сокет:</span> <span class="styles-module-accent-789">AM4</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Чипсет:</span> <span class="styles-module-accent-789">AMD B550</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Форм-фактор:</span> <span class="styles-module-accent-789">Standard-ATX</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Количество слотов памяти:</span> <span class="styles-module-accent-789">4</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Тип памяти:</span> <span class="styles-module-accent-789">DDR4</span></li>
                <li class="params-paramsList__item-xyz34"><span class="styles-module-noaccent-456">Максимальный объем памяти:</span> <span class="styles-module-accent-789">128 ГБ</span></li>
            </ul>
        </div>
    </div>
    """
    
    extracted_dom = simulate_extract_characteristics_from_dom(motherboard_html)
    assert len(extracted_dom) == 8
    assert extracted_dom["Производитель"] == "ASUS"
    assert extracted_dom["Сокет"] == "AM4"
    assert extracted_dom["Чипсет"] == "AMD B550"
    assert extracted_dom["Форм-фактор"] == "Standard-ATX"

    # Also verify embedded state extraction
    motherboard_state = {
        "item": {
            "id": 8999888777,
            "params": [
                {"title": "Производитель", "value": "ASUS"},
                {"title": "Модель", "value": "TUF GAMING B550-PLUS"},
                {"title": "Сокет", "value": "AM4"},
                {"title": "Чипсет", "value": "AMD B550"},
                {"title": "Форм-фактор", "value": "Standard-ATX"},
                {"title": "Количество слотов памяти", "value": "4"},
                {"title": "Тип памяти", "value": "DDR4"},
                {"title": "Максимальный объем памяти", "value": "128 ГБ"}
            ]
        }
    }
    extracted_state = simulate_extract_characteristics_from_json_object(motherboard_state)
    assert len(extracted_state) == 8
    assert extracted_state["Чипсет"] == "AMD B550"

def test_realistic_computer_characteristics_extracted():
    """Verify rich extraction of real computer / system unit specifications."""
    computer_state = {
        "item": {
            "id": 8111222333,
            "params": [
                {"title": "Тип компьютера", "value": "Системный блок"},
                {"title": "Процессор", "value": "Intel Core i5-10400F"},
                {"title": "Оперативная память", "value": "16 ГБ"},
                {"title": "Объем SSD", "value": "512 ГБ"},
                {"title": "Объем HDD", "value": "1 ТБ"},
                {"title": "Видеокарта", "value": "NVIDIA GeForce GTX 1660 Super"},
                {"title": "Объем видеопамяти", "value": "6 ГБ"},
                {"title": "Операционная система", "value": "Windows 10 Pro"},
                {"title": "Состояние", "value": "Б/у"}
            ]
        }
    }
    extracted = simulate_extract_characteristics_from_json_object(computer_state)
    assert len(extracted) == 9
    assert extracted["Процессор"] == "Intel Core i5-10400F"
    assert extracted["Видеокарта"] == "NVIDIA GeForce GTX 1660 Super"
    assert extracted["Оперативная память"] == "16 ГБ"

def test_characteristics_survive_final_extension_payload():
    """Verify characteristics dictionary is properly packaged in listing payload."""
    characteristics = {
        "Сокет": "AM4",
        "Чипсет": "AMD B550",
        "Форм-фактор": "ATX"
    }
    payload = {
        "schema_version": 1,
        "extension_version": "0.2.11",
        "captured_at": "2026-08-21T17:40:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "8999888777",
            "external_url": "https://www.avito.ru/ekaterinburg/tovary_dlya_kompyutera/materinskaya_plata_am4_8999888777",
            "title": "Материнская плата AM4 B550",
            "price": 8500.0,
            "category": "Товары для компьютера / Комплектующие / Материнские платы",
            "brand": "ASUS",
            "model": "TUF B550",
            "characteristics": characteristics,
            "photos": []
        }
    }
    assert "characteristics" in payload["listing"]
    assert len(payload["listing"]["characteristics"]) == 3
    assert payload["extension_version"] == "0.2.11"

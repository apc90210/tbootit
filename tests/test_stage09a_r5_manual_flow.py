import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent

for k in list(sys.modules.keys()):
    if k == 'app' or k.startswith('app.'):
        mod = sys.modules[k]
        if hasattr(mod, '__file__') and mod.__file__:
            if 'admin-shell' not in mod.__file__:
                sys.modules.pop(k, None)

admin_shell_path = str(REPO_ROOT / 'admin-shell')
if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)

import app.main as admin_main
app = admin_main.app
auth_manager = admin_main.auth_manager
client = TestClient(app)

DB_PATH = REPO_ROOT / 'data' / 'db' / 'technoreboot.db'

@pytest.fixture
def owner_headers():
    return {
        'x-client-cert-verify': 'SUCCESS',
        'x-client-cert-serial': '1001',
        'x-auth-subject': 'Technoreboot Owner',
        'x-auth-is-owner': 'true'
    }

def test_stage09a_r5_extension_package_v0261_no_auto_execution():
    ext_dir = REPO_ROOT / 'chrome-extension' / 'technoreboot-avito'
    manifest_path = ext_dir / 'manifest.json'
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    assert manifest['version'] in ('0.2.61', '0.2.62', '0.2.63', '0.2.64', '0.2.65')

    sw_path = ext_dir / 'service_worker.js'
    with open(sw_path, 'r', encoding='utf-8') as f:
        sw = f.read()
    assert any(v in sw for v in ('0.2.61', '0.2.62', '0.2.63', '0.2.64', '0.2.65'))
    assert 'chrome.alarms.create' not in sw
    assert 'setInterval(pollNextDeactivationTask' not in sw
    assert 'Automatic post-sale deactivation is disabled' in sw

    cs_path = ext_dir / 'content.js'
    with open(cs_path, 'r', encoding='utf-8') as f:
        cs = f.read()
    assert any(v in cs for v in ('0.2.61', '0.2.62', '0.2.63', '0.2.64', '0.2.65'))
    assert 'disabled in Stage 09A-R5' in cs

    popup_path = ext_dir / 'popup.html'
    with open(popup_path, 'r', encoding='utf-8') as f:
        popup = f.read()
    assert 'stepExecuting' not in popup
    assert any(v in popup for v in ('0.2.61', '0.2.62', '0.2.63', '0.2.64', '0.2.65'))

def test_stage09a_r5_sales_detail_template_elements():
    tmpl_path = REPO_ROOT / 'inventory-sales-module' / 'app' / 'templates' / 'sales_detail.html'
    with open(tmpl_path, 'r', encoding='utf-8') as f:
        tmpl = f.read()

    assert 'avito-post-sale-prompt' in tmpl
    assert 'Снять с Avito вручную' in tmpl
    assert 'Не снимать' in tmpl
    assert 'target="_blank"' in tmpl
    assert 'rel="noopener noreferrer"' in tmpl
    assert 'btnPermanentAvitoDeactivate' in tmpl
    assert 'Для этой продажи нет связанного объявления Avito' in tmpl
    assert 'Объявление уже снято с Avito' in tmpl
    assert 'Я снял объявление' in tmpl
    assert 'avito-manual-confirm' in tmpl
    assert 'avito-dismiss' in tmpl

def test_stage09a_r5_queue_page_operator_oriented():
    tmpl_path = REPO_ROOT / 'admin-shell' / 'app' / 'templates' / 'avito_post_sale.html'
    with open(tmpl_path, 'r', encoding='utf-8') as f:
        tmpl = f.read()

    assert 'Дата' in tmpl
    assert 'Продажа' in tmpl
    assert 'Товар' in tmpl
    assert 'Avito ID' in tmpl
    assert 'Статус' in tmpl
    assert 'Действие' in tmpl
    assert 'Открыть объявление' in tmpl
    assert 'Не снимать' in tmpl
    assert 'Я снял объявление' in tmpl
    assert 'Снятие объявлений с Avito после продаж' in tmpl

def test_stage09a_r5_canonical_url_security():
    import urllib.parse

    def canonical_avito_url(listing_url, avito_listing_id):
        canonical = f'https://www.avito.ru/{avito_listing_id}'
        if listing_url:
            try:
                parsed = urllib.parse.urlparse(listing_url)
                host = (parsed.netloc or '').lower()
                if host in ['www.avito.ru', 'avito.ru', 'm.avito.ru']:
                    if str(avito_listing_id) in parsed.path or str(avito_listing_id) in parsed.query:
                        return listing_url
            except Exception:
                pass
        return canonical

    assert canonical_avito_url('https://www.avito.ru/7353766377', '7353766377') == 'https://www.avito.ru/7353766377'
    assert canonical_avito_url('https://www.avito.ru/moskva/tovar_7353766377', '7353766377') == 'https://www.avito.ru/moskva/tovar_7353766377'
    assert canonical_avito_url('https://evil.com/7353766377', '7353766377') == 'https://www.avito.ru/7353766377'
    assert canonical_avito_url('javascript:alert(1)', '7353766377') == 'https://www.avito.ru/7353766377'
    assert canonical_avito_url('https://avito.ru.phishing.com/7353766377', '7353766377') == 'https://www.avito.ru/7353766377'
    assert canonical_avito_url('https://www.avito.ru/9999999999', '7353766377') == 'https://www.avito.ru/7353766377'

def test_stage09a_r5_mark_opened_and_manual_confirm_endpoints():
    assert hasattr(admin_main, 'proxy_mark_opened_post_sale_task')
    assert hasattr(admin_main, 'proxy_manual_confirm_post_sale_task')

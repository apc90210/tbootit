import pytest
from app.browser_worker import AvitoBrowserWorker

@pytest.mark.asyncio
async def test_my_listings_discovery():
    """
    Test extraction of own listings from profile page HTML:
    - Extracts external_item_id, external_url, title, price, remote_status
    """
    mock_html = """
    <html>
        <body>
            <h1>Мои объявления</h1>
            <div class="item-snippet">
                <a class="item-link" href="/moskva/noutbuki/lenovo_ideapad_3_2847291011">
                    <h3 class="title">Ноутбук Lenovo IdeaPad 3</h3>
                </a>
                <div class="price">25 000 ₽</div>
            </div>
            <div class="item-snippet">
                <a class="item-link" href="/moskva/telefony/iphone_11_1122334455">
                    <h3 class="title">iPhone 11 64GB</h3>
                </a>
                <div class="price">18 500 ₽</div>
                <div>Завершено</div>
            </div>
        </body>
    </html>
    """

    worker = AvitoBrowserWorker("main")
    items = await worker.discover_my_listings(mock_html=mock_html)

    assert len(items) == 2
    assert items[0]["external_item_id"] == "2847291011"
    assert items[0]["title"] == "Ноутбук Lenovo IdeaPad 3"
    assert items[0]["price"] == 25000.0
    assert items[0]["remote_status"] == "active"

    assert items[1]["external_item_id"] == "1122334455"
    assert items[1]["price"] == 18500.0
    assert items[1]["remote_status"] == "inactive"

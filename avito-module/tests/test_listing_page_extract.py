import pytest
from app.browser_worker import AvitoBrowserWorker

@pytest.mark.asyncio
async def test_listing_page_card_extraction():
    """
    Test detailed card extraction from an individual item page HTML:
    - Extracts title, price, description, parameters/attributes, photo URLs
    """
    mock_html = """
    <html>
        <body>
            <h1 class="title-info-title-text">Игровой системный блок Core i5 RTX 3060</h1>
            <span class="js-item-price">45 000 ₽</span>
            <div class="item-description-text">Мощный ПК для игр и работы. Состояние идеальное.</div>
            <div class="item-params">
                <ul>
                    <li class="item-params-list-item">Процессор: Intel Core i5-10400F</li>
                    <li class="item-params-list-item">Видеокарта: NVIDIA GeForce RTX 3060</li>
                    <li class="item-params-list-item">Объем ОЗУ: 16 ГБ</li>
                </ul>
            </div>
            <img src="https://img.avito.st/image/1/111.jpg" />
            <img src="https://img.avito.st/image/1/222.jpg" />
        </body>
    </html>
    """

    worker = AvitoBrowserWorker("main")
    card = await worker.extract_item_card("https://www.avito.ru/item/9900", mock_html=mock_html)

    assert card["title"] == "Игровой системный блок Core i5 RTX 3060"
    assert card["price"] == 45000.0
    assert "Мощный ПК" in card["description"]
    assert card["parameters"]["Процессор"] == "Intel Core i5-10400F"
    assert card["parameters"]["Видеокарта"] == "NVIDIA GeForce RTX 3060"
    assert len(card["photos"]) == 2
    assert card["photos"][0]["url"] == "https://img.avito.st/image/1/111.jpg"

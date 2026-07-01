from app.schemas import ParsedAd
from app.normalizer import normalize_to_product_card

def test_normalize():
    ad = ParsedAd(
        id="123",
        run_id="run",
        source_url="https://avito.ru/item-111",
        external_id="111",
        title="Phone",
        price=100.0,
        description="Desc",
        parameters={"Производитель": "Apple", "Модель": "iPhone 13"},
        parse_status="parsed",
        created_at="now"
    )
    
    card = normalize_to_product_card(ad)
    assert card.product.sku == "AVITO-111"
    assert card.product.brand == "Apple"
    assert card.product.model == "iPhone 13"
    assert card.avito.title == "Phone"
    assert card.avito.price == 100.0
    assert card.operation == "create_or_update"

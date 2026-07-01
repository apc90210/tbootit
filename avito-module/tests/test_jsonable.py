import pytest
from fastapi.encoders import jsonable_encoder
from app.schemas import ParsedAd
from app import normalizer

def test_jsonable_encoder_on_product_card():
    ad = ParsedAd(
        id="test-ad-1",
        run_id="run",
        source_url="http",
        title="Test",
        parse_status="parsed",
        created_at="now"
    )
    product_card = normalizer.normalize_to_product_card(ad)
    json_data = jsonable_encoder(product_card)
    assert json_data is not None

from fastapi import APIRouter, HTTPException
from app.schemas import ProductCardImport
from app import storage
from app import normalizer
from app import core_client

router = APIRouter(prefix="/api/avito/parsed-ads")

@router.get("/{ad_id}/product-card-json", response_model=ProductCardImport)
async def get_product_card_json(ad_id: str):
    ad = storage.get_parsed_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Parsed Ad not found")
    return normalizer.normalize_to_product_card(ad)

@router.post("/{ad_id}/core-import-preview")
async def core_import_preview(ad_id: str):
    ad = storage.get_parsed_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Parsed Ad not found")
        
    product_card = normalizer.normalize_to_product_card(ad)
    validation_result = await core_client.validate_product_card(product_card)
    
    return {
        "status": "preview_done",
        "ad_id": ad_id,
        "product_card": product_card,
        "core_validation": validation_result
    }

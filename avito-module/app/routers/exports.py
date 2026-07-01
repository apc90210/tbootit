from fastapi import APIRouter, HTTPException
from app.schemas import ProductCardImport, ImportRequest
from datetime import datetime
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

@router.post("/{ad_id}/core-import")
async def core_import(ad_id: str, request: ImportRequest):
    ad = storage.get_parsed_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Parsed Ad not found")
        
    status = storage.get_import_status(ad_id)
    if status and status.get("status") == "imported" and not request.force:
        return {"status": "already_imported", "ad_id": ad_id}

    product_card = normalizer.normalize_to_product_card(ad)
    import_result = await core_client.import_product_card(product_card)
    
    status_data = {
        "status": import_result.get("status", "failed"),
        "last_attempt_at": datetime.utcnow().isoformat(),
        "core_response": import_result
    }
    storage.save_import_status(ad_id, status_data)
    
    if status_data["status"] == "failed":
        raise HTTPException(status_code=400, detail={"msg": "Import failed", "core_response": import_result})
        
    return {
        "status": "imported",
        "ad_id": ad_id,
        "core_response": import_result
    }

@router.get("/{ad_id}/core-import-status")
async def core_import_status(ad_id: str):
    ad = storage.get_parsed_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Parsed Ad not found")
        
    status = storage.get_import_status(ad_id)
    if not status:
        return {"status": "not_imported"}
    return status

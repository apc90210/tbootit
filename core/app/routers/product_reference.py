"""
Core API Router for Product Reference Catalog.

Provides OWNER-only endpoints for managing reference models, aliases, previewing
matches, dry-run/apply imports, exports, and learning from confirmed products.

Endpoints:
- GET    /api/product-reference/models
- GET    /api/product-reference/models/{id}
- POST   /api/product-reference/models
- PUT    /api/product-reference/models/{id}
- DELETE /api/product-reference/models/{id}
- POST   /api/product-reference/models/{id}/aliases
- DELETE /api/product-reference/models/{id}/aliases/{alias_id}
- POST   /api/product-reference/match-preview
- POST   /api/product-reference/enrich-preview/{product_id}
- POST   /api/product-reference/import
- GET    /api/product-reference/export
- POST   /api/product-reference/learn-from-product/{product_id}
"""

import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.services.product_reference_matcher import (
    match_product,
    normalize_for_matching,
    generate_stable_key,
)
from app.services.product_reference_enricher import (
    enrich_product_from_reference,
)
from app.services.product_reference_json_service import (
    import_reference_models_from_dict,
    export_reference_models_to_dict,
)
from app.services.product_reference_learn import (
    save_product_as_reference_model,
)

def verify_owner_access(request: Request):
    """Verify owner authorization via header and token."""
    auth_is_owner = request.headers.get("x-auth-is-owner")
    api_token = request.headers.get("x-api-token")

    if auth_is_owner != "1" or (settings.api_token and api_token != settings.api_token):
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён: требуется авторизация владельца"
        )
    return True


router = APIRouter(
    prefix="/api/product-reference",
    tags=["Product Reference Catalog"],
    dependencies=[Depends(verify_owner_access)]
)




@router.get("/models", response_model=schemas.ProductReferenceListResponse)
def list_reference_models(
    q: Optional[str] = None,
    brand: Optional[str] = None,
    device_type: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List reference models with filtering and pagination."""
    query = db.query(models.ProductReferenceModel)

    if q:
        q_norm = normalize_for_matching(q)
        q_pat = f"%{q_norm}%"
        query = query.filter(
            or_(
                func.lower(models.ProductReferenceModel.canonical_name).like(q_pat),
                func.lower(models.ProductReferenceModel.brand).like(q_pat),
                func.lower(models.ProductReferenceModel.model).like(q_pat),
                func.lower(models.ProductReferenceModel.stable_key).like(q_pat),
            )
        )

    if brand:
        query = query.filter(func.lower(models.ProductReferenceModel.brand) == brand.strip().lower())
    if device_type:
        query = query.filter(models.ProductReferenceModel.device_type == device_type.strip().lower())
    if active is not None:
        query = query.filter(models.ProductReferenceModel.active == active)

    total = query.count()
    items = query.order_by(models.ProductReferenceModel.brand.asc(), models.ProductReferenceModel.model.asc()).offset(offset).limit(limit).all()

    # Parse specifications for response
    result_items = []
    for m in items:
        specs_dict = None
        if m.specifications_json:
            try:
                specs_dict = json.loads(m.specifications_json)
            except Exception:
                pass
        m_dict = {
            "id": m.id,
            "stable_key": m.stable_key,
            "canonical_name": m.canonical_name,
            "brand": m.brand,
            "model": m.model,
            "device_type": m.device_type,
            "default_category_id": m.default_category_id,
            "specifications_json": m.specifications_json,
            "specifications": specs_dict,
            "site_title": m.site_title,
            "site_description": m.site_description,
            "active": m.active,
            "source": m.source,
            "source_note": m.source_note,
            "aliases": m.aliases,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        result_items.append(m_dict)

    return {
        "items": result_items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/models/{model_id}", response_model=schemas.ProductReferenceModel)
def get_reference_model(model_id: int, db: Session = Depends(get_db)):
    """Retrieve a single reference model by ID."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    specs_dict = None
    if ref.specifications_json:
        try:
            specs_dict = json.loads(ref.specifications_json)
        except Exception:
            pass

    return {
        "id": ref.id,
        "stable_key": ref.stable_key,
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "specifications_json": ref.specifications_json,
        "specifications": specs_dict,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
        "source_note": ref.source_note,
        "aliases": ref.aliases,
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
    }


@router.post("/models", response_model=schemas.ProductReferenceModel, dependencies=[Depends(verify_owner_access)])
def create_reference_model(payload: schemas.ProductReferenceModelCreate, db: Session = Depends(get_db)):
    """Create a new reference model (OWNER-only)."""
    brand = payload.brand.strip()
    model_name = payload.model.strip()
    canonical_name = (payload.canonical_name or f"{brand} {model_name}").strip()
    stable_key = payload.stable_key or generate_stable_key(brand, model_name)

    existing = db.query(models.ProductReferenceModel).filter(
        models.ProductReferenceModel.stable_key == stable_key
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Reference model with key '{stable_key}' already exists (ID: {existing.id})")

    specs_json = payload.specifications_json
    if not specs_json and payload.specifications:
        specs_json = json.dumps(payload.specifications, ensure_ascii=False)

    ref = models.ProductReferenceModel(
        stable_key=stable_key,
        canonical_name=canonical_name,
        brand=brand,
        model=model_name,
        device_type=payload.device_type,
        default_category_id=payload.default_category_id,
        specifications_json=specs_json,
        site_title=payload.site_title or canonical_name,
        site_description=payload.site_description,
        active=payload.active if payload.active is not None else True,
        source=payload.source or "manual",
        source_note=payload.source_note,
    )
    db.add(ref)
    db.flush()

    # Add default aliases
    alias_texts = [canonical_name, f"{brand} {model_name}"]
    if payload.aliases:
        alias_texts.extend(payload.aliases)

    seen_norm = set()
    for a_str in alias_texts:
        norm = normalize_for_matching(a_str)
        if norm and norm not in seen_norm:
            a_obj = models.ProductReferenceAlias(
                reference_model_id=ref.id,
                alias=a_str.strip(),
                normalized_alias=norm,
                priority=100,
                active=True,
            )
            db.add(a_obj)
            seen_norm.add(norm)

    db.commit()
    db.refresh(ref)

    specs_dict = payload.specifications or (json.loads(specs_json) if specs_json else None)
    return {
        "id": ref.id,
        "stable_key": ref.stable_key,
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "specifications_json": ref.specifications_json,
        "specifications": specs_dict,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
        "source_note": ref.source_note,
        "aliases": ref.aliases,
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
    }


@router.put("/models/{model_id}", response_model=schemas.ProductReferenceModel, dependencies=[Depends(verify_owner_access)])
def update_reference_model(model_id: int, payload: schemas.ProductReferenceModelUpdate, db: Session = Depends(get_db)):
    """Update an existing reference model (OWNER-only)."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    if payload.canonical_name is not None:
        ref.canonical_name = payload.canonical_name.strip()
    if payload.brand is not None:
        ref.brand = payload.brand.strip()
    if payload.model is not None:
        ref.model = payload.model.strip()
    if payload.device_type is not None:
        ref.device_type = payload.device_type
    if payload.default_category_id is not None:
        ref.default_category_id = payload.default_category_id
    if payload.site_title is not None:
        ref.site_title = payload.site_title
    if payload.site_description is not None:
        ref.site_description = payload.site_description
    if payload.active is not None:
        ref.active = payload.active
    if payload.source is not None:
        ref.source = payload.source
    if payload.source_note is not None:
        ref.source_note = payload.source_note

    if payload.specifications is not None:
        ref.specifications_json = json.dumps(payload.specifications, ensure_ascii=False)
    elif payload.specifications_json is not None:
        ref.specifications_json = payload.specifications_json

    db.commit()
    db.refresh(ref)

    specs_dict = None
    if ref.specifications_json:
        try:
            specs_dict = json.loads(ref.specifications_json)
        except Exception:
            pass

    return {
        "id": ref.id,
        "stable_key": ref.stable_key,
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "specifications_json": ref.specifications_json,
        "specifications": specs_dict,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
        "source_note": ref.source_note,
        "aliases": ref.aliases,
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
    }


@router.delete("/models/{model_id}", dependencies=[Depends(verify_owner_access)])
def delete_reference_model(model_id: int, hard: bool = False, db: Session = Depends(get_db)):
    """Deactivate (or hard delete) a reference model (OWNER-only)."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    if hard:
        db.delete(ref)
        db.commit()
        return {"deleted": True, "hard": True, "id": model_id}
    else:
        ref.active = False
        db.commit()
        return {"deactivated": True, "id": model_id}


@router.post("/models/{model_id}/aliases", response_model=schemas.ProductReferenceAlias, dependencies=[Depends(verify_owner_access)])
def add_alias(model_id: int, payload: schemas.ProductReferenceAliasCreate, db: Session = Depends(get_db)):
    """Add an alias to a reference model (OWNER-only)."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    alias_clean = payload.alias.strip()
    norm = payload.normalized_alias or normalize_for_matching(alias_clean)
    if not norm:
        raise HTTPException(status_code=400, detail="Alias cannot be empty")

    existing = db.query(models.ProductReferenceAlias).filter(
        models.ProductReferenceAlias.reference_model_id == model_id,
        models.ProductReferenceAlias.normalized_alias == norm,
    ).first()
    if existing:
        return existing

    new_alias = models.ProductReferenceAlias(
        reference_model_id=model_id,
        alias=alias_clean,
        normalized_alias=norm,
        priority=payload.priority or 100,
        active=payload.active if payload.active is not None else True,
    )
    db.add(new_alias)
    db.commit()
    db.refresh(new_alias)
    return new_alias


@router.delete("/models/{model_id}/aliases/{alias_id}", dependencies=[Depends(verify_owner_access)])
def delete_alias(model_id: int, alias_id: int, db: Session = Depends(get_db)):
    """Delete an alias (OWNER-only)."""
    alias_obj = db.query(models.ProductReferenceAlias).filter(
        models.ProductReferenceAlias.id == alias_id,
        models.ProductReferenceAlias.reference_model_id == model_id,
    ).first()
    if not alias_obj:
        raise HTTPException(status_code=404, detail="Alias not found")

    db.delete(alias_obj)
    db.commit()
    return {"deleted": True, "alias_id": alias_id}


@router.post("/match-preview", response_model=schemas.ProductReferenceMatchPreviewResponse)
def match_preview(payload: schemas.ProductReferenceMatchPreviewRequest, db: Session = Depends(get_db)):
    """
    Preview matching result for a product title without making DB writes.
    Fulfills Section 22 contract.
    """
    res = match_product(
        db=db,
        title=payload.title,
        brand=payload.brand,
        model=payload.model,
        description=payload.description,
        active_only=True,
    )
    return res.to_dict()


@router.post("/enrich-preview/{product_id}")
def enrich_preview(product_id: int, db: Session = Depends(get_db)):
    """
    Preview enrichment for an existing product without making DB writes.
    """
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    match_res = match_product(
        db=db,
        title=prod.title,
        brand=prod.brand,
        model=prod.model,
        description=prod.description,
        active_only=True,
    )

    if not match_res.matched or not match_res.reference_model:
        return {
            "product_id": prod.id,
            "title": prod.title,
            "matched": False,
            "status": match_res.status,
            "reason": match_res.reason,
            "candidates": [c.to_dict() for c in match_res.candidates],
        }

    enrich_res = enrich_product_from_reference(
        db=db,
        product=prod,
        reference=match_res.reference_model,
        method=match_res.method or "manual",
        confidence=match_res.confidence or 1.0,
        apply=False,  # DRY RUN preview
    )

    fields_filled = enrich_res.get("fields_filled", {})
    return {
        "product_id": prod.id,
        "title": prod.title,
        "matched": True,
        "reference_model_id": match_res.reference_model_id,
        "canonical_name": match_res.canonical_name,
        "method": match_res.method,
        "confidence": match_res.confidence,
        "fields_filled": fields_filled,
        "enrichment_preview": {
            "specifications": fields_filled.get("specifications_added", {}),
            **fields_filled
        }
    }


@router.post("/import")
def import_reference_catalog(payload: Dict[str, Any], dry_run: bool = Query(False), db: Session = Depends(get_db)):
    """Import reference models JSON package (OWNER-only)."""
    res = import_reference_models_from_dict(
        db=db,
        data=payload,
        dry_run=dry_run,
        source="api_import",
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail={"errors": res.get("errors")})
    return res


@router.get("/export")
def export_reference_catalog(active_only: bool = Query(False), db: Session = Depends(get_db)):
    """Export reference catalog as standard JSON (Section 14)."""
    return export_reference_models_to_dict(db, active_only=active_only)


@router.post("/learn-from-product/{product_id}")
def learn_from_product(
    product_id: int,
    payload: Optional[schemas.ProductReferenceLearnRequest] = None,
    db: Session = Depends(get_db)
):
    """Explicitly save/promote a confirmed product as a Reference Model (OWNER-only)."""
    canonical_name = payload.canonical_name if payload else None
    aliases = []
    if payload:
        if payload.custom_aliases:
            aliases.extend(payload.custom_aliases)
        if payload.raw_alias:
            aliases.append(payload.raw_alias)

    try:
        res = save_product_as_reference_model(
            db=db,
            product_id=product_id,
            canonical_name=canonical_name,
            custom_aliases=aliases or None,
            override_existing=True,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


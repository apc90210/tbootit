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
import datetime
import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.routers.customers import log_audit
from app.services.product_reference_matcher import (
    match_product,
    find_reference_candidates,
    generate_stable_key,
    normalize_for_matching,
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
from app.services.ai import get_ai_provider

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


CONFLICTS_FILE_PATHS = [
    os.path.join(r"C:\tbootit\data", "reference_catalog", "EXTERNAL_ENRICHMENT_CONFLICTS.json"),
    r"C:\tboot-site\AntiGravity\PROMPT_WEB_07C_EXTERNAL_VERIFIED_REFERENCE_ENRICHMENT\Outbox\EXTERNAL_ENRICHMENT_CONFLICTS.json"
]

def _load_conflicts_data() -> List[Dict[str, Any]]:
    for path in CONFLICTS_FILE_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return []

router = APIRouter(
    prefix="/api/product-reference",
    tags=["Product Reference Catalog"],
    dependencies=[Depends(verify_owner_access)]
)

public_router = APIRouter(
    prefix="/api/product-reference",
    tags=["Product Reference Catalog (Search & Intake)"],
)

public_router_plural = APIRouter(
    prefix="/api/product-references",
    tags=["Product Reference Catalog (Search & Intake)"],
)


@router.get("/meta")
def get_reference_meta(db: Session = Depends(get_db)):
    """Get metadata for reference catalog filters and dropdowns."""
    brands = [b[0] for b in db.query(models.ProductReferenceModel.brand).distinct().order_by(models.ProductReferenceModel.brand.asc()).all() if b[0]]
    device_types = [d[0] for d in db.query(models.ProductReferenceModel.device_type).distinct().order_by(models.ProductReferenceModel.device_type.asc()).all() if d[0]]
    categories = db.query(models.Category).order_by(models.Category.name.asc()).all()
    cat_list = [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories]
    return {
        "brands": brands,
        "device_types": device_types,
        "categories": cat_list,
    }


@router.get("/models", response_model=schemas.ProductReferenceListResponse)
def list_reference_models(
    q: Optional[str] = None,
    brand: Optional[str] = None,
    device_type: Optional[str] = None,
    category_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    active: Optional[bool] = None,
    incomplete_specs: Optional[bool] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List reference models with filtering, completeness checks, and pagination."""
    query = db.query(models.ProductReferenceModel)

    if q:
        q_clean = q.strip()
        q_norm = normalize_for_matching(q_clean)
        q_pat = f"%{q_norm}%"
        alias_model_ids = [
            a[0] for a in db.query(models.ProductReferenceAlias.reference_model_id).filter(
                or_(
                    func.lower(models.ProductReferenceAlias.normalized_alias).like(q_pat),
                    func.lower(models.ProductReferenceAlias.alias).like(f"%{q_clean.lower()}%")
                )
            ).all()
        ]
        conds = [
            func.lower(models.ProductReferenceModel.canonical_name).like(q_pat),
            func.lower(models.ProductReferenceModel.brand).like(q_pat),
            func.lower(models.ProductReferenceModel.model).like(q_pat),
            func.lower(models.ProductReferenceModel.stable_key).like(q_pat),
        ]
        if alias_model_ids:
            conds.append(models.ProductReferenceModel.id.in_(alias_model_ids))
        query = query.filter(or_(*conds))

    if brand:
        query = query.filter(func.lower(models.ProductReferenceModel.brand) == brand.strip().lower())
    if device_type:
        query = query.filter(models.ProductReferenceModel.device_type == device_type.strip().lower())
    if category_id is not None:
        query = query.filter(models.ProductReferenceModel.default_category_id == category_id)
    if active is not None:
        query = query.filter(models.ProductReferenceModel.active == active)
    if source:
        query = query.filter(models.ProductReferenceModel.source == source.strip())

    items = query.order_by(models.ProductReferenceModel.brand.asc(), models.ProductReferenceModel.model.asc()).all()

    conflicts_all = _load_conflicts_data()
    conflict_map = {}
    for c in conflicts_all:
        k = c.get("stable_key")
        if k:
            conflict_map.setdefault(k, []).append(c)

    # Parse specifications and counts
    result_items = []
    for m in items:
        specs_dict = None
        if m.specifications_json:
            try:
                specs_dict = json.loads(m.specifications_json)
            except Exception:
                pass
        specs_count = len(specs_dict) if specs_dict else 0

        # Filter incomplete_specs if requested
        if incomplete_specs is True and specs_count >= 5:
            continue
        elif incomplete_specs is False and specs_count < 5:
            continue

        m_conflicts = conflict_map.get(m.stable_key, [])
        has_conflict = any(c.get("status") in ("conflict", "unresolved") for c in m_conflicts)
        v_state = getattr(m, "verification_state", "verified") or "verified"

        # Filter status_filter if requested
        if status_filter == "verified" and (v_state != "verified" or has_conflict):
            continue
        elif status_filter == "needs_review" and not (v_state == "needs_review" or specs_count < 5):
            continue
        elif status_filter == "conflict" and not has_conflict:
            continue

        linked_count = db.query(models.Product).filter(models.Product.reference_model_id == m.id).count()
        aliases_count = len(m.aliases) if m.aliases else 0

        source_urls = []
        if m.source_urls_json:
            try:
                source_urls = json.loads(m.source_urls_json)
            except Exception:
                source_urls = []

        m_dict = {
            "id": m.id,
            "stable_key": m.stable_key,
            "canonical_name": m.canonical_name,
            "brand": m.brand,
            "model": m.model,
            "device_type": m.device_type,
            "default_category_id": m.default_category_id,
            "category_name": m.default_category.name if m.default_category else None,
            "specifications_json": m.specifications_json,
            "specifications": specs_dict,
            "site_title": m.site_title,
            "site_description": m.site_description,
            "active": m.active,
            "source": m.source,
            "source_note": m.source_note,
            "verification_state": v_state,
            "has_conflict": has_conflict,
            "source_urls": source_urls,
            "conflicts": m_conflicts,
            "aliases": m.aliases,
            "linked_products_count": linked_count,
            "specifications_count": specs_count,
            "aliases_count": aliases_count,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        result_items.append(m_dict)

    total = len(result_items)
    paged_items = result_items[offset:offset + limit]

    return {
        "items": paged_items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/models/{model_id}", response_model=schemas.ProductReferenceModel)
def get_reference_model(model_id: int, db: Session = Depends(get_db)):
    """Retrieve a single reference model by ID with metadata counts."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    specs_dict = None
    if ref.specifications_json:
        try:
            specs_dict = json.loads(ref.specifications_json)
        except Exception:
            pass
    specs_count = len(specs_dict) if specs_dict else 0
    linked_count = db.query(models.Product).filter(models.Product.reference_model_id == ref.id).count()
    aliases_count = len(ref.aliases) if ref.aliases else 0

    model_conflicts = [c for c in _load_conflicts_data() if c.get("stable_key") == ref.stable_key]
    has_conflict = any(c.get("status") in ("conflict", "unresolved") for c in model_conflicts)

    source_urls = []
    if ref.source_urls_json:
        try:
            source_urls = json.loads(ref.source_urls_json)
        except Exception:
            source_urls = []

    return {
        "id": ref.id,
        "stable_key": ref.stable_key,
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "category_name": ref.default_category.name if ref.default_category else None,
        "specifications_json": ref.specifications_json,
        "specifications": specs_dict,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
        "source_note": ref.source_note,
        "verification_state": getattr(ref, "verification_state", "verified") or "verified",
        "has_conflict": has_conflict,
        "source_urls": source_urls,
        "conflicts": model_conflicts,
        "aliases": ref.aliases,
        "linked_products_count": linked_count,
        "specifications_count": specs_count,
        "aliases_count": aliases_count,
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
    }


@router.get("/models/{model_id}/products", response_model=List[schemas.ProductReferenceLinkedProductItem])
def get_model_linked_products(model_id: int, db: Session = Depends(get_db)):
    """Retrieve all warehouse products linked to a reference model (read-only instance list)."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    products = db.query(models.Product).filter(models.Product.reference_model_id == model_id).order_by(models.Product.id.asc()).all()
    results = []
    for p in products:
        photo_url = None
        if p.photos:
            photo_url = p.photos[0].media_url or f"/media/product_photos/{p.photos[0].filename}"

        results.append(schemas.ProductReferenceLinkedProductItem(
            id=p.id,
            title=p.title,
            brand=p.brand,
            model=p.model,
            category_id=p.category_id,
            category_name=p.category.name if p.category else None,
            sale_price=float(p.sale_price) if p.sale_price is not None else None,
            status=p.status,
            condition=p.condition,
            serial_number=p.serial_number,
            primary_photo_url=photo_url,
            reference_match_method=p.reference_match_method,
            reference_confidence=p.reference_match_confidence,
            reference_matched_at=p.reference_enriched_at,
        ))
    return results


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

    log_audit(
        db=db,
        entity_type="product_reference_model",
        entity_id=ref.id,
        action="create",
        new_value={
            "canonical_name": ref.canonical_name,
            "brand": ref.brand,
            "model": ref.model,
            "device_type": ref.device_type,
            "stable_key": ref.stable_key,
        },
        comment=f"Owner created reference model #{ref.id} ({ref.canonical_name})"
    )

    db.commit()
    db.refresh(ref)

    specs_dict = payload.specifications or (json.loads(specs_json) if specs_json else None)
    specs_count = len(specs_dict) if specs_dict else 0
    aliases_count = len(ref.aliases) if ref.aliases else 0

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
        "verification_state": getattr(ref, "verification_state", "verified") or "verified",
        "aliases": ref.aliases,
        "linked_products_count": 0,
        "specifications_count": specs_count,
        "aliases_count": aliases_count,
        "created_at": ref.created_at,
        "updated_at": ref.updated_at,
    }


@router.put("/models/{model_id}", response_model=schemas.ProductReferenceModel, dependencies=[Depends(verify_owner_access)])
def update_reference_model(model_id: int, payload: schemas.ProductReferenceModelUpdate, db: Session = Depends(get_db)):
    """Update an existing reference model (OWNER-only)."""
    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    old_val = {
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
    }

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
    if payload.verification_state is not None:
        ref.verification_state = payload.verification_state
    if payload.source_urls_json is not None:
        ref.source_urls_json = payload.source_urls_json

    if payload.specifications is not None:
        ref.specifications_json = json.dumps(payload.specifications, ensure_ascii=False)
    elif payload.specifications_json is not None:
        ref.specifications_json = payload.specifications_json

    ref.updated_at = datetime.datetime.now(datetime.timezone.utc)

    log_audit(
        db=db,
        entity_type="product_reference_model",
        entity_id=ref.id,
        action="update",
        old_value=old_val,
        new_value={
            "canonical_name": ref.canonical_name,
            "brand": ref.brand,
            "model": ref.model,
            "device_type": ref.device_type,
            "site_title": ref.site_title,
            "site_description": ref.site_description,
            "active": ref.active,
            "source": ref.source,
            "verification_state": ref.verification_state,
        },
        comment=f"Owner updated reference model #{ref.id} ({ref.canonical_name})"
    )

    db.commit()
    db.refresh(ref)

    specs_dict = None
    if ref.specifications_json:
        try:
            specs_dict = json.loads(ref.specifications_json)
        except Exception:
            pass
    specs_count = len(specs_dict) if specs_dict else 0
    linked_count = db.query(models.Product).filter(models.Product.reference_model_id == ref.id).count()
    aliases_count = len(ref.aliases) if ref.aliases else 0

    model_conflicts = [c for c in _load_conflicts_data() if c.get("stable_key") == ref.stable_key]
    has_conflict = any(c.get("status") in ("conflict", "unresolved") for c in model_conflicts)

    source_urls = []
    if ref.source_urls_json:
        try:
            source_urls = json.loads(ref.source_urls_json)
        except Exception:
            source_urls = []

    return {
        "id": ref.id,
        "stable_key": ref.stable_key,
        "canonical_name": ref.canonical_name,
        "brand": ref.brand,
        "model": ref.model,
        "device_type": ref.device_type,
        "default_category_id": ref.default_category_id,
        "category_name": ref.default_category.name if ref.default_category else None,
        "specifications_json": ref.specifications_json,
        "specifications": specs_dict,
        "site_title": ref.site_title,
        "site_description": ref.site_description,
        "active": ref.active,
        "source": ref.source,
        "source_note": ref.source_note,
        "verification_state": getattr(ref, "verification_state", "verified") or "verified",
        "has_conflict": has_conflict,
        "source_urls": source_urls,
        "conflicts": model_conflicts,
        "aliases": ref.aliases,
        "linked_products_count": linked_count,
        "specifications_count": specs_count,
        "aliases_count": aliases_count,
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
        log_audit(
            db=db,
            entity_type="product_reference_model",
            entity_id=ref.id,
            action="delete",
            old_value={"id": ref.id, "canonical_name": ref.canonical_name},
            new_value={"deleted": True},
            comment=f"Owner hard deleted reference model #{ref.id} ({ref.canonical_name})"
        )
        db.delete(ref)
        db.commit()
        return {"deleted": True, "hard": True, "id": model_id}
    else:
        ref.active = False
        ref.updated_at = datetime.datetime.now(datetime.timezone.utc)
        log_audit(
            db=db,
            entity_type="product_reference_model",
            entity_id=ref.id,
            action="deactivate",
            old_value={"active": True},
            new_value={"active": False},
            comment=f"Owner deactivated reference model #{ref.id} ({ref.canonical_name})"
        )
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
    db.flush()

    log_audit(
        db=db,
        entity_type="product_reference_alias",
        entity_id=new_alias.id,
        action="create",
        new_value={"reference_model_id": model_id, "alias": alias_clean, "normalized_alias": norm},
        comment=f"Owner added alias '{alias_clean}' to reference model #{model_id}"
    )

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

    log_audit(
        db=db,
        entity_type="product_reference_alias",
        entity_id=alias_id,
        action="delete",
        old_value={"reference_model_id": model_id, "alias": alias_obj.alias},
        comment=f"Owner deleted alias #{alias_id} from reference model #{model_id}"
    )

    db.delete(alias_obj)
    db.commit()
    return {"deleted": True, "alias_id": alias_id}


@router.patch("/models/{model_id}/aliases/{alias_id}", response_model=schemas.ProductReferenceAlias, dependencies=[Depends(verify_owner_access)])
def update_alias(model_id: int, alias_id: int, payload: schemas.ProductReferenceAliasUpdate, db: Session = Depends(get_db)):
    """Update an alias (OWNER-only). Allows activating/deactivating, changing priority or text."""
    alias_obj = db.query(models.ProductReferenceAlias).filter(
        models.ProductReferenceAlias.id == alias_id,
        models.ProductReferenceAlias.reference_model_id == model_id,
    ).first()
    if not alias_obj:
        raise HTTPException(status_code=404, detail="Alias not found")

    old_val = {"alias": alias_obj.alias, "active": alias_obj.active, "priority": alias_obj.priority}

    if payload.alias is not None:
        alias_clean = payload.alias.strip()
        norm = normalize_for_matching(alias_clean)
        if norm:
            alias_obj.alias = alias_clean
            alias_obj.normalized_alias = norm
    if payload.active is not None:
        alias_obj.active = payload.active
    if payload.priority is not None:
        alias_obj.priority = payload.priority

    log_audit(
        db=db,
        entity_type="product_reference_alias",
        entity_id=alias_id,
        action="update",
        old_value=old_val,
        new_value={"alias": alias_obj.alias, "active": alias_obj.active, "priority": alias_obj.priority},
        comment=f"Owner updated alias #{alias_id} for reference model #{model_id}"
    )

    db.commit()
    db.refresh(alias_obj)
    return alias_obj


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


@router.post("/products/{product_id}/link", dependencies=[Depends(verify_owner_access)])
def link_product_to_reference(
    product_id: int,
    payload: schemas.ProductReferenceLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Manually link a product to a confirmed reference model (OWNER-only).
    Optionally applies canonical Safe Enrichment (existing values win, category 52 preserved).
    Logs audit with before/after.
    """
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == payload.reference_model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    old_ref_id = prod.reference_model_id
    old_method = prod.reference_match_method

    now = datetime.datetime.now(datetime.timezone.utc)
    prod.reference_model_id = ref.id
    prod.reference_match_method = "manual_owner"
    prod.reference_match_confidence = 1.0
    prod.reference_enriched_at = now

    enrichment_result = None
    if payload.apply_enrichment:
        enrichment_result = enrich_product_from_reference(
            db=db,
            product=prod,
            reference=ref,
            method="manual_owner",
            confidence=1.0,
            apply=True,
        )

    log_audit(
        db=db,
        entity_type="product",
        entity_id=prod.id,
        action="link_reference",
        old_value={"reference_model_id": old_ref_id, "reference_match_method": old_method},
        new_value={
            "reference_model_id": ref.id,
            "reference_match_method": "manual_owner",
            "applied_enrichment": payload.apply_enrichment,
            "fields_filled": enrichment_result.get("fields_filled", {}) if enrichment_result else {}
        },
        comment=f"Owner manually linked product #{prod.id} to reference model #{ref.id} ({ref.canonical_name})"
    )

    db.commit()
    db.refresh(prod)

    return {
        "success": True,
        "product_id": prod.id,
        "reference_model_id": ref.id,
        "canonical_name": ref.canonical_name,
        "applied_enrichment": payload.apply_enrichment,
        "enrichment": enrichment_result,
    }


@router.post("/products/{product_id}/unlink", dependencies=[Depends(verify_owner_access)])
def unlink_product_from_reference(
    product_id: int,
    reason: Optional[str] = Query("rejected_by_owner"),
    db: Session = Depends(get_db)
):
    """
    Unlink a product from its reference model / reject wrong reference match (OWNER-only).
    Logs audit with before/after.
    """
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    old_ref_id = prod.reference_model_id
    old_method = prod.reference_match_method

    prod.reference_model_id = None
    prod.reference_match_method = reason or "rejected_by_owner"
    prod.reference_match_confidence = 0.0

    log_audit(
        db=db,
        entity_type="product",
        entity_id=prod.id,
        action="unlink_reference",
        old_value={"reference_model_id": old_ref_id, "reference_match_method": old_method},
        new_value={"reference_model_id": None, "reason": reason},
        comment=f"Owner unlinked product #{prod.id} from reference model #{old_ref_id} ({reason})"
    )

    db.commit()
    db.refresh(prod)

    return {
        "success": True,
        "product_id": prod.id,
        "reference_model_id": None,
        "status": "unlinked",
    }


@router.post("/products/{product_id}/enrich-apply", dependencies=[Depends(verify_owner_access)])
def enrich_apply_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Re-run canonical enrichment for a product with its linked reference model (OWNER-only).
    Existing product values win, category 52 strictly preserved.
    """
    prod = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if not prod.reference_model_id:
        raise HTTPException(status_code=400, detail="Product has no linked reference model")

    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == prod.reference_model_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Linked reference model not found")

    enrich_res = enrich_product_from_reference(
        db=db,
        product=prod,
        reference=ref,
        method=prod.reference_match_method or "manual_owner",
        confidence=prod.reference_match_confidence or 1.0,
        apply=True,
    )

    log_audit(
        db=db,
        entity_type="product",
        entity_id=prod.id,
        action="re_enrich_product",
        new_value={"fields_filled": enrich_res.get("fields_filled", {})},
        comment=f"Owner re-applied canonical enrichment for product #{prod.id} from ref #{ref.id}"
    )

    db.commit()
    return enrich_res


@router.get("/review-queue", response_model=schemas.ProductReferenceReviewQueueResponse)
def get_review_queue(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve review queue and conflict items for Owner UI (Section 5).
    - Unresolved products without reference_model_id, with candidate suggestions;
    - Known/external conflicts (from EXTERNAL_ENRICHMENT_CONFLICTS.json);
    - Aggregated catalog coverage summary metrics.
    """
    unresolved_query = db.query(models.Product).filter(
        models.Product.reference_model_id.is_(None)
    )
    total_unresolved = unresolved_query.count()
    unresolved_items = unresolved_query.order_by(models.Product.id.asc()).offset(offset).limit(limit).all()

    queue_products = []
    for p in unresolved_items:
        cands = find_reference_candidates(db=db, title=p.title, active_only=True)
        cand_list = [c.to_dict() for c in cands[:3]]

        queue_products.append(schemas.ProductReferenceReviewQueueItem(
            product_id=p.id,
            title=p.title,
            brand=p.brand,
            model=p.model,
            category_id=p.category_id,
            category_name=p.category.name if p.category else None,
            sale_price=float(p.sale_price) if p.sale_price is not None else None,
            status=p.status,
            candidates=cand_list,
        ))

    conflicts_list = []
    candidates_paths = [
        os.path.join(r"C:\tbootit\data", "reference_catalog", "EXTERNAL_ENRICHMENT_CONFLICTS.json"),
        r"C:\tboot-site\AntiGravity\PROMPT_WEB_07C_EXTERNAL_VERIFIED_REFERENCE_ENRICHMENT\Outbox\EXTERNAL_ENRICHMENT_CONFLICTS.json"
    ]
    for c_path in candidates_paths:
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    for c in c_data:
                        conflicts_list.append(schemas.ProductReferenceConflictItem(
                            stable_key=c.get("stable_key", ""),
                            canonical_name=c.get("canonical_name", ""),
                            status=c.get("status", "conflict"),
                            field=c.get("field", ""),
                            note=c.get("note", ""),
                            sources_compared=c.get("sources_compared", []),
                        ))
                    break
            except Exception:
                pass

    total_prods = db.query(models.Product).count()
    linked_prods = db.query(models.Product).filter(models.Product.reference_model_id.isnot(None)).count()
    total_models = db.query(models.ProductReferenceModel).count()

    all_models = db.query(models.ProductReferenceModel).all()
    verified_models = 0
    incomplete_models = 0
    for m in all_models:
        s_cnt = 0
        if m.specifications_json:
            try:
                s_dict = json.loads(m.specifications_json)
                s_cnt = len(s_dict)
            except Exception:
                pass
        if s_cnt >= 5:
            verified_models += 1
        else:
            incomplete_models += 1

    summary = {
        "total_products": total_prods,
        "linked_products": linked_prods,
        "unresolved_products": total_unresolved,
        "linked_percentage": round((linked_prods / total_prods * 100), 1) if total_prods else 0.0,
        "total_models": total_models,
        "verified_models": verified_models,
        "incomplete_models": incomplete_models,
        "conflicts_count": len(conflicts_list),
    }

    return schemas.ProductReferenceReviewQueueResponse(
        unresolved_products=queue_products,
        conflicts=conflicts_list,
        summary=summary,
    )


@router.post("/conflicts/resolve", dependencies=[Depends(verify_owner_access)])
def resolve_reference_conflict(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Manually resolve a specification conflict for a model (OWNER-only).
    Payload: {"stable_key": str, "field": str, "resolved_value": Any, "note": Optional[str]}
    """
    stable_key = payload.get("stable_key")
    if not stable_key:
        raise HTTPException(status_code=400, detail="stable_key is required")

    ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.stable_key == stable_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference model not found")

    field = payload.get("field")
    resolved_val = payload.get("resolved_value")
    note = payload.get("note", "")

    specs = {}
    if ref.specifications_json:
        try:
            specs = json.loads(ref.specifications_json)
        except Exception:
            specs = {}

    old_val = specs.get(field)
    if field and resolved_val is not None:
        specs[field] = resolved_val
        ref.specifications_json = json.dumps(specs, ensure_ascii=False)

    now = datetime.datetime.now(datetime.timezone.utc)
    ref.source_note = f"{ref.source_note or ''} | Conflict on '{field}' resolved manually by owner: {note} ({now.strftime('%Y-%m-%d')})".strip(" |")
    ref.updated_at = now

    log_audit(
        db=db,
        entity_type="product_reference_model",
        entity_id=ref.id,
        action="resolve_conflict",
        old_value={"field": field, "value": old_val},
        new_value={"field": field, "value": resolved_val, "note": note},
        comment=f"Owner resolved conflict for model #{ref.id} ({ref.canonical_name}): {field} = {resolved_val}"
    )

    db.commit()
    db.refresh(ref)

    # Update conflict file on disk if found
    for c_path in CONFLICTS_FILE_PATHS:
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                updated = False
                for c in c_data:
                    if c.get("stable_key") == stable_key and (not field or c.get("field") == field):
                        c["status"] = "resolved_manual_owner"
                        c["resolved_value"] = resolved_val
                        c["resolved_note"] = note
                        c["resolved_at"] = now.isoformat()
                        updated = True
                if updated:
                    with open(c_path, "w", encoding="utf-8") as f:
                        json.dump(c_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            break

    return {
        "success": True,
        "model_id": ref.id,
        "canonical_name": ref.canonical_name,
        "field": field,
        "resolved_value": resolved_val,
    }


@public_router.get("/search", response_model=schemas.ProductReferenceSearchResponse)
@public_router_plural.get("/search", response_model=schemas.ProductReferenceSearchResponse)
def search_reference_models(
    q: str = Query(..., min_length=1, description="Search query (model name, OCR text, alias)"),
    limit: int = Query(10, ge=1, le=50),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Search reference catalog for matching models using 3-tier deterministic matcher.
    Per Section 7 of TR_Stage05A:
    - Returns ranked candidates with confidence.
    - High confidence (>=0.90) may preselect.
    - Medium confidence shows choices.
    - Low confidence does not silently select.
    """
    candidates = find_reference_candidates(db=db, title=q, active_only=active_only)

    results: List[schemas.ProductReferenceSearchItem] = []
    for cand in candidates[:limit]:
        ref = db.query(models.ProductReferenceModel).filter(models.ProductReferenceModel.id == cand.reference_model_id).first()
        if not ref:
            continue

        # Count prior products in store
        prior_q = db.query(models.Product).filter(models.Product.reference_model_id == ref.id)
        prior_count = prior_q.count()
        prior_sample = None
        if prior_count > 0:
            latest_p = prior_q.order_by(models.Product.id.desc()).first()
            if latest_p:
                prior_sample = {
                    "id": latest_p.id,
                    "title": latest_p.title,
                    "sale_price": latest_p.sale_price,
                    "condition": latest_p.condition
                }

        specs_dict = {}
        if ref.specifications_json:
            try:
                specs_dict = json.loads(ref.specifications_json)
            except Exception:
                specs_dict = {}

        desc_preview = None
        if ref.site_description:
            desc_preview = ref.site_description[:250] + "..." if len(ref.site_description) > 250 else ref.site_description

        cat_name = ref.default_category.name if ref.default_category else None

        results.append(schemas.ProductReferenceSearchItem(
            reference_model_id=ref.id,
            canonical_name=ref.canonical_name,
            brand=ref.brand,
            model=ref.model,
            device_type=ref.device_type,
            category_id=ref.default_category_id,
            category_name=cat_name,
            confidence=cand.confidence,
            tier=cand.tier,
            matched_string=cand.matched_term,
            description_preview=desc_preview,
            specifications=specs_dict,
            verification_state=getattr(ref, "verification_state", "verified") or "verified",
            prior_products_count=prior_count,
            prior_product_sample=prior_sample
        ))

    return schemas.ProductReferenceSearchResponse(
        query=q,
        total_candidates=len(results),
        candidates=results
    )


@public_router.post("/ai-assist", response_model=schemas.AiAssistResponse)
@public_router_plural.post("/ai-assist", response_model=schemas.AiAssistResponse)
async def ai_assist_model(
    payload: schemas.AiAssistRequest,
    db: Session = Depends(get_db)
):
    """
    Server-side AI assistant fallback for identifying unknown models and extracting structured specs.
    Per Section 9, 10, 12, 13:
    - Credentials server-side only;
    - Returns STRICT structured JSON candidate;
    - Returns graceful fallback when AI is disabled.
    """
    provider = get_ai_provider()
    result = await provider.identify_model(
        query=payload.query,
        ocr_text=payload.ocr_text,
        category_hint=payload.category_hint
    )

    return schemas.AiAssistResponse(
        status=result.status,
        manufacturer=result.manufacturer,
        model=result.model,
        canonical_name=result.canonical_name,
        category=result.category,
        device_type=result.device_type,
        likely_aliases=result.likely_aliases,
        proposed_structured_specs=result.proposed_structured_specs,
        proposed_reusable_description=result.proposed_reusable_description,
        confidence=result.confidence,
        missing_uncertain_fields=result.missing_uncertain_fields,
        source_provenance=result.source_provenance,
        source_urls=result.source_urls,
        message=result.message
    )


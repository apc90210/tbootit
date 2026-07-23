import random
from sqlalchemy.orm import Session
from app import models
from app.routers.customers import log_audit

PREFIX = "200"

def generate_unique_barcode(db: Session) -> str:
    """Generate a unique 12-digit barcode starting with '200'."""
    max_id = db.query(models.Product.id).order_by(models.Product.id.desc()).first()
    seq = (max_id[0] if max_id else 0) + 1
    
    while True:
        # 12 digits: 200 + 9 digits
        candidate = f"{PREFIX}{seq:09d}"
        existing = db.query(models.Product).filter(models.Product.barcode == candidate).first()
        if not existing:
            return candidate
        seq += 1

def generate_barcode_for_product(db: Session, product: models.Product, actor: str = "system") -> dict:
    """Generate barcode for a single product if it doesn't have one."""
    if product.barcode and product.barcode.strip():
        return {
            "product_id": product.id,
            "barcode": product.barcode,
            "generated": False
        }
    
    new_barcode = generate_unique_barcode(db)
    product.barcode = new_barcode
    
    # Audit log
    log_audit(
        db=db,
        entity_type="product",
        entity_id=product.id,
        action="barcode_generated",
        new_value={"barcode": new_barcode},
        comment=f"actor:{actor}"
    )
    
    db.commit()
    db.refresh(product)
    
    return {
        "product_id": product.id,
        "barcode": new_barcode,
        "generated": True
    }

def generate_missing_barcodes(db: Session, actor: str = "system") -> dict:
    """Generate barcodes for all products that lack a barcode."""
    products = db.query(models.Product).filter(
        (models.Product.barcode == None) | (models.Product.barcode == "")
    ).all()
    
    processed = len(products)
    generated = 0
    skipped = 0
    errors = []
    
    for prod in products:
        try:
            if not prod.barcode or not prod.barcode.strip():
                new_bc = generate_unique_barcode(db)
                prod.barcode = new_bc
                generated += 1
                log_audit(
                    db=db,
                    entity_type="product",
                    entity_id=prod.id,
                    action="barcode_bulk_generated",
                    new_value={"barcode": new_bc},
                    comment=f"actor:{actor}"
                )
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"Product {prod.id}: {str(e)}")
            
    db.commit()
    
    return {
        "processed": processed,
        "generated": generated,
        "skipped_existing": skipped,
        "errors": errors
    }

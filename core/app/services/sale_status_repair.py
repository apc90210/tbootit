import logging
from sqlalchemy.orm import Session
from app import models
from app.routers.customers import log_audit

logger = logging.getLogger(__name__)

def normalize_misclassified_reissued_sales(db: Session) -> int:
    """
    Idempotent normalization for legacy misclassified reissued sales.
    Any sale with source_sale_id IS NOT NULL and status == 'completed'
    is updated to status = 'reissued'.
    Returns the number of rows updated.
    """
    misclassified = db.query(models.Sale).filter(
        models.Sale.source_sale_id.isnot(None),
        models.Sale.status == "completed"
    ).all()
    
    updated_count = len(misclassified)
    if updated_count > 0:
        logger.info(f"[Migration] Normalizing {updated_count} misclassified reissued sales from 'completed' to 'reissued'")
        for sale in misclassified:
            old_s = sale.status
            sale.status = "reissued"
            log_audit(
                db=db,
                entity_type="sale",
                entity_id=sale.id,
                action="status_normalized",
                old_value={"status": old_s},
                new_value={"status": "reissued", "source_sale_id": sale.source_sale_id},
                comment="Legacy reissued sale status normalization from completed to reissued"
            )
        db.commit()
    else:
        logger.info("[Migration] 0 misclassified reissued sales found. Live DB is clean.")
    return updated_count

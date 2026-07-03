from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.defaults import default_organization_settings_payload, is_blank

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/organization", response_model=schemas.OrganizationSettingsResponse)
def get_organization_settings(db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    defaults = default_organization_settings_payload()
    
    if not settings:
        settings = models.OrganizationSettings(**defaults)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    else:
        # Backfill any blank fields and normalize texts
        from app.defaults import normalize_multiline_text
        changed = False
        for key, default_value in defaults.items():
            current_value = getattr(settings, key)
            if is_blank(current_value):
                setattr(settings, key, default_value)
                changed = True
            elif key in ["warranty_text", "no_warranty_text"]:
                normalized = normalize_multiline_text(current_value)
                if normalized != current_value:
                    setattr(settings, key, normalized)
                    changed = True
        
        if changed:
            db.commit()
            db.refresh(settings)
            
    return settings

@router.put("/organization", response_model=schemas.OrganizationSettingsResponse)
def update_organization_settings(settings_data: schemas.OrganizationSettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    defaults = default_organization_settings_payload()
    
    if not settings:
        settings = models.OrganizationSettings(**defaults)
        db.add(settings)
    
    update_data = settings_data.model_dump(exclude_unset=True)
    from app.defaults import normalize_multiline_text
    for key, value in update_data.items():
        if key in ["warranty_text", "no_warranty_text"]:
            value = normalize_multiline_text(value)
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

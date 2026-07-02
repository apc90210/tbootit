from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/organization", response_model=schemas.OrganizationSettingsResponse)
def get_organization_settings(db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    if not settings:
        # Return default values if not found, though seeding should prevent this
        return schemas.OrganizationSettingsResponse(
            id=0,
            organization_name="Название не задано",
            inn="ИНН не задан",
            address="Адрес не задан",
            phone="Телефон не задан",
            default_customer_label="Частное лицо"
        )
    return settings

@router.put("/organization", response_model=schemas.OrganizationSettingsResponse)
def update_organization_settings(settings_data: schemas.OrganizationSettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

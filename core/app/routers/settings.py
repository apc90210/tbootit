from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/organization", response_model=schemas.OrganizationSettingsResponse)
def get_organization_settings(db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    if not settings:
        settings = models.OrganizationSettings(
            organization_name="ИП Атанов Павел Сергеевич",
            inn="667009336901",
            address="Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10",
            phone="+7 343 344 88 95",
            default_customer_label="Частное лицо",
            warranty_text="На все Б/У товары предоставляется гарантия 30 дней.\nГарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения дефекта товара в течении 30 дней с даты продажи.\nТовар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен.\nНа программное обеспечение и расходные материалы гарантия не предоставляется.\nВ случае обнаружения неисправности – товар сдается на диагностику. По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики.",
            no_warranty_text="Товар продаётся без гарантии, в том состоянии, в котором есть.\nПокупатель внимательно осмотрел товар при покупке."
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/organization", response_model=schemas.OrganizationSettingsResponse)
def update_organization_settings(settings_data: schemas.OrganizationSettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(models.OrganizationSettings).first()
    if not settings:
        settings = models.OrganizationSettings(
            organization_name="ИП Атанов Павел Сергеевич",
            inn="667009336901",
            address="Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10",
            phone="+7 343 344 88 95",
            default_customer_label="Частное лицо",
            warranty_text="На все Б/У товары предоставляется гарантия 30 дней.\nГарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения дефекта товара в течении 30 дней с даты продажи.\nТовар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен.\nНа программное обеспечение и расходные материалы гарантия не предоставляется.\nВ случае обнаружения неисправности – товар сдается на диагностику. По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики.",
            no_warranty_text="Товар продаётся без гарантии, в том состоянии, в котором есть.\nПокупатель внимательно осмотрел товар при покупке."
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

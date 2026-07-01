from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
import json

router = APIRouter()

@router.get("/", response_model=List[schemas.RepairOrder])
def get_repairs(db: Session = Depends(get_db)):
    return db.query(models.RepairOrder).all()

@router.post("/", response_model=schemas.RepairOrder)
def create_repair(repair: schemas.RepairOrderCreate, db: Session = Depends(get_db)):
    db_repair = models.RepairOrder(**repair.model_dump())
    db.add(db_repair)
    db.commit()
    db.refresh(db_repair)
    
    log_audit(db, "repair_order", db_repair.id, "create", new_value=repair.model_dump())
    db.commit()
    return db_repair

@router.get("/{repair_id}", response_model=schemas.RepairOrder)
def get_repair(repair_id: int, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Repair order not found")
    return db_repair

@router.patch("/{repair_id}", response_model=schemas.RepairOrder)
def update_repair(repair_id: int, repair: schemas.RepairOrderUpdate, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Repair order not found")
    
    old_data = {c.name: getattr(db_repair, c.name) for c in db_repair.__table__.columns}
    update_data = repair.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_repair, key, value)
        
    db.commit()
    db.refresh(db_repair)
    
    new_data = {c.name: getattr(db_repair, c.name) for c in db_repair.__table__.columns}
    log_audit(db, "repair_order", db_repair.id, "update", old_value=old_data, new_value=new_data)
    db.commit()
    return db_repair

@router.patch("/{repair_id}/status", response_model=schemas.RepairOrder)
def update_repair_status(repair_id: int, status_update: schemas.RepairOrderStatusUpdate, db: Session = Depends(get_db)):
    db_repair = db.query(models.RepairOrder).filter(models.RepairOrder.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=404, detail="Repair order not found")
    
    old_status = db_repair.status
    db_repair.status = status_update.status
    if status_update.status in ["issued", "cancelled"]:
        db_repair.closed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_repair)
    
    log_audit(db, "repair_order", db_repair.id, "update_status", old_value={"status": old_status}, new_value={"status": status_update.status})
    db.commit()
    return db_repair

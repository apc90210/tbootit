from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    brand = Column(String, index=True)
    model = Column(String)
    serial_number = Column(String)
    condition = Column(String)
    description = Column(Text)
    purchase_price = Column(Float)
    sale_price = Column(Float)
    status = Column(String, default="draft", index=True)
    storage_location = Column(String)
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    min_price = Column(Float, nullable=True)
    market_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_published_site = Column(Integer, default=0)  # Boolean via int for sqlite
    is_published_avito = Column(Integer, default=0) # Boolean via int for sqlite
    site_title = Column(String, nullable=True)
    site_description = Column(Text, nullable=True)
    avito_title = Column(String, nullable=True)
    avito_description = Column(Text, nullable=True)
    avito_category_path = Column(Text, nullable=True)
    avito_goods_type = Column(String, nullable=True)
    avito_condition = Column(String, nullable=True)
    avito_params_json = Column(Text, nullable=True)
    avito_contact_name = Column(String, nullable=True)
    avito_phone = Column(String, nullable=True)
    avito_address = Column(String, nullable=True)
    avito_seller_type = Column(String, nullable=True)
    source_json = Column(Text, nullable=True)
    source_type = Column(String, nullable=True)
    last_imported_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductCardImport(Base):
    __tablename__ = "product_cards"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    source_type = Column(String)
    source_json = Column(Text)
    normalized_json = Column(Text, nullable=True)
    avito_json = Column(Text, nullable=True)
    validation_status = Column(String)
    validation_errors = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductEvent(Base):
    __tablename__ = "product_events"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    event_type = Column(String, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    movement_type = Column(String, index=True)
    quantity_delta = Column(Integer)
    old_quantity = Column(Integer)
    new_quantity = Column(Integer)
    reason = Column(String)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductPhoto(Base):
    __tablename__ = "product_photos"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    filename = Column(String)
    storage_path = Column(String)
    media_url = Column(String)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, index=True)
    email = Column(String, index=True)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RepairOrder(Base):
    __tablename__ = "repair_orders"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="received", index=True, nullable=False)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)

    device_type = Column(String, default="Устройство", nullable=True)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial_number = Column(String, index=True, nullable=True)

    reported_issue = Column(Text, nullable=True)
    completeness = Column(Text, nullable=True)
    appearance = Column(Text, nullable=True)
    customer_comment = Column(Text, nullable=True)
    internal_note = Column(Text, nullable=True)

    access_code_provided = Column(Boolean, default=False, nullable=False)

    assigned_to = Column(String, nullable=True)
    priority = Column(String, default="normal", nullable=False)
    diagnostic_fee = Column(Float, default=500.0, nullable=False)

    accepted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    # Legacy fields
    device_title = Column(String, nullable=True)
    device_serial = Column(String, nullable=True)
    problem_description = Column(Text, nullable=True)
    diagnostics_result = Column(Text, nullable=True)
    work_description = Column(Text, nullable=True)
    parts_description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)

    history = relationship("RepairStatusHistory", back_populates="repair", order_by="RepairStatusHistory.changed_at.asc()")

from sqlalchemy import event
import datetime

@event.listens_for(RepairOrder, 'before_insert')
def repair_order_before_insert(mapper, connection, target):
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y%m%d")
    if not target.number:
        import random
        rnd = random.randint(1000, 9999)
        target.number = f"R-{date_str}-{rnd}"
    if not target.customer_name:
        target.customer_name = f"Клиент #{target.customer_id or 1}"
    if not target.customer_phone:
        target.customer_phone = "+7 000 000-00-00"
    if not target.device_type:
        target.device_type = target.device_title or "Устройство"
    if not target.reported_issue:
        target.reported_issue = target.problem_description or "Заявка на ремонт"

class RepairStatusHistory(Base):
    __tablename__ = "repair_status_history"
    id = Column(Integer, primary_key=True, index=True)
    repair_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    repair = relationship("RepairOrder", back_populates="history")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    total_amount = Column(Float)
    payment_method = Column(String)
    comment = Column(Text)
    status = Column(String, default="completed", index=True)
    warranty_days = Column(Integer, nullable=True)
    warranty_enabled = Column(Integer, default=1)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(Text, nullable=True)
    canceled_by = Column(String, nullable=True)
    original_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    replaced_by_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    source_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    superseded_by_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    reissued_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    title = Column(String)
    price = Column(Float)
    quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sale = relationship("Sale", back_populates="items")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, index=True)
    entity_id = Column(Integer, index=True)
    action = Column(String)
    old_value = Column(Text)
    new_value = Column(Text)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OrganizationSettings(Base):
    __tablename__ = "organization_settings"
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String)
    inn = Column(String)
    address = Column(String)
    phone = Column(String)
    default_cashier_name = Column(String, nullable=True)
    default_customer_label = Column(String, default="Частное лицо")
    warranty_text = Column(Text, nullable=True)
    no_warranty_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

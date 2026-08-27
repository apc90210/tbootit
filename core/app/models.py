from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, UniqueConstraint
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

class AvitoCategory(Base):
    __tablename__ = "avito_categories"
    id = Column(Integer, primary_key=True, index=True)
    external_category_id = Column(String, index=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    parent_external_category_id = Column(String, nullable=True)
    path = Column(Text, nullable=True)
    source = Column(String, default="avito", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    observed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    definitions = relationship("AvitoAttributeDefinition", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="avito_category")

class AvitoAttributeDefinition(Base):
    __tablename__ = "avito_attribute_definitions"
    __table_args__ = (
        UniqueConstraint("category_id", "external_key", name="uix_avito_attr_category_key"),
    )
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("avito_categories.id"), nullable=False, index=True)
    external_key = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default="string", nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    multiple = Column(Boolean, default=False, nullable=False)
    unit = Column(String, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    observed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("AvitoCategory", back_populates="definitions")
    options = relationship("AvitoAttributeOption", back_populates="definition", cascade="all, delete-orphan")
    product_values = relationship("ProductAvitoAttributeValue", back_populates="definition", cascade="all, delete-orphan")

class AvitoAttributeOption(Base):
    __tablename__ = "avito_attribute_options"
    __table_args__ = (
        UniqueConstraint("attribute_definition_id", "value", name="uix_avito_option_attr_val"),
    )
    id = Column(Integer, primary_key=True, index=True)
    attribute_definition_id = Column(Integer, ForeignKey("avito_attribute_definitions.id"), nullable=False, index=True)
    external_option_id = Column(String, nullable=True)
    value = Column(String, nullable=False)
    label = Column(String, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    definition = relationship("AvitoAttributeDefinition", back_populates="options")

class ProductAvitoAttributeValue(Base):
    __tablename__ = "product_avito_attribute_values"
    __table_args__ = (
        UniqueConstraint("product_id", "attribute_definition_id", name="uix_prod_avito_attr_val"),
    )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    attribute_definition_id = Column(Integer, ForeignKey("avito_attribute_definitions.id"), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("avito_attribute_options.id"), nullable=True, index=True)
    value = Column(Text, nullable=True)
    raw_value = Column(Text, nullable=True)
    source = Column(String, default="avito", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="avito_attribute_values")
    definition = relationship("AvitoAttributeDefinition", back_populates="product_values")
    option = relationship("AvitoAttributeOption")

class AvitoCanonicalCategory(Base):
    __tablename__ = "avito_canonical_categories"
    id = Column(Integer, primary_key=True, index=True)
    internal_key = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, index=True, nullable=False)
    observed_category_id = Column(Integer, ForeignKey("avito_categories.id"), nullable=True, index=True)
    official_slug = Column(String, nullable=True, index=True)
    official_source = Column(String, nullable=True)
    capability_source = Column(String, default="observed", nullable=False)  # observed, official_api, manual
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    observed_category = relationship("AvitoCategory", foreign_keys=[observed_category_id])
    fields = relationship("AvitoCanonicalField", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="canonical_category")

class AvitoCanonicalField(Base):
    __tablename__ = "avito_canonical_fields"
    __table_args__ = (
        UniqueConstraint("category_id", "internal_key", name="uix_avito_canonical_field_cat_key"),
    )
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("avito_canonical_categories.id"), nullable=False, index=True)
    internal_key = Column(String, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    official_tag = Column(String, nullable=True, index=True)
    official_source = Column(String, nullable=True)
    data_type = Column(String, nullable=True)  # string, integer, float
    field_type = Column(String, nullable=True)  # input, select, checkbox
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("AvitoCanonicalCategory", back_populates="fields")
    rules = relationship("AvitoCanonicalFieldRule", back_populates="field", cascade="all, delete-orphan")
    values = relationship("AvitoCanonicalFieldValue", back_populates="field", cascade="all, delete-orphan")
    mappings = relationship("AvitoObservedFieldMapping", back_populates="canonical_field")

class AvitoCanonicalFieldRule(Base):
    __tablename__ = "avito_canonical_field_rules"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("avito_canonical_fields.id"), nullable=False, index=True)
    ordinal = Column(Integer, default=0, nullable=False)
    rule_source = Column(String, default="official_api", nullable=False)  # official_api, manual, inferred_disabled
    required = Column(Boolean, nullable=True)
    required_by_dependency = Column(Boolean, nullable=True)
    dependencies_json = Column(Text, nullable=True)
    values_range_json = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    field = relationship("AvitoCanonicalField", back_populates="rules")
    values = relationship("AvitoCanonicalFieldValue", back_populates="rule")

class AvitoCanonicalFieldValue(Base):
    __tablename__ = "avito_canonical_field_values"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("avito_canonical_fields.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("avito_canonical_field_rules.id"), nullable=True, index=True)
    value = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    official_value = Column(String, nullable=True)
    source = Column(String, default="inline", nullable=False)  # inline, linked_json, manual, observed
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    field = relationship("AvitoCanonicalField", back_populates="values")
    rule = relationship("AvitoCanonicalFieldRule", back_populates="values")

class AvitoObservedFieldMapping(Base):
    __tablename__ = "avito_observed_field_mappings"
    __table_args__ = (
        UniqueConstraint("category_id", "observed_name_normalized", name="uix_avito_observed_mapping_cat_name"),
    )
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("avito_categories.id"), nullable=False, index=True)
    observed_name = Column(String, nullable=False)
    observed_name_normalized = Column(String, index=True, nullable=False)
    canonical_field_id = Column(Integer, ForeignKey("avito_canonical_fields.id"), nullable=True, index=True)
    mapping_source = Column(String, default="exact_label", nullable=False)  # exact_label, manual, official_tag_match
    confidence = Column(Float, default=1.0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    observed_category = relationship("AvitoCategory")
    canonical_field = relationship("AvitoCanonicalField", back_populates="mappings")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    avito_category_id = Column(Integer, ForeignKey("avito_categories.id"), nullable=True, index=True)
    canonical_category_id = Column(Integer, ForeignKey("avito_canonical_categories.id"), nullable=True, index=True)
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
    source_origin = Column(String, nullable=True, default="manual")
    source_attributes_json = Column(Text, nullable=True)
    last_imported_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category")
    external_listings = relationship("ProductExternalListing", back_populates="product", cascade="all, delete-orphan")
    avito_category = relationship("AvitoCategory", back_populates="products")
    canonical_category = relationship("AvitoCanonicalCategory", back_populates="products")
    avito_attribute_values = relationship("ProductAvitoAttributeValue", back_populates="product", cascade="all, delete-orphan")
    photos = relationship("ProductPhoto", back_populates="product", cascade="all, delete-orphan")

class ProductExternalListing(Base):
    __tablename__ = "product_external_listings"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    marketplace = Column(String, default="avito", index=True, nullable=False)
    external_account_key = Column(String, index=True, nullable=False)
    external_item_id = Column(String, index=True, nullable=False)
    external_url = Column(String, nullable=True)
    remote_status = Column(String, default="active", index=True, nullable=False)
    remote_status_raw = Column(String, nullable=True)
    source_title = Column(String, nullable=True)
    source_price = Column(Float, nullable=True)
    source_attributes_json = Column(Text, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_imported_at = Column(DateTime(timezone=True), nullable=True)
    last_pushed_at = Column(DateTime(timezone=True), nullable=True)
    sync_state = Column(String, default="synced", nullable=False)
    sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="external_listings")

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
    source_url = Column(String, nullable=True)
    content_hash = Column(String, nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="photos")

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
    diagnostic_fee = Column(Integer, default=500, nullable=False)

    # Stage05B Simple Diagnosis and Manual Estimate
    diagnosis_text = Column(Text, nullable=True)
    planned_works_text = Column(Text, nullable=True)
    planned_parts_text = Column(Text, nullable=True)
    estimated_repair_amount = Column(Integer, nullable=True)

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
    source_type = Column(String, nullable=True, index=True)
    source_id = Column(Integer, nullable=True, index=True)
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
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
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

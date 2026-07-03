from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    sku: str
    title: str
    category_id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    status: Optional[str] = "draft"
    storage_location: Optional[str] = None
    quantity: Optional[int] = 0
    reserved_quantity: Optional[int] = 0
    min_price: Optional[float] = None
    market_price: Optional[float] = None
    notes: Optional[str] = None
    is_published_site: Optional[int] = 0
    is_published_avito: Optional[int] = 0
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    avito_title: Optional[str] = None
    avito_description: Optional[str] = None
    avito_category_path: Optional[str] = None
    avito_goods_type: Optional[str] = None
    avito_condition: Optional[str] = None
    avito_params_json: Optional[str] = None
    avito_contact_name: Optional[str] = None
    avito_phone: Optional[str] = None
    avito_address: Optional[str] = None
    avito_seller_type: Optional[str] = None
    source_json: Optional[str] = None
    source_type: Optional[str] = None
    last_imported_at: Optional[datetime] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    status: Optional[str] = None
    storage_location: Optional[str] = None
    quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    min_price: Optional[float] = None
    market_price: Optional[float] = None
    notes: Optional[str] = None

class ProductStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

class Product(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    items: List[Product]
    total: int
    limit: int
    offset: int

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    comment: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    comment: Optional[str] = None

class Customer(CustomerBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Repair Schemas
class RepairOrderBase(BaseModel):
    customer_id: int
    device_title: str
    device_serial: Optional[str] = None
    problem_description: str
    diagnostics_result: Optional[str] = None
    work_description: Optional[str] = None
    parts_description: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = "new"

class RepairOrderCreate(RepairOrderBase):
    pass

class RepairOrderUpdate(BaseModel):
    device_title: Optional[str] = None
    device_serial: Optional[str] = None
    problem_description: Optional[str] = None
    diagnostics_result: Optional[str] = None
    work_description: Optional[str] = None
    parts_description: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None

class RepairOrderStatusUpdate(BaseModel):
    status: str

class RepairOrder(RepairOrderBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Sale Schemas
class SaleItemBase(BaseModel):
    product_id: int
    title: str
    price: float
    quantity: int

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    id: int
    sale_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    customer_id: Optional[int] = None
    total_amount: float
    payment_method: Optional[str] = "cash"
    comment: Optional[str] = None
    warranty_days: Optional[int] = 30
    warranty_enabled: Optional[bool] = True

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class SaleCancel(BaseModel):
    reason: str

class Sale(SaleBase):
    id: int
    status: str
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[SaleItem] = []
    class Config:
        from_attributes = True

class SaleListResponse(BaseModel):
    items: List[Sale]
    total: int
    limit: int
    offset: int

# Photo Schemas
class ProductPhoto(BaseModel):
    id: int
    product_id: int
    filename: str
    media_url: str
    sort_order: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ProductEventBase(BaseModel):
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None

class ProductEventCreate(ProductEventBase):
    pass

class ProductEvent(ProductEventBase):
    id: int
    product_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class StockMovementBase(BaseModel):
    movement_type: str
    quantity_delta: int
    old_quantity: int
    new_quantity: int
    reason: str
    comment: Optional[str] = None

class StockMovement(StockMovementBase):
    id: int
    product_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class StockAdjustment(BaseModel):
    quantity_delta: int
    reason: str
    comment: Optional[str] = None

class SitePublication(BaseModel):
    is_published_site: int
    site_title: Optional[str] = None
    site_description: Optional[str] = None

class AvitoPublication(BaseModel):
    is_published_avito: int
    avito_title: Optional[str] = None
    avito_description: Optional[str] = None

class ProductDetails(Product):
    margin: Optional[float] = None
    available_quantity: int = 0
    has_photos: bool = False
    photos: List[ProductPhoto] = []
    events: List[ProductEvent] = []
    stock_movements: List[StockMovement] = []
    avito_ready: bool = False
    site_ready: bool = False
    class Config:
        from_attributes = True

class ProductCardImportSchema(BaseModel):
    id: int
    product_id: Optional[int] = None
    source_type: str
    source_json: str
    normalized_json: Optional[str] = None
    avito_json: Optional[str] = None
    validation_status: str
    validation_errors: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ChatGPT Payload Schemas
class ImportProductSection(BaseModel):
    sku: str
    title: str
    category_path: Optional[List[str]] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    min_price: Optional[float] = None
    market_price: Optional[float] = None
    quantity: Optional[int] = 0
    storage_location: Optional[str] = None
    notes: Optional[str] = None

class ImportAvitoSection(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_path: Optional[List[str]] = None
    goods_type: Optional[str] = None
    condition: Optional[str] = None
    price: Optional[float] = None
    seller_type: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    parameters: Optional[dict] = None
    photos: Optional[List[str]] = None

class ImportSiteSection(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    publish_ready: Optional[bool] = False

class ProductCardJSONPayload(BaseModel):
    source: str
    schema_version: str
    operation: str
    product: ImportProductSection
    avito: Optional[ImportAvitoSection] = None
    site: Optional[ImportSiteSection] = None

# Organization Settings Schemas
class OrganizationSettingsBase(BaseModel):
    organization_name: str
    inn: str
    address: str
    phone: str
    default_cashier_name: Optional[str] = None
    default_customer_label: Optional[str] = "Частное лицо"
    warranty_text: Optional[str] = None
    no_warranty_text: Optional[str] = None

class OrganizationSettingsCreate(OrganizationSettingsBase):
    pass

class OrganizationSettingsUpdate(BaseModel):
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    default_cashier_name: Optional[str] = None
    default_customer_label: Optional[str] = None
    warranty_text: Optional[str] = None
    no_warranty_text: Optional[str] = None

class OrganizationSettingsResponse(OrganizationSettingsBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

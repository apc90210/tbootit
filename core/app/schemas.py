from pydantic import BaseModel, field_validator
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
    barcode: Optional[str] = None
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
    storage_location: Optional[str] = "store"
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
    
    @field_validator("storage_location", mode="before")
    def set_default_location(cls, v):
        return v if v else "store"

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    barcode: Optional[str] = None
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

class BarcodeGenerateResponse(BaseModel):
    product_id: int
    barcode: str
    generated: bool

class BarcodeBulkGenerateResponse(BaseModel):
    processed: int
    generated: int
    skipped_existing: int
    errors: List[str] = []

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
    linked_sale_id: Optional[int] = None
    class Config:
        from_attributes = True

# Sale Schemas
class SaleItemBase(BaseModel):
    product_id: Optional[int] = None
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
    total_amount: Optional[float] = None
    payment_method: Optional[str] = "cash"
    comment: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    warranty_days: Optional[int] = 30
    warranty_enabled: Optional[bool] = True

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class SaleCancel(BaseModel):
    reason: str
    canceled_by: Optional[str] = "Администратор"

class Sale(SaleBase):
    id: int
    status: str
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    canceled_by: Optional[str] = None
    original_sale_id: Optional[int] = None
    replaced_by_sale_id: Optional[int] = None
    source_sale_id: Optional[int] = None
    superseded_by_sale_id: Optional[int] = None
    reissued_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    items: List[SaleItem] = []
    class Config:
        from_attributes = True

class SaleReissue(BaseModel):
    reason: str
    payment_method: Optional[str] = "cash"
    items: List[SaleItemCreate]

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
    avito_category_name: Optional[str] = None
    avito_characteristics: Optional[dict] = None
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

class PaymentBreakdown(BaseModel):
    payment_method: str
    label: str
    amount: float
    sales_count: int

class ReportSaleItem(BaseModel):
    id: int
    created_at: datetime
    total_amount: float
    items_count: int
    payment_method: str
    payment_method_label: str
    comment: Optional[str] = None

class MoneySummary(BaseModel):
    cash: float = 0.0
    card: float = 0.0
    transfer: float = 0.0
    sbp: float = 0.0
    legal_entity_account: float = 0.0
    other: float = 0.0
    unspecified: float = 0.0
    total: float = 0.0

class MoneySummaryRow(MoneySummary):
    period_key: str
    label: str

class SalesReportResponse(BaseModel):
    period: str
    date_from: str
    date_to: str
    total_amount: float
    sales_count: int
    items_count: int
    payment_breakdown: List[PaymentBreakdown]
    money_summary: MoneySummary = MoneySummary()
    money_summary_rows: List[MoneySummaryRow] = []
    money_summary_total: MoneySummary = MoneySummary()
    money_summary_granularity: str = "day"
    payment_labels: dict = {}
    sales: List[ReportSaleItem]

# Repair Order Constants and Schemas
REPAIR_STATUSES = {
    "received": "Принят",
    "diagnostics": "Диагностика",
    "waiting_customer": "Ожидает клиента",
    "waiting_parts": "Ожидает запчасти",
    "in_repair": "В ремонте",
    "ready": "Готов",
    "unrepairable": "Ремонт невозможен",
    "issued": "Выдан",
    "canceled": "Отменён"
}

REPAIR_PRIORITIES = {
    "normal": "Обычный",
    "urgent": "Срочный"
}

REPAIR_DEVICE_TYPES = [
    "Ноутбук",
    "Системный блок",
    "Моноблок",
    "Монитор",
    "Принтер",
    "МФУ",
    "Планшет",
    "Телефон",
    "Сетевое оборудование",
    "Комплектующее",
    "Другое"
]

class RepairStatusHistorySchema(BaseModel):
    id: int
    repair_id: int
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    changed_by: Optional[str] = None
    changed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RepairOrderBase(BaseModel):
    customer_id: Optional[int] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    device_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    reported_issue: str
    completeness: Optional[str] = None
    appearance: Optional[str] = None
    customer_comment: Optional[str] = None
    internal_note: Optional[str] = None
    access_code_provided: Optional[bool] = False
    assigned_to: Optional[str] = None
    priority: Optional[str] = "normal"
    diagnostic_fee: Optional[int] = 500
    diagnosis_text: Optional[str] = None
    planned_works_text: Optional[str] = None
    planned_parts_text: Optional[str] = None
    estimated_repair_amount: Optional[int] = None

    @field_validator("priority")
    def validate_priority(cls, v):
        if v is not None and v not in ["normal", "urgent"]:
            raise ValueError("Приоритет должен быть 'normal' или 'urgent'")
        return v or "normal"

    @field_validator("estimated_repair_amount", mode="before")
    def validate_estimated_repair_amount(cls, v):
        if v is None:
            return None
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
            val_int = int(v)
            if val_int < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return val_int
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return v
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                val = float(v)
                if not val.is_integer():
                    raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
                val_int = int(val)
                if val_int < 0:
                    raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
                return val_int
            except Exception:
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
        return v

    @field_validator("diagnostic_fee", mode="before")
    def validate_diagnostic_fee(cls, v):
        if v is None:
            return 500
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Стоимость диагностики должна быть целым числом")
            val_int = int(v)
            if val_int < 0:
                raise ValueError("Стоимость диагностики не может быть отрицательной")
            return val_int
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Стоимость диагностики не может быть отрицательной")
            return v
        if isinstance(v, str):
            if not v.strip():
                return 500
            try:
                val = float(v)
                if not val.is_integer():
                    raise ValueError("Стоимость диагностики должна быть целым числом")
                val_int = int(val)
                if val_int < 0:
                    raise ValueError("Стоимость диагностики не может быть отрицательной")
                return val_int
            except Exception:
                raise ValueError("Стоимость диагностики должна быть целым числом")
        return v

    @field_validator("customer_name", "customer_phone", "device_type", "reported_issue", mode="before")
    def validate_non_empty(cls, v, info):
        if v is None or not str(v).strip():
            field_labels = {
                "customer_name": "ФИО клиента",
                "customer_phone": "Телефон",
                "device_type": "Тип устройства",
                "reported_issue": "Заявленная неисправность"
            }
            label = field_labels.get(info.field_name, info.field_name)
            raise ValueError(f"Поле '{label}' обязательно для заполнения")
        return str(v).strip()

class RepairOrderCreate(RepairOrderBase):
    pass

class RepairOrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    reported_issue: Optional[str] = None
    completeness: Optional[str] = None
    appearance: Optional[str] = None
    customer_comment: Optional[str] = None
    internal_note: Optional[str] = None
    access_code_provided: Optional[bool] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    diagnostic_fee: Optional[int] = None
    diagnosis_text: Optional[str] = None
    planned_works_text: Optional[str] = None
    planned_parts_text: Optional[str] = None
    estimated_repair_amount: Optional[int] = None

    @field_validator("priority")
    def validate_priority_opt(cls, v):
        if v is not None and v not in ["normal", "urgent"]:
            raise ValueError("Приоритет должен быть 'normal' или 'urgent'")
        return v

    @field_validator("estimated_repair_amount", mode="before")
    def validate_estimated_repair_amount_opt(cls, v):
        if v is None:
            return None
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
            val_int = int(v)
            if val_int < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return val_int
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return v
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                val = float(v)
                if not val.is_integer():
                    raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
                val_int = int(val)
                if val_int < 0:
                    raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
                return val_int
            except Exception:
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
        return v

    @field_validator("diagnostic_fee", mode="before")
    def validate_diagnostic_fee_opt(cls, v):
        if v is None:
            return None
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Стоимость диагностики должна быть целым числом")
            val_int = int(v)
            if val_int < 0:
                raise ValueError("Стоимость диагностики не может быть отрицательной")
            return val_int
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Стоимость диагностики не может быть отрицательной")
            return v
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                val = float(v)
                if not val.is_integer():
                    raise ValueError("Стоимость диагностики должна быть целым числом")
                val_int = int(val)
                if val_int < 0:
                    raise ValueError("Стоимость диагностики не может быть отрицательной")
                return val_int
            except Exception:
                raise ValueError("Стоимость диагностики должна быть целым числом")
        return v

class RepairOrderStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None
    changed_by: Optional[str] = None
    estimated_repair_amount: Optional[int] = None

    @field_validator("estimated_repair_amount", mode="before")
    def validate_estimated_repair_amount_opt(cls, v):
        if v is None:
            return None
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
            val_int = int(v)
            if val_int < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return val_int
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
            return v
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                val = float(v)
                if not val.is_integer():
                    raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
                val_int = int(val)
                if val_int < 0:
                    raise ValueError("Предполагаемая стоимость ремонта не может быть отрицательной")
                return val_int
            except Exception:
                raise ValueError("Предполагаемая стоимость ремонта должна быть целым числом")
        return v

class RepairOrder(RepairOrderBase):
    id: int
    number: str
    status: str
    status_label: Optional[str] = None
    priority_label: Optional[str] = None
    accepted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    history: List[RepairStatusHistorySchema] = []

    class Config:
        from_attributes = True

class RepairListResponse(BaseModel):
    items: List[RepairOrder]
    total: int
    page: int
    page_size: int
    total_pages: int

# External Listing Schemas
class ProductExternalListingBase(BaseModel):
    product_id: int
    marketplace: str = "avito"
    external_account_key: str
    external_item_id: str
    external_url: Optional[str] = None
    remote_status: str = "active"
    remote_status_raw: Optional[str] = None
    source_title: Optional[str] = None
    source_price: Optional[float] = None
    source_attributes_json: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    last_imported_at: Optional[datetime] = None
    last_pushed_at: Optional[datetime] = None
    sync_state: str = "synced"
    sync_error: Optional[str] = None

class ProductExternalListingCreate(ProductExternalListingBase):
    pass

class ProductExternalListing(ProductExternalListingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Avito Item Import Payload Schema
class AvitoImportPhotoItem(BaseModel):
    url: Optional[str] = None
    position: Optional[int] = None
    content_base64: Optional[str] = None
    filename: Optional[str] = None

class AvitoItemImportPayload(BaseModel):
    account_key: str
    external_item_id: str
    external_url: Optional[str] = None
    remote_status: str = "active"
    remote_status_raw: Optional[str] = None
    title: str
    price: Optional[float] = None
    description: Optional[str] = None
    category_path: List[str] = []
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: Optional[str] = None
    parameters: dict = {}
    photos: List[AvitoImportPhotoItem] = []
    raw_source_data: Optional[dict] = None

class AvitoItemImportResponse(BaseModel):
    status: str
    product_id: int
    external_listing_id: int
    photos_imported: int
    photos_skipped: int = 0
    photos_reconciled: int = 0

# Dynamic Avito Category & Attribute Schemas
class AvitoAttributeOptionSchema(BaseModel):
    id: int
    attribute_definition_id: int
    external_option_id: Optional[str] = None
    value: str
    label: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    class Config:
        from_attributes = True

class AvitoAttributeDefinitionSchema(BaseModel):
    id: int
    category_id: int
    external_key: str
    name: str
    type: str = "string"
    required: bool = False
    multiple: bool = False
    unit: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    options: List[AvitoAttributeOptionSchema] = []
    class Config:
        from_attributes = True

class AvitoCategorySchema(BaseModel):
    id: int
    external_category_id: Optional[str] = None
    name: str
    parent_external_category_id: Optional[str] = None
    path: Optional[str] = None
    source: str = "avito"
    is_active: bool = True
    class Config:
        from_attributes = True

class ProductAvitoAttributeValueSchema(BaseModel):
    id: int
    product_id: int
    attribute_definition_id: int
    option_id: Optional[int] = None
    external_key: Optional[str] = None
    attribute_name: Optional[str] = None
    value: Optional[str] = None
    raw_value: Optional[str] = None
    source: str = "avito"
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ProductAvitoAttributesResponse(BaseModel):
    product_id: int
    avito_category: Optional[AvitoCategorySchema] = None
    attributes: List[ProductAvitoAttributeValueSchema] = []
    class Config:
        from_attributes = True

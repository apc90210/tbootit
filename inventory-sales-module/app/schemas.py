from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# These schemas reflect what we expect from the Core API
class Product(BaseModel):
    id: int
    sku: Optional[str] = None
    title: str
    status: str
    price: Optional[float] = None  # Using sale_price from Core
    sale_price: Optional[float] = None
    quantity: int
    storage_location: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

class ProductListResponse(BaseModel):
    items: List[Product]
    total: int
    limit: int
    offset: int

# --- Sales schemas (Stage 04E) ---

SELLABLE_STATUSES = {"in_stock", "reserved"}

PAYMENT_METHODS = {
    "cash": "Наличные",
    "card": "Карта / эквайринг",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "mixed": "Смешанная оплата",
    "other": "Другое",
}

STATUS_LABELS = {
    "in_stock": "В наличии",
    "reserved": "В резерве",
    "sold": "Продан",
    "draft": "Черновик",
    "in_repair": "В ремонте",
    "written_off": "Списан",
}

SALE_STATUS_LABELS = {
    "completed": "Завершена",
    "cancelled": "Отменена",
}


class SaleCreateForm(BaseModel):
    product_id: int
    price: float
    payment_method: str
    notes: Optional[str] = None


class SaleItemView(BaseModel):
    id: Optional[int] = None
    product_id: int
    title: Optional[str] = None
    price: float
    quantity: int


class SaleView(BaseModel):
    id: int
    customer_id: Optional[int] = None
    total_amount: float
    payment_method: Optional[str] = "cash"
    comment: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancel_reason: Optional[str] = None


class SaleListItem(BaseModel):
    id: int
    total_amount: float
    payment_method: Optional[str] = "cash"
    status: Optional[str] = None
    created_at: Optional[str] = None

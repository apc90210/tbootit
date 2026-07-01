from pydantic import BaseModel
from typing import Optional, List

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

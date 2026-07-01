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

class ProductStatusUpdate(BaseModel):
    status: str

class Product(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

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
    payment_method: Optional[str] = None
    comment: Optional[str] = None

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class Sale(SaleBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

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

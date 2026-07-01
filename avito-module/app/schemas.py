from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ParseRequest(BaseModel):
    profile_url: str
    max_pages: int = 1
    save_html: bool = True

class ParseResponse(BaseModel):
    status: str
    run_id: str
    profile_url: str
    ads_found: int
    ads_saved: int
    warnings: List[str] = []

class Photo(BaseModel):
    url: str
    local_path: Optional[str] = None
    downloaded: bool = False

class ParsedAd(BaseModel):
    id: str
    run_id: str
    source: str = "avito"
    source_url: str
    external_id: Optional[str] = None
    title: str
    price: Optional[float] = None
    currency: str = "RUB"
    description: Optional[str] = None
    location: Optional[str] = None
    seller_name: Optional[str] = None
    published_at_text: Optional[str] = None
    category_path: List[str] = []
    parameters: Dict[str, str] = {}
    photos: List[Photo] = []
    raw_html_path: Optional[str] = None
    parse_status: str
    parse_errors: List[str] = []
    created_at: str

class ParseRun(BaseModel):
    run_id: str
    profile_url: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    pages_parsed: int = 0
    ads_found: int = 0
    ads_saved: int = 0
    warnings: List[str] = []
    errors: List[str] = []

# Product Card mappings
class ProductSection(BaseModel):
    sku: str
    title: str
    category_path: List[str] = []
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    min_price: Optional[float] = None
    market_price: Optional[float] = None
    quantity: int = 1
    storage_location: Optional[str] = None
    notes: Optional[str] = None

class AvitoSection(BaseModel):
    title: str
    description: Optional[str] = None
    category_path: Optional[List[str]] = None
    goods_type: Optional[str] = None
    condition: Optional[str] = None
    price: Optional[float] = None
    seller_type: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    parameters: Dict[str, str] = {}
    photos: Optional[List[Any]] = None

class SiteSection(BaseModel):
    title: str
    description: Optional[str] = None
    publish_ready: bool = False

class ProductCardImport(BaseModel):
    source: str = "avito-module"
    schema_version: str = "1.0"
    operation: str = "create_or_update"
    product: ProductSection
    avito: Optional[AvitoSection] = None
    site: Optional[SiteSection] = None

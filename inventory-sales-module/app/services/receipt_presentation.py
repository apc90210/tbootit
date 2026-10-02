"""
Canonical receipt transport DTO and consumer adapter for Technoreboot.

Inventory-sales-module is a consumer/adapter only.
Canonical business receipt content, defaults, and formatting live solely in Core API:
core.app.services.receipt_presentation.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ReceiptDocumentItem(BaseModel):
    idx: int
    id: Optional[int] = None
    product_id: Optional[int] = None
    title: str
    code: str = ""
    unit: str = "шт"
    quantity: int = 1
    price: float = 0.0
    unit_price: float = 0.0
    line_total: float = 0.0
    price_formatted: str = "0.00"
    line_total_formatted: str = "0.00"

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class ReceiptDocumentData(BaseModel):
    id: int
    sale_id: int
    receipt_number: str
    receipt_title: str
    date_formatted: str
    created_at: Optional[str] = None
    status: str = "completed"
    status_banner_text: Optional[str] = None
    status_banner_bg_color: Optional[str] = None
    revision_count: int = 0
    revision_notice: Optional[str] = None
    cancelled_at: Optional[str] = None
    superseded_by_sale_id: Optional[int] = None
    source_sale_id: Optional[int] = None

    organization_name: str
    inn: str
    address: str
    phone: str

    items: List[ReceiptDocumentItem] = Field(default_factory=list)
    total_items_count: int = 0
    total_amount: float = 0.0
    total_amount_formatted: str = "0.00"
    prepayment_formatted: str = "0.00"
    to_pay_formatted: str = "0.00"

    payment_method: str = "unspecified"
    payment_method_label: str = "Не указано"
    payment_label: str = "Не указано"

    cashier_name: str = "Продавец"
    seller_signature_title: str = "Отпустил:"
    seller_signature_actor: str = "(Продавец)"

    buyer_signature_title: str = "Покупатель:"
    buyer_signature_actor: str = "Частное лицо"

    warranty_title: str = "Гарантийные условия"
    warranty_enabled: bool = True
    warranty_days: int = 30
    warranty_headline: str = ""
    warranty_body_text: str = ""
    warranty_full_text: str = ""
    buyer_acknowledgement_title: str = "Подпись покупателя:"
    buyer_acknowledgement_prompt: str = "С условиями ознакомился и согласен:"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


def parse_receipt_document_data(data: Union[Dict[str, Any], ReceiptDocumentData]) -> ReceiptDocumentData:
    """
    Consumer adapter: validates and loads canonical receipt document data
    originating from Core API (GET /api/sales/{sale_id}/receipt/data).
    Performs zero business derivations or label overrides.
    """
    if isinstance(data, ReceiptDocumentData):
        return data
    return ReceiptDocumentData.model_validate(data)

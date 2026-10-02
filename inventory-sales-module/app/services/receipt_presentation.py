"""
Canonical receipt presentation and domain data model for Technoreboot.
Shared client/module mirror of core.app.services.receipt_presentation.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

DEFAULT_ORGANIZATION_NAME = "ИП Атанов Павел Сергеевич"
DEFAULT_INN = "667009336901"
DEFAULT_ADDRESS = "Свердловская обл. г. Екатеринбург, ул. Кузнецова, дом 10"
DEFAULT_PHONE = "+7 343 344 88 95"
DEFAULT_CASHIER_NAME = "Продавец"
DEFAULT_CUSTOMER_LABEL = "Частное лицо"
DEFAULT_WARRANTY_DAYS = 30

DEFAULT_WARRANTY_TEXT = (
    "На все Б/У товары предоставляется гарантия 30 дней.\n"
    "Гарантийный ремонт и обмен Б/У товара возможен только в случае обнаружения "
    "дефекта товара в течении 30 дней с даты продажи.\n"
    "Товар Б/У без дефектов возврату - не подлежит, возможен обмен, но только по согласованию "
    "с менеджером магазина. В случае обнаружения дефекта товара по вине покупателя обмен и возврат товара – невозможен.\n"
    "На программное обеспечение и расходные материалы гарантия не предоставляется.\n"
    "В случае обнаружения неисправности – товар сдается на диагностику. "
    "По согласованию с продавцом – возможна мгновенная замена товара, без проведения диагностики."
)

DEFAULT_NO_WARRANTY_TEXT = (
    "Товар продаётся без гарантии, в том состоянии, в котором есть.\n"
    "Покупатель внимательно осмотрел товар при покупке."
)

SELLER_SIGNATURE_TITLE = "Отпустил:"
BUYER_SIGNATURE_TITLE = "Покупатель:"
WARRANTY_SECTION_TITLE = "Гарантийные условия"
BUYER_ACKNOWLEDGEMENT_TITLE = "Подпись покупателя:"
BUYER_ACKNOWLEDGEMENT_PROMPT = "С условиями ознакомился и согласен:"
NO_ITEMS_TEXT = "Товары отсутствуют"
ITEM_UNIT_DEFAULT = "шт"

PAYMENT_METHODS_LABELS = {
    "cash": "Наличные",
    "card": "Банковская карта",
    "card_terminal": "Банковская карта",
    "sbp": "СБП (Система быстрых платежей)",
    "transfer": "Безналичный перевод",
    "legal_entity_account": "Счёт юрлица",
    "mixed": "Смешанная оплата",
    "other": "Другое",
    "unspecified": "Не указано",
}


class ReceiptDocumentItem(BaseModel):
    idx: int
    id: Optional[int] = None
    product_id: Optional[int] = None
    title: str
    code: str = ""
    unit: str = ITEM_UNIT_DEFAULT
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

    cashier_name: str = DEFAULT_CASHIER_NAME
    seller_signature_title: str = SELLER_SIGNATURE_TITLE
    seller_signature_actor: str = f"({DEFAULT_CASHIER_NAME})"

    buyer_signature_title: str = BUYER_SIGNATURE_TITLE
    buyer_signature_actor: str = DEFAULT_CUSTOMER_LABEL

    warranty_title: str = WARRANTY_SECTION_TITLE
    warranty_enabled: bool = True
    warranty_days: int = DEFAULT_WARRANTY_DAYS
    warranty_headline: str = ""
    warranty_body_text: str = ""
    warranty_full_text: str = ""
    buyer_acknowledgement_title: str = BUYER_ACKNOWLEDGEMENT_TITLE
    buyer_acknowledgement_prompt: str = BUYER_ACKNOWLEDGEMENT_PROMPT

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


def _normalize_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def build_receipt_document_data(
    sale: Union[Dict[str, Any], Any],
    org_settings: Optional[Union[Dict[str, Any], Any]] = None,
) -> ReceiptDocumentData:
    """
    Builds the single canonical ReceiptDocumentData presentation model
    from a sale snapshot and organization settings.
    """
    if org_settings is None:
        org_settings = {}

    def get_val(source: Any, key: str, fallback: Any = None) -> Any:
        if source is None:
            return fallback
        if isinstance(source, dict):
            val = source.get(key)
        else:
            val = getattr(source, key, None)
        return val if val is not None else fallback

    # 1. Sale ID & Status
    sale_id_raw = get_val(sale, "id") or get_val(sale, "sale_id") or 0
    sale_id = int(sale_id_raw)
    status = str(get_val(sale, "status", "completed")).lower().strip()

    # Dates
    created_at_raw = get_val(sale, "created_at")
    if isinstance(created_at_raw, datetime):
        created_at_str = created_at_raw.isoformat()
        date_formatted = created_at_raw.strftime("%Y-%m-%d")
    elif created_at_raw:
        created_at_str = str(created_at_raw)
        date_formatted = created_at_str[:10] if len(created_at_str) >= 10 else "—"
    else:
        created_at_str = ""
        date_formatted = "—"

    cancelled_at_raw = get_val(sale, "cancelled_at")
    if isinstance(cancelled_at_raw, datetime):
        cancelled_at_str = cancelled_at_raw.isoformat()
        cancel_date = cancelled_at_raw.strftime("%Y-%m-%d")
    elif cancelled_at_raw:
        cancelled_at_str = str(cancelled_at_raw)
        cancel_date = cancelled_at_str[:10] if len(cancelled_at_str) >= 10 else ""
    else:
        cancelled_at_str = None
        cancel_date = ""

    superseded_by_sale_id = get_val(sale, "superseded_by_sale_id") or get_val(sale, "replaced_by_sale_id")
    if superseded_by_sale_id is not None:
        try:
            superseded_by_sale_id = int(superseded_by_sale_id)
        except (ValueError, TypeError):
            pass

    source_sale_id = get_val(sale, "source_sale_id") or get_val(sale, "original_sale_id")
    if source_sale_id is not None:
        try:
            source_sale_id = int(source_sale_id)
        except (ValueError, TypeError):
            pass

    revision_count = int(get_val(sale, "revision_count", 0) or 0)

    # 2. Status Banner & Revision Notice
    status_banner_text: Optional[str] = None
    status_banner_bg_color: Optional[str] = None

    if status in ["canceled", "cancelled"]:
        status_banner_text = f"АРХИВНЫЙ ЧЕК — ПРОДАЖА №{sale_id} ОТМЕНЕНА ({cancel_date})"
        status_banner_bg_color = "#dc3545"
    elif status == "superseded":
        sup_str = str(superseded_by_sale_id or "")
        status_banner_text = f"АРХИВНЫЙ ЧЕК — ПРОДАЖА №{sale_id} ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №{sup_str})"
        status_banner_bg_color = "#6c757d"
    elif status == "reissued":
        src_str = str(source_sale_id or "")
        status_banner_text = f"ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №{src_str})"
        status_banner_bg_color = "#007bff"

    revision_notice: Optional[str] = None
    if revision_count > 0:
        revision_notice = f"Продажа скорректирована — ревизия №{revision_count}"

    receipt_title = f"Товарный чек № {sale_id} от {date_formatted}"
    receipt_number = f"REC-{sale_id:06d}"

    # 3. Organization Info
    org_name = _normalize_str(get_val(org_settings, "organization_name"), DEFAULT_ORGANIZATION_NAME)
    inn = _normalize_str(get_val(org_settings, "inn"), DEFAULT_INN)
    address = _normalize_str(get_val(org_settings, "address"), DEFAULT_ADDRESS)
    phone = _normalize_str(get_val(org_settings, "phone"), DEFAULT_PHONE)

    # 4. Items List
    raw_items = get_val(sale, "items", []) or []
    doc_items: List[ReceiptDocumentItem] = []
    calculated_total = 0.0

    for idx, raw_item in enumerate(raw_items, start=1):
        if isinstance(raw_item, dict):
            item_id = raw_item.get("id")
            prod_id = raw_item.get("product_id")
            title = _normalize_str(raw_item.get("title"), f"Товар #{prod_id}" if prod_id else "Позиция")
            code = _normalize_str(
                raw_item.get("sku") or raw_item.get("barcode") or raw_item.get("product_id") or ""
            )
            qty = int(raw_item.get("quantity") or 1)
            price = float(raw_item.get("price") or raw_item.get("unit_price") or 0.0)
        else:
            item_id = getattr(raw_item, "id", None)
            prod_id = getattr(raw_item, "product_id", None)
            title = _normalize_str(
                getattr(raw_item, "title", None),
                f"Товар #{prod_id}" if prod_id else "Позиция"
            )
            code = _normalize_str(
                getattr(raw_item, "sku", None) or getattr(raw_item, "barcode", None) or getattr(raw_item, "product_id", None) or ""
            )
            qty = int(getattr(raw_item, "quantity", 1) or 1)
            price = float(getattr(raw_item, "price", None) or getattr(raw_item, "unit_price", 0.0) or 0.0)

        line_sum = round(price * qty, 2)
        calculated_total += line_sum

        doc_items.append(
            ReceiptDocumentItem(
                idx=idx,
                id=item_id,
                product_id=prod_id,
                title=title,
                code=code,
                unit=ITEM_UNIT_DEFAULT,
                quantity=qty,
                price=price,
                unit_price=price,
                line_total=line_sum,
                price_formatted=f"{price:.2f}",
                line_total_formatted=f"{line_sum:.2f}",
            )
        )

    # 5. Totals & Payment
    total_amt_val = get_val(sale, "total_amount")
    if total_amt_val is not None:
        total_amount = float(total_amt_val)
    else:
        total_amount = calculated_total

    total_amount_formatted = f"{total_amount:.2f}"
    prepayment_formatted = "0.00"
    to_pay_formatted = total_amount_formatted

    raw_pm = _normalize_str(get_val(sale, "payment_method"), "unspecified").lower()
    custom_label = get_val(sale, "payment_label")
    payment_method_label = PAYMENT_METHODS_LABELS.get(raw_pm, custom_label or raw_pm)

    # 6. Signatures
    cashier_candidate = (
        get_val(sale, "cashier_name")
        or get_val(org_settings, "default_cashier_name")
        or DEFAULT_CASHIER_NAME
    )
    cashier_name = _normalize_str(cashier_candidate, DEFAULT_CASHIER_NAME)
    seller_signature_actor = f"({cashier_name})"

    customer_candidate = (
        get_val(org_settings, "default_customer_label")
        or DEFAULT_CUSTOMER_LABEL
    )
    buyer_signature_actor = _normalize_str(customer_candidate, DEFAULT_CUSTOMER_LABEL)

    # 7. Warranty Terms
    warranty_enabled_raw = get_val(sale, "warranty_enabled")
    warranty_enabled = True if warranty_enabled_raw is None else bool(warranty_enabled_raw)

    warranty_days_raw = get_val(sale, "warranty_days")
    warranty_days = int(warranty_days_raw) if warranty_days_raw is not None else DEFAULT_WARRANTY_DAYS

    if warranty_enabled:
        warranty_headline = f"На все Б/У товары предоставляется гарантия {warranty_days} дней."
        raw_w_text = _normalize_str(get_val(org_settings, "warranty_text"), DEFAULT_WARRANTY_TEXT)
        lines = [l.strip() for l in raw_w_text.split("\n") if l.strip()]
        if len(lines) > 1 and ("гарантия" in lines[0].lower() or "предоставляется" in lines[0].lower()):
            body_lines = lines[1:]
        else:
            body_lines = lines
        warranty_body_text = "\n".join(body_lines)
        warranty_full_text = f"{warranty_headline}\n{warranty_body_text}" if warranty_body_text else warranty_headline
    else:
        warranty_headline = ""
        warranty_body_text = _normalize_str(get_val(org_settings, "no_warranty_text"), DEFAULT_NO_WARRANTY_TEXT)
        warranty_full_text = warranty_body_text

    return ReceiptDocumentData(
        id=sale_id,
        sale_id=sale_id,
        receipt_number=receipt_number,
        receipt_title=receipt_title,
        date_formatted=date_formatted,
        created_at=created_at_str,
        status=status,
        status_banner_text=status_banner_text,
        status_banner_bg_color=status_banner_bg_color,
        revision_count=revision_count,
        revision_notice=revision_notice,
        cancelled_at=cancelled_at_str,
        superseded_by_sale_id=superseded_by_sale_id,
        source_sale_id=source_sale_id,
        organization_name=org_name,
        inn=inn,
        address=address,
        phone=phone,
        items=doc_items,
        total_items_count=len(doc_items),
        total_amount=total_amount,
        total_amount_formatted=total_amount_formatted,
        prepayment_formatted=prepayment_formatted,
        to_pay_formatted=to_pay_formatted,
        payment_method=raw_pm,
        payment_method_label=payment_method_label,
        payment_label=payment_method_label,
        cashier_name=cashier_name,
        seller_signature_title=SELLER_SIGNATURE_TITLE,
        seller_signature_actor=seller_signature_actor,
        buyer_signature_title=BUYER_SIGNATURE_TITLE,
        buyer_signature_actor=buyer_signature_actor,
        warranty_title=WARRANTY_SECTION_TITLE,
        warranty_enabled=warranty_enabled,
        warranty_days=warranty_days,
        warranty_headline=warranty_headline,
        warranty_body_text=warranty_body_text,
        warranty_full_text=warranty_full_text,
        buyer_acknowledgement_title=BUYER_ACKNOWLEDGEMENT_TITLE,
        buyer_acknowledgement_prompt=BUYER_ACKNOWLEDGEMENT_PROMPT,
    )

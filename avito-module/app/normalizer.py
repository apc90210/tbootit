import hashlib
from app.schemas import ParsedAd, ProductCardImport, ProductSection, AvitoSection

def normalize_to_product_card(ad: ParsedAd) -> ProductCardImport:
    sku = ad.external_id
    if not sku:
        sku_hash = hashlib.md5(ad.source_url.encode("utf-8")).hexdigest()[:8].upper()
        sku = f"AVITO-{sku_hash}"
    else:
        sku = f"AVITO-{sku}"
        
    product = ProductSection(
        sku=sku,
        title=ad.title,
        category_path=ad.category_path,
        sale_price=ad.price,
        description=ad.description,
        storage_location=ad.location,
        notes=f"Source URL: {ad.source_url}"
    )
    
    # Try to extract brand and model from parameters
    if "Производитель" in ad.parameters:
        product.brand = ad.parameters["Производитель"]
    if "Модель" in ad.parameters:
        product.model = ad.parameters["Модель"]
        
    avito = AvitoSection(
        title=ad.title,
        description=ad.description,
        category_path=ad.category_path,
        price=ad.price,
        contact_name=ad.seller_name,
        address=ad.location,
        parameters=ad.parameters,
        photos=ad.photos
    )
    
    return ProductCardImport(
        source="avito-module",
        operation="create_or_update",
        product=product,
        avito=avito,
        site=None
    )

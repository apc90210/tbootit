"""
Category-specific specification schemas and canonical description generator.
Per Section 14 of TR_Stage05A:
- Structured facts for Printer and MFP.
- Missing values remain null/unknown (no hallucination).
- Canonical human-readable description is generated purely from structured facts,
  never containing condition/defect text of concrete used items.
"""

from typing import Dict, Any, Optional, List


PRINTER_SPEC_FIELDS = [
    ("technology", "Технология печати"),
    ("color_mode", "Цветность печати"),
    ("max_format", "Максимальный формат"),
    ("duplex", "Двусторонняя печать (дуплекс)"),
    ("print_speed", "Скорость печати"),
    ("print_resolution", "Разрешение печати"),
    ("interfaces", "Интерфейсы"),
    ("cartridge_family", "Картридж / тонер"),
    ("scanner", "Наличие сканера"),
]

MFP_SPEC_FIELDS = PRINTER_SPEC_FIELDS + [
    ("scanner_type", "Тип сканера"),
    ("scan_resolution", "Разрешение сканирования"),
    ("adf", "Автоподатчик оригиналов (ADF)"),
    ("fax", "Факс"),
]


def build_canonical_description(
    device_type: str,
    brand: str,
    model: str,
    specs: Dict[str, Any],
) -> str:
    """
    Generate canonical, reusable Russian description from structured specs.
    Strictly factual. Does NOT include concrete condition, defects, or pricing.
    """
    dev_type_lower = (device_type or "").lower()
    is_mfu = "mfu" in dev_type_lower or "мфу" in dev_type_lower
    
    header = f"{brand} {model}"
    if is_mfu:
        type_str = "Многофункциональное устройство (МФУ)"
    else:
        type_str = "Принтер"

    lines = [f"{type_str} {header}."]
    
    # Tech and color
    tech = specs.get("technology") or specs.get("Технология печати")
    color = specs.get("color_mode") or specs.get("Цветность печати") or specs.get("Цветность")
    fmt = specs.get("max_format") or specs.get("Максимальный формат") or specs.get("Формат")
    
    desc_parts = []
    if tech:
        desc_parts.append(f"Технология печати: {tech}.")
    if color:
        desc_parts.append(f"Цветность: {color}.")
    if fmt:
        desc_parts.append(f"Формат: {fmt}.")
    
    if desc_parts:
        lines.append(" ".join(desc_parts))
        
    # Speed and duplex
    speed = specs.get("print_speed") or specs.get("Скорость печати")
    duplex = specs.get("duplex") or specs.get("Двусторонняя печать") or specs.get("Двусторонняя печать (дуплекс)")
    speed_parts = []
    if speed:
        speed_parts.append(f"Скорость печати: {speed}.")
    if duplex:
        duplex_val = str(duplex).lower()
        if duplex_val in ("да", "true", "есть", "автоматическая"):
            speed_parts.append("Автоматическая двусторонняя печать (дуплекс).")
        elif duplex_val in ("нет", "false", "отсутствует", "ручная"):
            speed_parts.append("Двусторонняя печать: с ручной подачей.")
        else:
            speed_parts.append(f"Двусторонняя печать: {duplex}.")
    if speed_parts:
        lines.append(" ".join(speed_parts))

    # Scanner / ADF for MFP
    if is_mfu:
        scan_parts = []
        scanner_type = specs.get("scanner_type") or specs.get("Тип сканера")
        adf = specs.get("adf") or specs.get("Автоподатчик") or specs.get("Автоподатчик оригиналов (ADF)")
        if scanner_type:
            scan_parts.append(f"Сканер: {scanner_type}.")
        if adf:
            adf_val = str(adf).lower()
            if adf_val in ("да", "true", "есть"):
                scan_parts.append("Автоподатчик документов (ADF).")
            else:
                scan_parts.append(f"Автоподатчик: {adf}.")
        if scan_parts:
            lines.append(" ".join(scan_parts))

    # Interfaces
    interfaces = specs.get("interfaces") or specs.get("Интерфейсы") or specs.get("Интерфейс")
    if interfaces:
        lines.append(f"Интерфейсы: {interfaces}.")

    # Cartridges
    cartridge = specs.get("cartridge_family") or specs.get("Картридж / тонер") or specs.get("Картридж")
    if cartridge:
        lines.append(f"Картридж: {cartridge}.")

    return "\n".join(lines)

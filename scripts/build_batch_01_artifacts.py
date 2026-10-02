#!/usr/bin/env python3
"""
Generator for WEB-07C External Verified Reference Enrichment Batch 01 Artifacts.
Produces:
1. EXTERNAL_ENRICHMENT_BATCH_01.json
2. EXTERNAL_SOURCE_MANIFEST.json
3. EXTERNAL_ENRICHMENT_CONFLICTS.json
4. UNRESOLVED_AFTER_BATCH_01.json
"""

import os
import sys
import json
import sqlite3
import hashlib
from typing import Dict, Any, List

DB_PATH = r"C:\tbootit\data\db\technoreboot.db"
OUTBOX_DIR = r"C:\tboot-site\AntiGravity\PROMPT_WEB_07C_EXTERNAL_VERIFIED_REFERENCE_ENRICHMENT\Outbox"
DATA_DIR = r"C:\tbootit\data\reference_catalog"

MODELS_DATA = [
    # ------------------ PRINTERS (15) ------------------
    {
        "stable_key": "hp|laserjet-pro-400-m401a",
        "canonical_name": "HP LaserJet Pro 400 M401a",
        "brand": "HP",
        "model": "LaserJet Pro 400 M401a",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m401_ds",
                "url": "https://support.hp.com/us-en/document/c03333919",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_m401_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m401_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m401_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m401_ds"]},
            "print_speed_a4_mono": {"value": "33 стр/мин", "source_ids": ["hp_m401_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m401_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m401_ds"]},
            "first_page_time": {"value": "8.0 сек", "source_ids": ["hp_m401_ds"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["hp_m401_ds"]},
            "recommended_monthly_volume": {"value": "750 - 3 000 стр/мес", "source_ids": ["hp_m401_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_m401_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["hp_m401_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "33 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "8.0 сек",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Рекомендуемая нагрузка": "750 - 3 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-enterprise-p3015",
        "canonical_name": "HP LaserJet Enterprise P3015",
        "brand": "HP",
        "model": "LaserJet Enterprise P3015",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_p3015_ds",
                "url": "https://support.hp.com/us-en/document/c01826019",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_p3015_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_p3015_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_p3015_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_p3015_ds"]},
            "print_speed_a4_mono": {"value": "40 стр/мин", "source_ids": ["hp_p3015_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_p3015_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_p3015_ds"]},
            "first_page_time": {"value": "7.5 сек", "source_ids": ["hp_p3015_ds"]},
            "monthly_duty_cycle": {"value": "100 000 стр/мес", "source_ids": ["hp_p3015_ds"]},
            "recommended_monthly_volume": {"value": "1 500 - 5 000 стр/мес", "source_ids": ["hp_p3015_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_p3015_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["hp_p3015_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "40 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "7.5 сек",
            "Максимальная нагрузка": "100 000 стр/мес",
            "Рекомендуемая нагрузка": "1 500 - 5 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-p2035",
        "canonical_name": "HP LaserJet P2035",
        "brand": "HP",
        "model": "LaserJet P2035",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_p2035_ds",
                "url": "https://support.hp.com/us-en/document/c01594970",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_p2035_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_p2035_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_p2035_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_p2035_ds"]},
            "print_speed_a4_mono": {"value": "30 стр/мин", "source_ids": ["hp_p2035_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (FastRes 1200)", "source_ids": ["hp_p2035_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_p2035_ds"]},
            "first_page_time": {"value": "8.0 сек", "source_ids": ["hp_p2035_ds"]},
            "monthly_duty_cycle": {"value": "25 000 стр/мес", "source_ids": ["hp_p2035_ds"]},
            "recommended_monthly_volume": {"value": "500 - 2 500 стр/мес", "source_ids": ["hp_p2035_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_p2035_ds"]},
            "memory": {"value": "16 МБ", "source_ids": ["hp_p2035_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "30 стр/мин",
            "Разрешение печати": "600 x 600 dpi (FastRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "8.0 сек",
            "Максимальная нагрузка": "25 000 стр/мес",
            "Рекомендуемая нагрузка": "500 - 2 500 стр/мес",
            "Интерфейсы": "USB 2.0, IEEE 1284-B",
            "Объем памяти": "16 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-pro-m203dw",
        "canonical_name": "HP LaserJet Pro M203dw",
        "brand": "HP",
        "model": "LaserJet Pro M203dw",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m203dw_ds",
                "url": "https://support.hp.com/us-en/document/c05252870",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_m203dw_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m203dw_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m203dw_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m203dw_ds"]},
            "print_speed_a4_mono": {"value": "28 стр/мин", "source_ids": ["hp_m203dw_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m203dw_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["hp_m203dw_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_m203dw_ds"]},
            "wifi": {"value": "Да", "source_ids": ["hp_m203dw_ds"]},
            "first_page_time": {"value": "6.7 сек", "source_ids": ["hp_m203dw_ds"]},
            "monthly_duty_cycle": {"value": "30 000 стр/мес", "source_ids": ["hp_m203dw_ds"]},
            "recommended_monthly_volume": {"value": "250 - 2 500 стр/мес", "source_ids": ["hp_m203dw_ds"]},
            "memory": {"value": "256 МБ", "source_ids": ["hp_m203dw_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "28 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Wi-Fi": "Да",
            "Время выхода первого отпечатка": "6.7 сек",
            "Максимальная нагрузка": "30 000 стр/мес",
            "Рекомендуемая нагрузка": "250 - 2 500 стр/мес",
            "Интерфейсы": "USB 2.0, Ethernet (RJ-45), Wi-Fi (802.11b/g/n)",
            "Объем памяти": "256 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-enterprise-m608",
        "canonical_name": "HP LaserJet Enterprise M608",
        "brand": "HP",
        "model": "LaserJet Enterprise M608",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m608_ds",
                "url": "https://support.hp.com/us-en/document/c05511874",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_m608_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m608_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m608_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m608_ds"]},
            "print_speed_a4_mono": {"value": "61 стр/мин", "source_ids": ["hp_m608_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m608_ds"]},
            "duplex": {"value": "Ручная (автомат в опции)", "source_ids": ["hp_m608_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_m608_ds"]},
            "first_page_time": {"value": "5.4 сек", "source_ids": ["hp_m608_ds"]},
            "monthly_duty_cycle": {"value": "275 000 стр/мес", "source_ids": ["hp_m608_ds"]},
            "recommended_monthly_volume": {"value": "5 000 - 25 000 стр/мес", "source_ids": ["hp_m608_ds"]},
            "memory": {"value": "512 МБ", "source_ids": ["hp_m608_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "61 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Ручная (автомат в опции)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Время выхода первого отпечатка": "5.4 сек",
            "Максимальная нагрузка": "275 000 стр/мес",
            "Рекомендуемая нагрузка": "5 000 - 25 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet (10/100/1000Base-TX)",
            "Объем памяти": "512 МБ"
        }
    },
    {
        "stable_key": "kyocera|fs-4100dn",
        "canonical_name": "Kyocera FS-4100dn",
        "brand": "Kyocera",
        "model": "FS-4100dn",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "kyocera_fs4100_ds",
                "url": "https://www.kyoceradocumentsolutions.eu/en/products/printers/FS4100DN.html",
                "publisher": "Kyocera Document Solutions",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["kyocera_fs4100_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["kyocera_fs4100_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["kyocera_fs4100_ds"]},
            "max_format": {"value": "A4", "source_ids": ["kyocera_fs4100_ds"]},
            "print_speed_a4_mono": {"value": "45 стр/мин", "source_ids": ["kyocera_fs4100_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["kyocera_fs4100_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["kyocera_fs4100_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["kyocera_fs4100_ds"]},
            "first_page_time": {"value": "9.0 сек", "source_ids": ["kyocera_fs4100_ds"]},
            "monthly_duty_cycle": {"value": "200 000 стр/мес", "source_ids": ["kyocera_fs4100_ds"]},
            "memory": {"value": "256 МБ", "source_ids": ["kyocera_fs4100_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "45 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Время выхода первого отпечатка": "9.0 сек",
            "Максимальная нагрузка": "200 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet (10/100/1000Base-TX)",
            "Объем памяти": "256 МБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-lbp6030b",
        "canonical_name": "Canon i-SENSYS LBP6030B",
        "brand": "Canon",
        "model": "i-SENSYS LBP6030B",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_lbp6030_ds",
                "url": "https://www.canon-europe.com/printers/i-sensys-lbp6030b/specifications/",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["canon_lbp6030_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_lbp6030_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_lbp6030_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_lbp6030_ds"]},
            "print_speed_a4_mono": {"value": "18 стр/мин", "source_ids": ["canon_lbp6030_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (AIR 2400 x 600 dpi)", "source_ids": ["canon_lbp6030_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["canon_lbp6030_ds"]},
            "first_page_time": {"value": "7.8 сек", "source_ids": ["canon_lbp6030_ds"]},
            "monthly_duty_cycle": {"value": "5 000 стр/мес", "source_ids": ["canon_lbp6030_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["canon_lbp6030_ds"]},
            "memory": {"value": "32 МБ", "source_ids": ["canon_lbp6030_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "18 стр/мин",
            "Разрешение печати": "600 x 600 dpi (AIR 2400 x 600 dpi)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "7.8 сек",
            "Максимальная нагрузка": "5 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "32 МБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-lbp2900b",
        "canonical_name": "Canon i-SENSYS LBP2900B",
        "brand": "Canon",
        "model": "i-SENSYS LBP2900B",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_lbp2900_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/printers/laser/i-sensys_lbp2900b.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["canon_lbp2900_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_lbp2900_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_lbp2900_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_lbp2900_ds"]},
            "print_speed_a4_mono": {"value": "12 стр/мин", "source_ids": ["canon_lbp2900_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (AIR 2400 x 600 dpi)", "source_ids": ["canon_lbp2900_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["canon_lbp2900_ds"]},
            "first_page_time": {"value": "9.3 сек", "source_ids": ["canon_lbp2900_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["canon_lbp2900_ds"]},
            "memory": {"value": "2 МБ", "source_ids": ["canon_lbp2900_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "12 стр/мин",
            "Разрешение печати": "600 x 600 dpi (AIR 2400 x 600 dpi)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "9.3 сек",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "2 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-p1505",
        "canonical_name": "HP LaserJet P1505",
        "brand": "HP",
        "model": "LaserJet P1505",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_p1505_ds",
                "url": "https://support.hp.com/us-en/document/c01314981",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_p1505_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_p1505_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_p1505_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_p1505_ds"]},
            "print_speed_a4_mono": {"value": "23 стр/мин", "source_ids": ["hp_p1505_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (FastRes 1200)", "source_ids": ["hp_p1505_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_p1505_ds"]},
            "first_page_time": {"value": "6.5 сек", "source_ids": ["hp_p1505_ds"]},
            "monthly_duty_cycle": {"value": "8 000 стр/мес", "source_ids": ["hp_p1505_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_p1505_ds"]},
            "memory": {"value": "2 МБ", "source_ids": ["hp_p1505_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "23 стр/мин",
            "Разрешение печати": "600 x 600 dpi (FastRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "6.5 сек",
            "Максимальная нагрузка": "8 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "2 МБ"
        }
    },
    {
        "stable_key": "hp|color-laserjet-cp1515n",
        "canonical_name": "HP Color LaserJet CP1515n",
        "brand": "HP",
        "model": "Color LaserJet CP1515n",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_cp1515n_ds",
                "url": "https://support.hp.com/us-en/document/c01429676",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_cp1515n_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_cp1515n_ds"]},
            "color_mode": {"value": "Цветная", "source_ids": ["hp_cp1515n_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_cp1515n_ds"]},
            "print_speed_a4_mono": {"value": "12 стр/мин", "source_ids": ["hp_cp1515n_ds"]},
            "print_speed_a4_color": {"value": "8 стр/мин", "source_ids": ["hp_cp1515n_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (ImageREt 3600)", "source_ids": ["hp_cp1515n_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_cp1515n_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_cp1515n_ds"]},
            "monthly_duty_cycle": {"value": "30 000 стр/мес", "source_ids": ["hp_cp1515n_ds"]},
            "memory": {"value": "96 МБ", "source_ids": ["hp_cp1515n_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "12 стр/мин",
            "Скорость печати (A4, цветная)": "8 стр/мин",
            "Разрешение печати": "600 x 600 dpi (ImageREt 3600)",
            "Двусторонняя печать": "Ручная",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "30 000 стр/мес",
            "Интерфейсы": "USB 2.0, Ethernet (RJ-45)",
            "Объем памяти": "96 МБ"
        }
    },
    {
        "stable_key": "hp|color-laserjet-pro-m252n",
        "canonical_name": "HP Color LaserJet Pro M252n",
        "brand": "HP",
        "model": "Color LaserJet Pro M252n",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m252n_ds",
                "url": "https://support.hp.com/us-en/document/c04584285",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_m252n_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m252n_ds"]},
            "color_mode": {"value": "Цветная", "source_ids": ["hp_m252n_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m252n_ds"]},
            "print_speed_a4_mono": {"value": "18 стр/мин", "source_ids": ["hp_m252n_ds"]},
            "print_speed_a4_color": {"value": "18 стр/мин", "source_ids": ["hp_m252n_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (ImageREt 3600)", "source_ids": ["hp_m252n_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m252n_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_m252n_ds"]},
            "first_page_time": {"value": "11.5 сек", "source_ids": ["hp_m252n_ds"]},
            "monthly_duty_cycle": {"value": "30 000 стр/мес", "source_ids": ["hp_m252n_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["hp_m252n_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "18 стр/мин",
            "Скорость печати (A4, цветная)": "18 стр/мин",
            "Разрешение печати": "600 x 600 dpi (ImageREt 3600)",
            "Двусторонняя печать": "Ручная",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Время выхода первого отпечатка": "11.5 сек",
            "Максимальная нагрузка": "30 000 стр/мес",
            "Интерфейсы": "USB 2.0, Fast Ethernet (10/100Base-TX)",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "kyocera|ecosys-p2135dn",
        "canonical_name": "Kyocera ECOSYS P2135dn",
        "brand": "Kyocera",
        "model": "ECOSYS P2135dn",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "kyocera_p2135dn_ds",
                "url": "https://www.kyoceradocumentsolutions.eu/en/products/printers/ECOSYSP2135DN.html",
                "publisher": "Kyocera Document Solutions",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["kyocera_p2135dn_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["kyocera_p2135dn_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["kyocera_p2135dn_ds"]},
            "max_format": {"value": "A4", "source_ids": ["kyocera_p2135dn_ds"]},
            "print_speed_a4_mono": {"value": "35 стр/мин", "source_ids": ["kyocera_p2135dn_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["kyocera_p2135dn_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["kyocera_p2135dn_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["kyocera_p2135dn_ds"]},
            "first_page_time": {"value": "8.0 сек", "source_ids": ["kyocera_p2135dn_ds"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["kyocera_p2135dn_ds"]},
            "memory": {"value": "256 МБ", "source_ids": ["kyocera_p2135dn_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "35 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Время выхода первого отпечатка": "8.0 сек",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Интерфейсы": "USB 2.0, Ethernet (10/100Base-TX)",
            "Объем памяти": "256 МБ"
        }
    },
    {
        "stable_key": "kyocera|ecosys-p6235cdn",
        "canonical_name": "Kyocera ECOSYS P6235cdn",
        "brand": "Kyocera",
        "model": "ECOSYS P6235cdn",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "kyocera_p6235cdn_ds",
                "url": "https://www.kyoceradocumentsolutions.eu/en/products/printers/ECOSYSP6235CDN.html",
                "publisher": "Kyocera Document Solutions",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["kyocera_p6235cdn_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["kyocera_p6235cdn_ds"]},
            "color_mode": {"value": "Цветная", "source_ids": ["kyocera_p6235cdn_ds"]},
            "max_format": {"value": "A4", "source_ids": ["kyocera_p6235cdn_ds"]},
            "print_speed_a4_mono": {"value": "35 стр/мин", "source_ids": ["kyocera_p6235cdn_ds"]},
            "print_speed_a4_color": {"value": "35 стр/мин", "source_ids": ["kyocera_p6235cdn_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["kyocera_p6235cdn_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["kyocera_p6235cdn_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["kyocera_p6235cdn_ds"]},
            "first_page_time": {"value": "6.5 сек", "source_ids": ["kyocera_p6235cdn_ds"]},
            "monthly_duty_cycle": {"value": "100 000 стр/мес", "source_ids": ["kyocera_p6235cdn_ds"]},
            "memory": {"value": "1024 МБ", "source_ids": ["kyocera_p6235cdn_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "35 стр/мин",
            "Скорость печати (A4, цветная)": "35 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Время выхода первого отпечатка": "6.5 сек",
            "Максимальная нагрузка": "100 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet (10/100/1000Base-TX)",
            "Объем памяти": "1024 МБ"
        }
    },
    {
        "stable_key": "zebra|zd220",
        "canonical_name": "Zebra ZD220",
        "brand": "Zebra",
        "model": "ZD220",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "zebra_zd220_ds",
                "url": "https://www.zebra.com/us/en/support-downloads/printers/desktop/zd220.html",
                "publisher": "Zebra Technologies",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер этикеток", "source_ids": ["zebra_zd220_ds"]},
            "print_technology": {"value": "Термотрансферная / прямая термопечать", "source_ids": ["zebra_zd220_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["zebra_zd220_ds"]},
            "max_format": {"value": "Ширина рулона до 104 мм", "source_ids": ["zebra_zd220_ds"]},
            "print_speed_a4_mono": {"value": "102 мм/сек (4 ips)", "source_ids": ["zebra_zd220_ds"]},
            "print_resolution": {"value": "203 dpi", "source_ids": ["zebra_zd220_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["zebra_zd220_ds"]},
            "memory": {"value": "128 МБ SDRAM, 256 МБ Flash", "source_ids": ["zebra_zd220_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер этикеток",
            "Технология печати": "Термотрансферная / прямая термопечать",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "Ширина рулона до 104 мм",
            "Скорость печати": "102 мм/сек (4 ips)",
            "Разрешение печати": "203 dpi",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "128 МБ SDRAM, 256 МБ Flash"
        }
    },
    {
        "stable_key": "brother|hl-2040",
        "canonical_name": "Brother HL-2040",
        "brand": "Brother",
        "model": "HL-2040",
        "device_type": "printer",
        "default_category_id": 1,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "brother_hl2040_ds",
                "url": "https://www.brother-usa.com/support/hl2040",
                "publisher": "Brother Industries",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["brother_hl2040_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["brother_hl2040_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["brother_hl2040_ds"]},
            "max_format": {"value": "A4", "source_ids": ["brother_hl2040_ds"]},
            "print_speed_a4_mono": {"value": "20 стр/мин", "source_ids": ["brother_hl2040_ds"]},
            "print_resolution": {"value": "2400 x 600 dpi (HQ1200)", "source_ids": ["brother_hl2040_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["brother_hl2040_ds"]},
            "first_page_time": {"value": "10.0 сек", "source_ids": ["brother_hl2040_ds"]},
            "usb": {"value": "USB 2.0, IEEE 1284 (Parallel)", "source_ids": ["brother_hl2040_ds"]},
            "memory": {"value": "8 МБ", "source_ids": ["brother_hl2040_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "20 стр/мин",
            "Разрешение печати": "2400 x 600 dpi (HQ1200)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "10.0 сек",
            "Интерфейсы": "USB 2.0, IEEE 1284 (Parallel)",
            "Объем памяти": "8 МБ"
        }
    },

    # ------------------ MFUS (20) ------------------
    {
        "stable_key": "brother|mfc-8880dn",
        "canonical_name": "Brother MFC-8880DN",
        "brand": "Brother",
        "model": "MFC-8880DN",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "brother_mfc8880_ds",
                "url": "https://www.brother-usa.com/support/mfc8880dn",
                "publisher": "Brother Industries",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["brother_mfc8880_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["brother_mfc8880_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["brother_mfc8880_ds"]},
            "max_format": {"value": "A4", "source_ids": ["brother_mfc8880_ds"]},
            "print_speed_a4_mono": {"value": "30 стр/мин", "source_ids": ["brother_mfc8880_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["brother_mfc8880_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["brother_mfc8880_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["brother_mfc8880_ds"]},
            "scanner_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["brother_mfc8880_ds"]},
            "adf": {"value": "Да (двусторонний DADF, 50 листов)", "source_ids": ["brother_mfc8880_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с)", "source_ids": ["brother_mfc8880_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["brother_mfc8880_ds"]},
            "memory": {"value": "64 МБ", "source_ids": ["brother_mfc8880_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "30 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "1200 x 2400 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний DADF, 50 листов)",
            "Факс": "Да (33.6 Кбит/с)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Интерфейсы": "USB 2.0, Ethernet (10/100Base-TX), IEEE 1284",
            "Объем памяти": "64 МБ"
        }
    },
    {
        "stable_key": "epson|workforce-pro-wf-m5799",
        "canonical_name": "Epson WorkForce Pro WF-M5799",
        "brand": "Epson",
        "model": "WorkForce Pro WF-M5799",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "epson_wfm5799_ds",
                "url": "https://www.epson.eu/en_EU/products/printers/inkjet/business/workforce-pro-wf-m5799dwf/p/21430",
                "publisher": "Epson Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["epson_wfm5799_ds"]},
            "print_technology": {"value": "Струйная (PrecisionCore)", "source_ids": ["epson_wfm5799_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["epson_wfm5799_ds"]},
            "max_format": {"value": "A4", "source_ids": ["epson_wfm5799_ds"]},
            "print_speed_a4_mono": {"value": "24 стр/мин", "source_ids": ["epson_wfm5799_ds"]},
            "print_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["epson_wfm5799_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["epson_wfm5799_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["epson_wfm5799_ds"]},
            "scanner_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["epson_wfm5799_ds"]},
            "adf": {"value": "Да (двусторонний DADF, 50 листов)", "source_ids": ["epson_wfm5799_ds"]},
            "fax": {"value": "Да", "source_ids": ["epson_wfm5799_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["epson_wfm5799_ds"]},
            "wifi": {"value": "Да", "source_ids": ["epson_wfm5799_ds"]},
            "monthly_duty_cycle": {"value": "45 000 стр/мес", "source_ids": ["epson_wfm5799_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Струйная (PrecisionCore)",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "24 стр/мин",
            "Разрешение печати": "1200 x 2400 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "1200 x 2400 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний DADF, 50 листов)",
            "Факс": "Да",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Wi-Fi": "Да",
            "Максимальная нагрузка": "45 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet, Wi-Fi, Wi-Fi Direct"
        }
    },
    {
        "stable_key": "hp|laserjet-pro-m1214nfh",
        "canonical_name": "HP LaserJet Pro M1214nfh",
        "brand": "HP",
        "model": "LaserJet Pro M1214nfh",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m1214_ds",
                "url": "https://support.hp.com/us-en/document/c02506461",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_m1214_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m1214_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m1214_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m1214_ds"]},
            "print_speed_a4_mono": {"value": "18 стр/мин", "source_ids": ["hp_m1214_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (FastRes 1200)", "source_ids": ["hp_m1214_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m1214_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["hp_m1214_ds"]},
            "scanner_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m1214_ds"]},
            "adf": {"value": "Да (35 листов)", "source_ids": ["hp_m1214_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с, телефонная трубка)", "source_ids": ["hp_m1214_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_m1214_ds"]},
            "monthly_duty_cycle": {"value": "8 000 стр/мес", "source_ids": ["hp_m1214_ds"]},
            "memory": {"value": "64 МБ", "source_ids": ["hp_m1214_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "18 стр/мин",
            "Разрешение печати": "600 x 600 dpi (FastRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "1200 x 1200 dpi",
            "Автоподатчик (ADF)": "Да (35 листов)",
            "Факс": "Да (33.6 Кбит/с, телефонная трубка)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "8 000 стр/мес",
            "Интерфейсы": "USB 2.0, Fast Ethernet (10/100Base-TX)",
            "Объем памяти": "64 МБ"
        }
    },
    {
        "stable_key": "samsung|scx-3400",
        "canonical_name": "Samsung SCX-3400",
        "brand": "Samsung",
        "model": "SCX-3400",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_scx3400_ds",
                "url": "https://support.hp.com/us-en/document/c05788079",
                "publisher": "Samsung Electronics",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["samsung_scx3400_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["samsung_scx3400_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["samsung_scx3400_ds"]},
            "max_format": {"value": "A4", "source_ids": ["samsung_scx3400_ds"]},
            "print_speed_a4_mono": {"value": "20 стр/мин", "source_ids": ["samsung_scx3400_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["samsung_scx3400_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["samsung_scx3400_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["samsung_scx3400_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["samsung_scx3400_ds"]},
            "monthly_duty_cycle": {"value": "10 000 стр/мес", "source_ids": ["samsung_scx3400_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["samsung_scx3400_ds"]},
            "memory": {"value": "64 МБ", "source_ids": ["samsung_scx3400_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "20 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "600 x 600 dpi",
            "Максимальная нагрузка": "10 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "64 МБ"
        }
    },
    {
        "stable_key": "epson|ecotank-m2140",
        "canonical_name": "Epson EcoTank M2140",
        "brand": "Epson",
        "model": "EcoTank M2140",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "epson_m2140_ds",
                "url": "https://www.epson.eu/en_EU/products/printers/inkjet/consumer/ecotank-m2140/p/22967",
                "publisher": "Epson Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["epson_m2140_ds"]},
            "print_technology": {"value": "Струйная (PrecisionCore)", "source_ids": ["epson_m2140_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["epson_m2140_ds"]},
            "max_format": {"value": "A4", "source_ids": ["epson_m2140_ds"]},
            "print_speed_a4_mono": {"value": "20 стр/мин", "source_ids": ["epson_m2140_ds"]},
            "print_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["epson_m2140_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["epson_m2140_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["epson_m2140_ds"]},
            "scanner_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["epson_m2140_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["epson_m2140_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Струйная (PrecisionCore)",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "20 стр/мин",
            "Разрешение печати": "1200 x 2400 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный",
            "Разрешение сканера": "1200 x 2400 dpi",
            "Интерфейсы": "USB 2.0",
            "Особенности": "Встроенная СНПЧ (EcoTank)"
        }
    },
    {
        "stable_key": "hp|laserjet-3030",
        "canonical_name": "HP LaserJet 3030",
        "brand": "HP",
        "model": "LaserJet 3030",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_3030_ds",
                "url": "https://support.hp.com/us-en/document/c00063255",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_3030_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_3030_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_3030_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_3030_ds"]},
            "print_speed_a4_mono": {"value": "14 стр/мин", "source_ids": ["hp_3030_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_3030_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_3030_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["hp_3030_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["hp_3030_ds"]},
            "adf": {"value": "Да (50 листов)", "source_ids": ["hp_3030_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с)", "source_ids": ["hp_3030_ds"]},
            "monthly_duty_cycle": {"value": "7 000 стр/мес", "source_ids": ["hp_3030_ds"]},
            "usb": {"value": "USB 2.0, IEEE 1284 (Parallel)", "source_ids": ["hp_3030_ds"]},
            "memory": {"value": "32 МБ", "source_ids": ["hp_3030_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "14 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (50 листов)",
            "Факс": "Да (33.6 Кбит/с)",
            "Максимальная нагрузка": "7 000 стр/мес",
            "Интерфейсы": "USB 2.0, IEEE 1284 (Parallel)",
            "Объем памяти": "32 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-enterprise-mfp-m527",
        "canonical_name": "HP LaserJet Enterprise MFP M527",
        "brand": "HP",
        "model": "LaserJet Enterprise MFP M527",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m527_ds",
                "url": "https://support.hp.com/us-en/document/c04812891",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_m527_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m527_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m527_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m527_ds"]},
            "print_speed_a4_mono": {"value": "43 стр/мин", "source_ids": ["hp_m527_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m527_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["hp_m527_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["hp_m527_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["hp_m527_ds"]},
            "adf": {"value": "Да (однопроходный двусторонний DADF, 100 листов)", "source_ids": ["hp_m527_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["hp_m527_ds"]},
            "monthly_duty_cycle": {"value": "150 000 стр/мес", "source_ids": ["hp_m527_ds"]},
            "recommended_monthly_volume": {"value": "2 000 - 7 500 стр/мес", "source_ids": ["hp_m527_ds"]},
            "memory": {"value": "1.25 ГБ", "source_ids": ["hp_m527_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "43 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (однопроходный двусторонний DADF, 100 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "150 000 стр/мес",
            "Рекомендуемая нагрузка": "2 000 - 7 500 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet (10/100/1000Base-TX)",
            "Объем памяти": "1.25 ГБ"
        }
    },
    {
        "stable_key": "hp|laserjet-m1005-mfp",
        "canonical_name": "HP LaserJet M1005 MFP",
        "brand": "HP",
        "model": "LaserJet M1005 MFP",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m1005_ds",
                "url": "https://support.hp.com/us-en/document/c00742186",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_m1005_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m1005_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m1005_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m1005_ds"]},
            "print_speed_a4_mono": {"value": "14 стр/мин", "source_ids": ["hp_m1005_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (FastRes 1200)", "source_ids": ["hp_m1005_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m1005_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["hp_m1005_ds"]},
            "scanner_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m1005_ds"]},
            "monthly_duty_cycle": {"value": "5 000 стр/мес", "source_ids": ["hp_m1005_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_m1005_ds"]},
            "memory": {"value": "32 МБ", "source_ids": ["hp_m1005_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "14 стр/мин",
            "Разрешение печати": "600 x 600 dpi (FastRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "1200 x 1200 dpi",
            "Максимальная нагрузка": "5 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "32 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-pro-m1132-mfp",
        "canonical_name": "HP LaserJet Pro M1132 MFP",
        "brand": "HP",
        "model": "LaserJet Pro M1132 MFP",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m1132_ds",
                "url": "https://support.hp.com/us-en/document/c02058451",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_m1132_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m1132_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m1132_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m1132_ds"]},
            "print_speed_a4_mono": {"value": "18 стр/мин", "source_ids": ["hp_m1132_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (FastRes 1200)", "source_ids": ["hp_m1132_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m1132_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["hp_m1132_ds"]},
            "scanner_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m1132_ds"]},
            "monthly_duty_cycle": {"value": "8 000 стр/мес", "source_ids": ["hp_m1132_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_m1132_ds"]},
            "memory": {"value": "8 МБ", "source_ids": ["hp_m1132_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "18 стр/мин",
            "Разрешение печати": "600 x 600 dpi (FastRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "1200 x 1200 dpi",
            "Максимальная нагрузка": "8 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "8 МБ"
        }
    },
    {
        "stable_key": "hp|laserjet-pro-mfp-m125r",
        "canonical_name": "HP LaserJet Pro MFP M125r",
        "brand": "HP",
        "model": "LaserJet Pro MFP M125r",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m125r_ds",
                "url": "https://support.hp.com/us-en/document/c04207903",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["hp_m125r_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m125r_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m125r_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m125r_ds"]},
            "print_speed_a4_mono": {"value": "20 стр/мин", "source_ids": ["hp_m125r_ds"]},
            "print_resolution": {"value": "600 x 600 dpi", "source_ids": ["hp_m125r_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m125r_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["hp_m125r_ds"]},
            "scanner_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["hp_m125r_ds"]},
            "monthly_duty_cycle": {"value": "8 000 стр/мес", "source_ids": ["hp_m125r_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["hp_m125r_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["hp_m125r_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "20 стр/мин",
            "Разрешение печати": "600 x 600 dpi",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "1200 x 1200 dpi",
            "Максимальная нагрузка": "8 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "xerox|workcentre-3335",
        "canonical_name": "Xerox WorkCentre 3335",
        "brand": "Xerox",
        "model": "WorkCentre 3335",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "xerox_wc3335_ds",
                "url": "https://www.xerox.com/en-us/office/multifunction-printers/workcentre-3335-3345/specifications",
                "publisher": "Xerox Corporation",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["xerox_wc3335_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["xerox_wc3335_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["xerox_wc3335_ds"]},
            "max_format": {"value": "A4", "source_ids": ["xerox_wc3335_ds"]},
            "print_speed_a4_mono": {"value": "33 стр/мин", "source_ids": ["xerox_wc3335_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["xerox_wc3335_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["xerox_wc3335_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["xerox_wc3335_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["xerox_wc3335_ds"]},
            "adf": {"value": "Да (50 листов)", "source_ids": ["xerox_wc3335_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с)", "source_ids": ["xerox_wc3335_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["xerox_wc3335_ds"]},
            "wifi": {"value": "Да", "source_ids": ["xerox_wc3335_ds"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["xerox_wc3335_ds"]},
            "memory": {"value": "1.5 ГБ", "source_ids": ["xerox_wc3335_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "33 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (50 листов)",
            "Факс": "Да (33.6 Кбит/с)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Wi-Fi": "Да",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet, Wi-Fi",
            "Объем памяти": "1.5 ГБ"
        }
    },
    {
        "stable_key": "canon|pixma-mp272",
        "canonical_name": "Canon PIXMA MP272",
        "brand": "Canon",
        "model": "PIXMA MP272",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mp272_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/fax__multifunctionals/inkjet/pixma_mp_series/pixma_mp272.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mp272_ds"]},
            "print_technology": {"value": "Струйная (FINE)", "source_ids": ["canon_mp272_ds"]},
            "color_mode": {"value": "Цветная", "source_ids": ["canon_mp272_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mp272_ds"]},
            "print_speed_a4_mono": {"value": "8.4 стр/мин (ESAT)", "source_ids": ["canon_mp272_ds"]},
            "print_speed_a4_color": {"value": "4.8 стр/мин (ESAT)", "source_ids": ["canon_mp272_ds"]},
            "print_resolution": {"value": "4800 x 1200 dpi", "source_ids": ["canon_mp272_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["canon_mp272_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["canon_mp272_ds"]},
            "scanner_resolution": {"value": "1200 x 2400 dpi", "source_ids": ["canon_mp272_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["canon_mp272_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Струйная (FINE)",
            "Цветность печати": "Цветная",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "8.4 стр/мин (ESAT)",
            "Скорость печати (A4, цветная)": "4.8 стр/мин (ESAT)",
            "Разрешение печати": "4800 x 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "1200 x 2400 dpi (CIS)",
            "Интерфейсы": "USB 2.0"
        }
    },
    {
        "stable_key": "canon|i-sensys-mf446",
        "canonical_name": "Canon i-SENSYS MF446",
        "brand": "Canon",
        "model": "i-SENSYS MF446",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mf446_ds",
                "url": "https://www.canon-europe.com/business-printers-and-faxes/i-sensys-mf440-series/specifications/",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mf446_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_mf446_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_mf446_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mf446_ds"]},
            "print_speed_a4_mono": {"value": "38 стр/мин", "source_ids": ["canon_mf446_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["canon_mf446_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["canon_mf446_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["canon_mf446_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_mf446_ds"]},
            "adf": {"value": "Да (двусторонний DADF, 50 листов)", "source_ids": ["canon_mf446_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["canon_mf446_ds"]},
            "wifi": {"value": "Да", "source_ids": ["canon_mf446_ds"]},
            "monthly_duty_cycle": {"value": "80 000 стр/мес", "source_ids": ["canon_mf446_ds"]},
            "memory": {"value": "1 ГБ", "source_ids": ["canon_mf446_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "38 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний DADF, 50 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Wi-Fi": "Да",
            "Максимальная нагрузка": "80 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet, Wi-Fi",
            "Объем памяти": "1 ГБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-mf446x",
        "canonical_name": "Canon i-SENSYS MF446x",
        "brand": "Canon",
        "model": "i-SENSYS MF446x",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mf446x_ds",
                "url": "https://www.canon-europe.com/business-printers-and-faxes/i-sensys-mf440-series/specifications/",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mf446x_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_mf446x_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_mf446x_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mf446x_ds"]},
            "print_speed_a4_mono": {"value": "38 стр/мин", "source_ids": ["canon_mf446x_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["canon_mf446x_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["canon_mf446x_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["canon_mf446x_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_mf446x_ds"]},
            "adf": {"value": "Да (однопроходный двусторонний DADF, 50 листов)", "source_ids": ["canon_mf446x_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["canon_mf446x_ds"]},
            "wifi": {"value": "Да", "source_ids": ["canon_mf446x_ds"]},
            "monthly_duty_cycle": {"value": "80 000 стр/мес", "source_ids": ["canon_mf446x_ds"]},
            "memory": {"value": "1 ГБ", "source_ids": ["canon_mf446x_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "38 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (однопроходный двусторонний DADF, 50 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Wi-Fi": "Да",
            "Максимальная нагрузка": "80 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet, Wi-Fi",
            "Объем памяти": "1 ГБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-mf4550d",
        "canonical_name": "Canon i-SENSYS MF4550d",
        "brand": "Canon",
        "model": "i-SENSYS MF4550d",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mf4550d_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/fax__multifunctionals/laser/i-sensys_mf_series/i-sensys_mf4550d.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mf4550d_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_mf4550d_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_mf4550d_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mf4550d_ds"]},
            "print_speed_a4_mono": {"value": "25 стр/мин", "source_ids": ["canon_mf4550d_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (AIR 1200 x 600 dpi)", "source_ids": ["canon_mf4550d_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["canon_mf4550d_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["canon_mf4550d_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_mf4550d_ds"]},
            "adf": {"value": "Да (35 листов)", "source_ids": ["canon_mf4550d_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с)", "source_ids": ["canon_mf4550d_ds"]},
            "monthly_duty_cycle": {"value": "10 000 стр/мес", "source_ids": ["canon_mf4550d_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["canon_mf4550d_ds"]},
            "memory": {"value": "64 МБ", "source_ids": ["canon_mf4550d_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "25 стр/мин",
            "Разрешение печати": "600 x 600 dpi (AIR 1200 x 600 dpi)",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (35 листов)",
            "Факс": "Да (33.6 Кбит/с)",
            "Максимальная нагрузка": "10 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "64 МБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-mf4730",
        "canonical_name": "Canon i-SENSYS MF4730",
        "brand": "Canon",
        "model": "i-SENSYS MF4730",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mf4730_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/fax__multifunctionals/laser/i-sensys_mf_series/i-sensys_mf4730.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mf4730_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_mf4730_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_mf4730_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mf4730_ds"]},
            "print_speed_a4_mono": {"value": "23 стр/мин", "source_ids": ["canon_mf4730_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (AIR 1200 x 600 dpi)", "source_ids": ["canon_mf4730_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["canon_mf4730_ds"]},
            "scanner": {"value": "Планшетный", "source_ids": ["canon_mf4730_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_mf4730_ds"]},
            "monthly_duty_cycle": {"value": "10 000 стр/мес", "source_ids": ["canon_mf4730_ds"]},
            "usb": {"value": "USB 2.0", "source_ids": ["canon_mf4730_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["canon_mf4730_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "23 стр/мин",
            "Разрешение печати": "600 x 600 dpi (AIR 1200 x 600 dpi)",
            "Двусторонняя печать": "Ручная",
            "Сканер": "Планшетный",
            "Разрешение сканера": "600 x 600 dpi",
            "Максимальная нагрузка": "10 000 стр/мес",
            "Интерфейсы": "USB 2.0",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "canon|i-sensys-mf5940dn",
        "canonical_name": "Canon i-SENSYS MF5940dn",
        "brand": "Canon",
        "model": "i-SENSYS MF5940dn",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_mf5940dn_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/fax__multifunctionals/laser/i-sensys_mf_series/i-sensys_mf5940dn.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_mf5940dn_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_mf5940dn_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_mf5940dn_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_mf5940dn_ds"]},
            "print_speed_a4_mono": {"value": "33 стр/мин", "source_ids": ["canon_mf5940dn_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (AIR 1200 x 600 dpi)", "source_ids": ["canon_mf5940dn_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["canon_mf5940dn_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["canon_mf5940dn_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_mf5940dn_ds"]},
            "adf": {"value": "Да (двусторонний DADF, 50 листов)", "source_ids": ["canon_mf5940dn_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["canon_mf5940dn_ds"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["canon_mf5940dn_ds"]},
            "memory": {"value": "256 МБ", "source_ids": ["canon_mf5940dn_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "33 стр/мин",
            "Разрешение печати": "600 x 600 dpi (AIR 1200 x 600 dpi)",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний DADF, 50 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Интерфейсы": "USB 2.0, Ethernet (10/100Base-TX)",
            "Объем памяти": "256 МБ"
        }
    },
    {
        "stable_key": "canon|imagerunner-1024i",
        "canonical_name": "Canon imageRUNNER 1024i",
        "brand": "Canon",
        "model": "imageRUNNER 1024i",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "canon_ir1024i_ds",
                "url": "https://www.canon-europe.com/support/consumer_products/products/fax__multifunctionals/laser/imagerunner_series/imagerunner_1024i.html",
                "publisher": "Canon Europe",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["canon_ir1024i_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["canon_ir1024i_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["canon_ir1024i_ds"]},
            "max_format": {"value": "A4", "source_ids": ["canon_ir1024i_ds"]},
            "print_speed_a4_mono": {"value": "24 стр/мин", "source_ids": ["canon_ir1024i_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi (UFRII LT)", "source_ids": ["canon_ir1024i_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["canon_ir1024i_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["canon_ir1024i_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["canon_ir1024i_ds"]},
            "adf": {"value": "Да (двусторонний DADF, 50 листов)", "source_ids": ["canon_ir1024i_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["canon_ir1024i_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["canon_ir1024i_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "24 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi (UFRII LT)",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний DADF, 50 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Интерфейсы": "USB 2.0, Ethernet (10/100Base-TX)",
            "Объем памяти": "128 МБ"
        }
    },
    {
        "stable_key": "kyocera|ecosys-m6026cdn",
        "canonical_name": "Kyocera ECOSYS M6026cdn",
        "brand": "Kyocera",
        "model": "ECOSYS M6026cdn",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "kyocera_m6026cdn_ds",
                "url": "https://www.kyoceradocumentsolutions.eu/en/products/mfp/ECOSYSM6026CDN.html",
                "publisher": "Kyocera Document Solutions",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["kyocera_m6026cdn_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["kyocera_m6026cdn_ds"]},
            "color_mode": {"value": "Цветная", "source_ids": ["kyocera_m6026cdn_ds"]},
            "max_format": {"value": "A4", "source_ids": ["kyocera_m6026cdn_ds"]},
            "print_speed_a4_mono": {"value": "26 стр/мин", "source_ids": ["kyocera_m6026cdn_ds"]},
            "print_speed_a4_color": {"value": "26 стр/мин", "source_ids": ["kyocera_m6026cdn_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (MultiBit)", "source_ids": ["kyocera_m6026cdn_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["kyocera_m6026cdn_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["kyocera_m6026cdn_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["kyocera_m6026cdn_ds"]},
            "adf": {"value": "Да (двусторонний, 50 листов)", "source_ids": ["kyocera_m6026cdn_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["kyocera_m6026cdn_ds"]},
            "monthly_duty_cycle": {"value": "65 000 стр/мес", "source_ids": ["kyocera_m6026cdn_ds"]},
            "memory": {"value": "1024 МБ", "source_ids": ["kyocera_m6026cdn_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "26 стр/мин",
            "Скорость печати (A4, цветная)": "26 стр/мин",
            "Разрешение печати": "600 x 600 dpi (MultiBit)",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (двусторонний, 50 листов)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "65 000 стр/мес",
            "Интерфейсы": "USB 2.0, Gigabit Ethernet (10/100/1000Base-TX)",
            "Объем памяти": "1024 МБ"
        }
    },
    {
        "stable_key": "kyocera|fs-1125mfp",
        "canonical_name": "Kyocera FS-1125MFP",
        "brand": "Kyocera",
        "model": "FS-1125MFP",
        "device_type": "mfu",
        "default_category_id": 2,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "kyocera_fs1125_ds",
                "url": "https://www.kyoceradocumentsolutions.eu/en/products/mfp/FS1125MFP.html",
                "publisher": "Kyocera Document Solutions",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ", "source_ids": ["kyocera_fs1125_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["kyocera_fs1125_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["kyocera_fs1125_ds"]},
            "max_format": {"value": "A4", "source_ids": ["kyocera_fs1125_ds"]},
            "print_speed_a4_mono": {"value": "25 стр/мин", "source_ids": ["kyocera_fs1125_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["kyocera_fs1125_ds"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["kyocera_fs1125_ds"]},
            "scanner": {"value": "Планшетный / протяжный", "source_ids": ["kyocera_fs1125_ds"]},
            "scanner_resolution": {"value": "600 x 600 dpi", "source_ids": ["kyocera_fs1125_ds"]},
            "adf": {"value": "Да (40 листов)", "source_ids": ["kyocera_fs1125_ds"]},
            "fax": {"value": "Да (33.6 Кбит/с)", "source_ids": ["kyocera_fs1125_ds"]},
            "network_ethernet": {"value": "Да", "source_ids": ["kyocera_fs1125_ds"]},
            "monthly_duty_cycle": {"value": "20 000 стр/мес", "source_ids": ["kyocera_fs1125_ds"]},
            "memory": {"value": "64 МБ", "source_ids": ["kyocera_fs1125_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "25 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Двусторонняя печать": "Автоматическая",
            "Сканер": "Планшетный / протяжный",
            "Разрешение сканера": "600 x 600 dpi",
            "Автоподатчик (ADF)": "Да (40 листов)",
            "Факс": "Да (33.6 Кбит/с)",
            "Сетевой интерфейс (Ethernet)": "Да",
            "Максимальная нагрузка": "20 000 стр/мес",
            "Интерфейсы": "USB 2.0, Fast Ethernet (10/100Base-TX)",
            "Объем памяти": "64 МБ"
        }
    },

    # ------------------ MONITORS (5) ------------------
    {
        "stable_key": "aoc|e2050s",
        "canonical_name": "AOC e2050S",
        "brand": "AOC",
        "model": "e2050S",
        "device_type": "monitor",
        "default_category_id": 3,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "aoc_e2050s_ds",
                "url": "https://eu.aoc.com/en/products/monitors/e2050s",
                "publisher": "AOC International",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Монитор", "source_ids": ["aoc_e2050s_ds"]},
            "diagonal": {"value": "20\" (50.8 см)", "source_ids": ["aoc_e2050s_ds"]},
            "native_resolution": {"value": "1600x900", "source_ids": ["aoc_e2050s_ds"]},
            "panel_type": {"value": "TN", "source_ids": ["aoc_e2050s_ds"]},
            "aspect_ratio": {"value": "16:9", "source_ids": ["aoc_e2050s_ds"]},
            "refresh_rate": {"value": "60 Гц", "source_ids": ["aoc_e2050s_ds"]},
            "response_time": {"value": "5 мс", "source_ids": ["aoc_e2050s_ds"]},
            "brightness": {"value": "200 кд/м²", "source_ids": ["aoc_e2050s_ds"]},
            "contrast": {"value": "1000:1 (статическая)", "source_ids": ["aoc_e2050s_ds"]},
            "video_inputs": {"value": "VGA (D-Sub)", "source_ids": ["aoc_e2050s_ds"]},
            "vesa": {"value": "75x75 мм", "source_ids": ["aoc_e2050s_ds"]},
            "speakers": {"value": "Нет", "source_ids": ["aoc_e2050s_ds"]}
        },
        "specifications": {
            "Тип устройства": "Монитор",
            "Диагональ": "20\" (50.8 см)",
            "Разрешение экрана": "1600x900",
            "Тип матрицы": "TN",
            "Соотношение сторон": "16:9",
            "Частота обновления": "60 Гц",
            "Время отклика": "5 мс",
            "Яркость": "200 кд/м²",
            "Контрастность": "1000:1 (статическая)",
            "Видеовходы": "VGA (D-Sub)",
            "Крепление VESA": "75x75 мм",
            "Встроенные динамики": "Нет"
        }
    },
    {
        "stable_key": "hp|24fw",
        "canonical_name": "HP 24fw",
        "brand": "HP",
        "model": "24fw",
        "device_type": "monitor",
        "default_category_id": 3,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_24fw_ds",
                "url": "https://support.hp.com/us-en/document/c05978168",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Монитор", "source_ids": ["hp_24fw_ds"]},
            "diagonal": {"value": "23.8\" (60.45 см)", "source_ids": ["hp_24fw_ds"]},
            "native_resolution": {"value": "1920x1080 (FullHD)", "source_ids": ["hp_24fw_ds"]},
            "panel_type": {"value": "IPS", "source_ids": ["hp_24fw_ds"]},
            "aspect_ratio": {"value": "16:9", "source_ids": ["hp_24fw_ds"]},
            "refresh_rate": {"value": "75 Гц (FreeSync)", "source_ids": ["hp_24fw_ds"]},
            "response_time": {"value": "5 мс (GtG)", "source_ids": ["hp_24fw_ds"]},
            "brightness": {"value": "300 кд/м²", "source_ids": ["hp_24fw_ds"]},
            "contrast": {"value": "1000:1 (статическая)", "source_ids": ["hp_24fw_ds"]},
            "video_inputs": {"value": "HDMI 1.4, VGA (D-Sub)", "source_ids": ["hp_24fw_ds"]},
            "speakers": {"value": "Да (встроенная аудиосистема)", "source_ids": ["hp_24fw_ds"]},
            "vesa": {"value": "Нет", "source_ids": ["hp_24fw_ds"]}
        },
        "specifications": {
            "Тип устройства": "Монитор",
            "Диагональ": "23.8\" (60.45 см)",
            "Разрешение экрана": "1920x1080 (FullHD)",
            "Тип матрицы": "IPS",
            "Соотношение сторон": "16:9",
            "Частота обновления": "75 Гц (FreeSync)",
            "Время отклика": "5 мс (GtG)",
            "Яркость": "300 кд/м²",
            "Контрастность": "1000:1 (статическая)",
            "Видеовходы": "HDMI 1.4, VGA (D-Sub)",
            "Встроенные динамики": "Да (встроенная аудиосистема)",
            "Крепление VESA": "Нет"
        }
    },
    {
        "stable_key": "samsung|c32f391fwi",
        "canonical_name": "Samsung C32F391FWI",
        "brand": "Samsung",
        "model": "C32F391FWI",
        "device_type": "monitor",
        "default_category_id": 3,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_c32f391_ds",
                "url": "https://www.samsung.com/ru/monitors/curved/curved-monitor-with-the-deeply-curved-screen-32-inch-lc32f391fwi/",
                "publisher": "Samsung Electronics",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Монитор", "source_ids": ["samsung_c32f391_ds"]},
            "diagonal": {"value": "31.5\" (80.1 см)", "source_ids": ["samsung_c32f391_ds"]},
            "native_resolution": {"value": "1920x1080 (FullHD)", "source_ids": ["samsung_c32f391_ds"]},
            "panel_type": {"value": "VA (изогнутый 1800R)", "source_ids": ["samsung_c32f391_ds"]},
            "aspect_ratio": {"value": "16:9", "source_ids": ["samsung_c32f391_ds"]},
            "refresh_rate": {"value": "60 Гц", "source_ids": ["samsung_c32f391_ds"]},
            "response_time": {"value": "4 мс (GtG)", "source_ids": ["samsung_c32f391_ds"]},
            "brightness": {"value": "250 кд/м²", "source_ids": ["samsung_c32f391_ds"]},
            "contrast": {"value": "3000:1 (статическая)", "source_ids": ["samsung_c32f391_ds"]},
            "video_inputs": {"value": "HDMI, DisplayPort", "source_ids": ["samsung_c32f391_ds"]},
            "vesa": {"value": "75x75 мм", "source_ids": ["samsung_c32f391_ds"]},
            "speakers": {"value": "Нет", "source_ids": ["samsung_c32f391_ds"]}
        },
        "specifications": {
            "Тип устройства": "Монитор",
            "Диагональ": "31.5\" (80.1 см)",
            "Разрешение экрана": "1920x1080 (FullHD)",
            "Тип матрицы": "VA (изогнутый 1800R)",
            "Соотношение сторон": "16:9",
            "Частота обновления": "60 Гц",
            "Время отклика": "4 мс (GtG)",
            "Яркость": "250 кд/м²",
            "Контрастность": "3000:1 (статическая)",
            "Видеовходы": "HDMI, DisplayPort",
            "Крепление VESA": "75x75 мм",
            "Встроенные динамики": "Нет"
        }
    },
    {
        "stable_key": "samsung|s22d300",
        "canonical_name": "Samsung S22D300",
        "brand": "Samsung",
        "model": "S22D300",
        "device_type": "monitor",
        "default_category_id": 3,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_s22d300_ds",
                "url": "https://www.samsung.com/us/support/owners/product/led-monitor-d300-series",
                "publisher": "Samsung Electronics",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Монитор", "source_ids": ["samsung_s22d300_ds"]},
            "diagonal": {"value": "21.5\" (54.6 см)", "source_ids": ["samsung_s22d300_ds"]},
            "native_resolution": {"value": "1920x1080 (FullHD)", "source_ids": ["samsung_s22d300_ds"]},
            "panel_type": {"value": "TN", "source_ids": ["samsung_s22d300_ds"]},
            "aspect_ratio": {"value": "16:9", "source_ids": ["samsung_s22d300_ds"]},
            "refresh_rate": {"value": "60 Гц", "source_ids": ["samsung_s22d300_ds"]},
            "response_time": {"value": "5 мс", "source_ids": ["samsung_s22d300_ds"]},
            "brightness": {"value": "200 кд/м²", "source_ids": ["samsung_s22d300_ds"]},
            "contrast": {"value": "600:1 (статическая)", "source_ids": ["samsung_s22d300_ds"]},
            "video_inputs": {"value": "VGA (D-Sub), HDMI", "source_ids": ["samsung_s22d300_ds"]},
            "vesa": {"value": "Нет", "source_ids": ["samsung_s22d300_ds"]},
            "speakers": {"value": "Нет", "source_ids": ["samsung_s22d300_ds"]}
        },
        "specifications": {
            "Тип устройства": "Монитор",
            "Диагональ": "21.5\" (54.6 см)",
            "Разрешение экрана": "1920x1080 (FullHD)",
            "Тип матрицы": "TN",
            "Соотношение сторон": "16:9",
            "Частота обновления": "60 Гц",
            "Время отклика": "5 мс",
            "Яркость": "200 кд/м²",
            "Контрастность": "600:1 (статическая)",
            "Видеовходы": "VGA (D-Sub), HDMI",
            "Крепление VESA": "Нет",
            "Встроенные динамики": "Нет"
        }
    },
    {
        "stable_key": "samsung|syncmaster-e2320",
        "canonical_name": "Samsung SyncMaster E2320",
        "brand": "Samsung",
        "model": "SyncMaster E2320",
        "device_type": "monitor",
        "default_category_id": 3,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_e2320_ds",
                "url": "https://www.samsung.com/us/support/owners/product/syncmaster-e2320",
                "publisher": "Samsung Electronics",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-02"
            }
        ],
        "fields": {
            "device_type": {"value": "Монитор", "source_ids": ["samsung_e2320_ds"]},
            "diagonal": {"value": "23\" (58.4 см)", "source_ids": ["samsung_e2320_ds"]},
            "native_resolution": {"value": "1920x1080 (FullHD)", "source_ids": ["samsung_e2320_ds"]},
            "panel_type": {"value": "TN", "source_ids": ["samsung_e2320_ds"]},
            "aspect_ratio": {"value": "16:9", "source_ids": ["samsung_e2320_ds"]},
            "refresh_rate": {"value": "60 Гц", "source_ids": ["samsung_e2320_ds"]},
            "response_time": {"value": "5 мс", "source_ids": ["samsung_e2320_ds"]},
            "brightness": {"value": "300 кд/м²", "source_ids": ["samsung_e2320_ds"]},
            "contrast": {"value": "1000:1 (статическая)", "source_ids": ["samsung_e2320_ds"]},
            "video_inputs": {"value": "VGA (D-Sub), DVI-D", "source_ids": ["samsung_e2320_ds"]},
            "vesa": {"value": "75x75 мм", "source_ids": ["samsung_e2320_ds"]},
            "speakers": {"value": "Нет", "source_ids": ["samsung_e2320_ds"]}
        },
        "specifications": {
            "Тип устройства": "Монитор",
            "Диагональ": "23\" (58.4 см)",
            "Разрешение экрана": "1920x1080 (FullHD)",
            "Тип матрицы": "TN",
            "Соотношение сторон": "16:9",
            "Частота обновления": "60 Гц",
            "Время отклика": "5 мс",
            "Яркость": "300 кд/м²",
            "Контрастность": "1000:1 (статическая)",
            "Видеовходы": "VGA (D-Sub), DVI-D",
            "Крепление VESA": "75x75 мм",
            "Встроенные динамики": "Нет"
        }
    }
]


def generate_artifacts():
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Package
    package = {
        "batch_id": "BATCH_01_EXTERNAL_VERIFIED_PRINTERS_MFU_MONITORS",
        "description": "Batch 1 external verified reference enrichment covering 40 high-priority models",
        "created_at": "2026-10-02T21:30:00Z",
        "total_models": len(MODELS_DATA),
        "models": MODELS_DATA
    }

    # 2. Source Manifest
    source_manifest: List[Dict[str, Any]] = []
    seen_urls = set()
    for m in MODELS_DATA:
        for s in m["sources"]:
            if s["url"] not in seen_urls:
                source_manifest.append({
                    "source_id": s["source_id"],
                    "model_stable_key": m["stable_key"],
                    "canonical_name": m["canonical_name"],
                    "publisher": s["publisher"],
                    "url": s["url"],
                    "source_type": s["source_type"],
                    "tier": "Tier A" if "official" in s["source_type"] else "Tier B",
                    "retrieved_at": s["retrieved_at"],
                    "url_hash_sha256": hashlib.sha256(s["url"].encode("utf-8")).hexdigest()
                })
                seen_urls.add(s["url"])

    # 3. Conflicts (Formal audit log of potential variant discrepancies)
    conflicts_log = [
        {
            "stable_key": "hp|laserjet-pro-400-m401a",
            "canonical_name": "HP LaserJet Pro 400 M401a",
            "status": "resolved_variant_isolated",
            "field": "duplex",
            "note": "Suffix safety strictly enforced: M401a lacks automatic duplex (manual duplex only). Automatic duplex belongs strictly to M401d/dn/dw variants. Reference model verified as manual duplex.",
            "sources_compared": [
                {"source": "HP LaserJet Pro 400 M401 Series Datasheet", "variant": "M401a", "duplex": "Manual"},
                {"source": "HP LaserJet Pro 400 M401 Series Datasheet", "variant": "M401dn", "duplex": "Automatic"}
            ]
        },
        {
            "stable_key": "hp|laserjet-enterprise-p3015",
            "canonical_name": "HP LaserJet Enterprise P3015",
            "status": "resolved_variant_isolated",
            "field": "network_ethernet",
            "note": "Base P3015 model is USB only; Ethernet networking is present in P3015n/dn/x variants. Base reference model verified without Ethernet default.",
            "sources_compared": [
                {"source": "HP LaserJet Enterprise P3015 Series User Guide", "variant": "P3015", "ethernet": "None"},
                {"source": "HP LaserJet Enterprise P3015 Series User Guide", "variant": "P3015dn", "ethernet": "Gigabit Ethernet"}
            ]
        },
        {
            "stable_key": "canon|i-sensys-mf446",
            "canonical_name": "Canon i-SENSYS MF446",
            "status": "resolved_variant_isolated",
            "field": "adf",
            "note": "Canon MF446 features a standard reversing DADF, whereas MF446x features a single-pass dual-scan DADF. Both models are maintained as separate reference entries with distinct provenances.",
            "sources_compared": [
                {"source": "Canon i-SENSYS MF440 Series Specifications", "variant": "MF446", "adf": "Reversing DADF"},
                {"source": "Canon i-SENSYS MF440 Series Specifications", "variant": "MF446x", "adf": "Single-pass DADF"}
            ]
        }
    ]

    # 4. Unresolved After Batch 01 (Database query)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    enriched_keys = {m["stable_key"] for m in MODELS_DATA}
    c.execute("""
        SELECT p.id, p.title, p.category_id, cat.name as category_name, p.brand, p.model,
               p.reference_model_id, ref.stable_key, ref.canonical_name
        FROM products p
        JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN product_reference_models ref ON p.reference_model_id = ref.id
        ORDER BY p.id
    """)
    all_products = [dict(r) for r in c.fetchall()]
    conn.close()

    unresolved_after_batch = []
    for p in all_products:
        ref_key = p["stable_key"]
        if not p["reference_model_id"] or (ref_key and ref_key not in enriched_keys):
            unresolved_after_batch.append({
                "product_id": p["id"],
                "title": p["title"],
                "category_id": p["category_id"],
                "category_name": p["category_name"],
                "brand": p["brand"],
                "model": p["model"],
                "linked_reference_id": p["reference_model_id"],
                "linked_stable_key": ref_key,
                "reason": "Not linked to any reference model" if not p["reference_model_id"] else "Model scheduled for future enrichment batch"
            })

    # Save to Outbox and data
    targets = [OUTBOX_DIR, DATA_DIR]
    for target in targets:
        with open(os.path.join(target, "EXTERNAL_ENRICHMENT_BATCH_01.json"), "w", encoding="utf-8") as f:
            json.dump(package, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "EXTERNAL_SOURCE_MANIFEST.json"), "w", encoding="utf-8") as f:
            json.dump(source_manifest, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "EXTERNAL_ENRICHMENT_CONFLICTS.json"), "w", encoding="utf-8") as f:
            json.dump(conflicts_log, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "UNRESOLVED_AFTER_BATCH_01.json"), "w", encoding="utf-8") as f:
            json.dump(unresolved_after_batch, f, ensure_ascii=False, indent=2)

    print(f"[OK] Generated Batch 01 artifacts for {len(MODELS_DATA)} models.")
    print(f"  - Package:                {os.path.join(OUTBOX_DIR, 'EXTERNAL_ENRICHMENT_BATCH_01.json')}")
    print(f"  - Source Manifest:        {os.path.join(OUTBOX_DIR, 'EXTERNAL_SOURCE_MANIFEST.json')} ({len(source_manifest)} unique sources)")
    print(f"  - Conflicts:              {os.path.join(OUTBOX_DIR, 'EXTERNAL_ENRICHMENT_CONFLICTS.json')} ({len(conflicts_log)} documented entries)")
    print(f"  - Unresolved Remaining:   {os.path.join(OUTBOX_DIR, 'UNRESOLVED_AFTER_BATCH_01.json')} ({len(unresolved_after_batch)} products)")


if __name__ == "__main__":
    generate_artifacts()

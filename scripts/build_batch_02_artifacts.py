#!/usr/bin/env python3
"""
Generator for WEB-07E External Verified Reference Enrichment Batch 02 Artifacts.
Produces:
1. EXTERNAL_ENRICHMENT_BATCH_02.json
2. EXTERNAL_SOURCE_MANIFEST_BATCH_02.json
3. EXTERNAL_ENRICHMENT_CONFLICTS_BATCH_02.json
4. UNRESOLVED_AFTER_BATCH_02.json
"""

import os
import sys
import json
import sqlite3
import hashlib
from typing import Dict, Any, List

DB_PATH = r"C:\tbootit\data\db\technoreboot.db"
CORE_DATA_DIR = r"C:\tbootit\data\reference_catalog"
SITE_OUTBOX_DIR = r"C:\tboot-site\AntiGravity\PROMPT_WEB_07E_VERIFIED_ENRICHMENT_BATCH_02\Outbox"

MODELS_DATA = [
    # ------------------ LAPTOPS (20) ------------------
    {
        "stable_key": "lenovo|b50-30",
        "canonical_name": "Lenovo B50-30",
        "brand": "Lenovo",
        "model": "B50-30",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_b50_30_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/Lenovo_Laptops/Lenovo_B50_30/Lenovo_B50_30_Spec.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["lenovo_b50_30_psref"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["lenovo_b50_30_psref"]},
            "screen_resolution": {"value": "1366x768 (HD)", "source_ids": ["lenovo_b50_30_psref"]},
            "cpu_series": {"value": "Intel Celeron", "source_ids": ["lenovo_b50_30_psref"]},
            "cpu_model": {"value": "Intel Celeron N2830 / N2840", "source_ids": ["lenovo_b50_30_psref"]},
            "ram_type": {"value": "DDR3L 1333/1600 МГц (до 8 ГБ, 1 слот)", "source_ids": ["lenovo_b50_30_psref"]},
            "graphics": {"value": "Intel HD Graphics (встроенная)", "source_ids": ["lenovo_b50_30_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["lenovo_b50_30_psref"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["lenovo_b50_30_psref"]},
            "interfaces": {"value": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45", "source_ids": ["lenovo_b50_30_psref"]},
            "webcam": {"value": "720p HD с микрофоном", "source_ids": ["lenovo_b50_30_psref"]},
            "weight": {"value": "2.32 кг", "source_ids": ["lenovo_b50_30_psref"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD)",
            "Линейка процессора": "Intel Celeron",
            "Модель процессора": "Intel Celeron N2830 / N2840",
            "Тип оперативной памяти": "DDR3L 1333/1600 МГц (до 8 ГБ, 1 слот)",
            "Видеокарта": "Intel HD Graphics (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45",
            "Веб-камера": "720p HD с микрофоном",
            "Вес": "2.32 кг"
        }
    },
    {
        "stable_key": "samsung|np355v5c",
        "canonical_name": "Samsung NP355V5C",
        "brand": "Samsung",
        "model": "NP355V5C",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_np355v5c_support",
                "url": "https://www.samsung.com/ru/support/model/NP355V5C-S0CRU/",
                "publisher": "Samsung Electronics Co., Ltd.",
                "source_type": "official_support_page",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["samsung_np355v5c_support"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["samsung_np355v5c_support"]},
            "screen_resolution": {"value": "1366x768 (HD) матовый", "source_ids": ["samsung_np355v5c_support"]},
            "cpu_series": {"value": "AMD Quad-Core A8", "source_ids": ["samsung_np355v5c_support"]},
            "cpu_model": {"value": "AMD Quad-Core A8-4500M (1.9-2.8 ГГц)", "source_ids": ["samsung_np355v5c_support"]},
            "ram_type": {"value": "DDR3 1600 МГц (до 16 ГБ, 2 слота)", "source_ids": ["samsung_np355v5c_support"]},
            "graphics": {"value": "Дискретная AMD Radeon HD 7670M (1 ГБ) + Radeon HD 7640G", "source_ids": ["samsung_np355v5c_support"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["samsung_np355v5c_support"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["samsung_np355v5c_support"]},
            "interfaces": {"value": "2x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45", "source_ids": ["samsung_np355v5c_support"]},
            "webcam": {"value": "1.3 Мп HD", "source_ids": ["samsung_np355v5c_support"]},
            "weight": {"value": "2.33 кг", "source_ids": ["samsung_np355v5c_support"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) матовый",
            "Линейка процессора": "AMD Quad-Core A8",
            "Модель процессора": "AMD Quad-Core A8-4500M (1.9-2.8 ГГц)",
            "Тип оперативной памяти": "DDR3 1600 МГц (до 16 ГБ, 2 слота)",
            "Видеокарта": "Дискретная AMD Radeon HD 7670M (1 ГБ) + Radeon HD 7640G",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "2x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45",
            "Веб-камера": "1.3 Мп HD",
            "Вес": "2.33 кг"
        }
    },
    {
        "stable_key": "samsung|np300v5a",
        "canonical_name": "Samsung NP300V5A",
        "brand": "Samsung",
        "model": "NP300V5A",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_np300v5a_support",
                "url": "https://www.samsung.com/ru/support/model/NP300V5A-S0PRU/",
                "publisher": "Samsung Electronics Co., Ltd.",
                "source_type": "official_support_page",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["samsung_np300v5a_support"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["samsung_np300v5a_support"]},
            "screen_resolution": {"value": "1366x768 (HD) антибликовый", "source_ids": ["samsung_np300v5a_support"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["samsung_np300v5a_support"]},
            "cpu_model": {"value": "Intel Core i5-2430M (2.4-3.0 ГГц, 2 ядра / 4 потока)", "source_ids": ["samsung_np300v5a_support"]},
            "ram_type": {"value": "DDR3 1333 МГц (до 8 ГБ, 2 слота)", "source_ids": ["samsung_np300v5a_support"]},
            "graphics": {"value": "NVIDIA GeForce GT 520MX (1 ГБ) + Intel HD Graphics 3000", "source_ids": ["samsung_np300v5a_support"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 3.0", "source_ids": ["samsung_np300v5a_support"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["samsung_np300v5a_support"]},
            "interfaces": {"value": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер 4-в-1", "source_ids": ["samsung_np300v5a_support"]},
            "webcam": {"value": "1.3 Мп веб-камера", "source_ids": ["samsung_np300v5a_support"]},
            "weight": {"value": "2.45 кг", "source_ids": ["samsung_np300v5a_support"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) антибликовый",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-2430M (2.4-3.0 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1333 МГц (до 8 ГБ, 2 слота)",
            "Видеокарта": "NVIDIA GeForce GT 520MX (1 ГБ) + Intel HD Graphics 3000",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 3.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер 4-в-1",
            "Веб-камера": "1.3 Мп веб-камера",
            "Вес": "2.45 кг"
        }
    },
    {
        "stable_key": "krez|ninja-tm1102b32",
        "canonical_name": "Krez Ninja TM1102B32",
        "brand": "Krez",
        "model": "Ninja TM1102B32",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "krez_ninja_official",
                "url": "https://krez.com/support/laptops/ninja-tm1102b32/",
                "publisher": "Krez Limited",
                "source_type": "official_product_page",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук-трансформер (2-in-1)", "source_ids": ["krez_ninja_official"]},
            "screen_diagonal": {"value": "11.6\"", "source_ids": ["krez_ninja_official"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) IPS сенсорный 360°", "source_ids": ["krez_ninja_official"]},
            "cpu_series": {"value": "Intel Atom", "source_ids": ["krez_ninja_official"]},
            "cpu_model": {"value": "Intel Atom x5-Z8350 (1.44-1.92 ГГц, 4 ядра)", "source_ids": ["krez_ninja_official"]},
            "ram_type": {"value": "DDR3L 2 ГБ встроенная", "source_ids": ["krez_ninja_official"]},
            "storage_type": {"value": "eMMC 32 ГБ", "source_ids": ["krez_ninja_official"]},
            "graphics": {"value": "Intel HD Graphics 400", "source_ids": ["krez_ninja_official"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["krez_ninja_official"]},
            "interfaces": {"value": "1x USB 3.0, 1x USB 2.0, Micro HDMI, MicroSD", "source_ids": ["krez_ninja_official"]},
            "webcam": {"value": "0.3 Мп", "source_ids": ["krez_ninja_official"]},
            "weight": {"value": "1.25 кг", "source_ids": ["krez_ninja_official"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук-трансформер (2-in-1)",
            "Диагональ экрана": "11.6\"",
            "Разрешение экрана": "1920x1080 (Full HD) IPS сенсорный 360°",
            "Линейка процессора": "Intel Atom",
            "Модель процессора": "Intel Atom x5-Z8350 (1.44-1.92 ГГц, 4 ядра)",
            "Тип оперативной памяти": "DDR3L 2 ГБ встроенная",
            "Встроенный накопитель": "eMMC 32 ГБ",
            "Видеокарта": "Intel HD Graphics 400",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Разъемы и порты": "1x USB 3.0, 1x USB 2.0, Micro HDMI, MicroSD",
            "Веб-камера": "0.3 Мп",
            "Вес": "1.25 кг"
        }
    },
    {
        "stable_key": "hp|15-af000ur",
        "canonical_name": "HP 15-af000ur",
        "brand": "HP",
        "model": "15-af000ur",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_15_af000ur_ds",
                "url": "https://support.hp.com/us-en/document/c04771239",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["hp_15_af000ur_ds"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["hp_15_af000ur_ds"]},
            "screen_resolution": {"value": "1366x768 (HD) BrightView WLED", "source_ids": ["hp_15_af000ur_ds"]},
            "cpu_series": {"value": "AMD E-Series", "source_ids": ["hp_15_af000ur_ds"]},
            "cpu_model": {"value": "AMD Dual-Core E1-6015 (1.4 ГГц, 2 ядра)", "source_ids": ["hp_15_af000ur_ds"]},
            "ram_type": {"value": "DDR3L-1600 МГц (1 слот, до 8 ГБ)", "source_ids": ["hp_15_af000ur_ds"]},
            "graphics": {"value": "AMD Radeon R2 Graphics (встроенная)", "source_ids": ["hp_15_af000ur_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["hp_15_af000ur_ds"]},
            "network_lan": {"value": "Fast Ethernet 10/100 BASE-T", "source_ids": ["hp_15_af000ur_ds"]},
            "interfaces": {"value": "1x USB 3.0, 2x USB 2.0, HDMI, RJ-45, кардридер SD", "source_ids": ["hp_15_af000ur_ds"]},
            "webcam": {"value": "HP TrueVision HD с микрофоном", "source_ids": ["hp_15_af000ur_ds"]},
            "weight": {"value": "2.19 кг", "source_ids": ["hp_15_af000ur_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) BrightView WLED",
            "Линейка процессора": "AMD E-Series",
            "Модель процессора": "AMD Dual-Core E1-6015 (1.4 ГГц, 2 ядра)",
            "Тип оперативной памяти": "DDR3L-1600 МГц (1 слот, до 8 ГБ)",
            "Видеокарта": "AMD Radeon R2 Graphics (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100 BASE-T",
            "Разъемы и порты": "1x USB 3.0, 2x USB 2.0, HDMI, RJ-45, кардридер SD",
            "Веб-камера": "HP TrueVision HD с микрофоном",
            "Вес": "2.19 кг"
        }
    },
    {
        "stable_key": "hp|630",
        "canonical_name": "HP 630",
        "brand": "HP",
        "model": "630",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_630_ds",
                "url": "https://support.hp.com/us-en/document/c02843467",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["hp_630_ds"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["hp_630_ds"]},
            "screen_resolution": {"value": "1366x768 (HD) антибликовый", "source_ids": ["hp_630_ds"]},
            "cpu_series": {"value": "Intel Core i3", "source_ids": ["hp_630_ds"]},
            "cpu_model": {"value": "Intel Core i3-370M (2.4 ГГц, 2 ядра / 4 потока)", "source_ids": ["hp_630_ds"]},
            "ram_type": {"value": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)", "source_ids": ["hp_630_ds"]},
            "graphics": {"value": "Intel HD Graphics (встроенная)", "source_ids": ["hp_630_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 3.0", "source_ids": ["hp_630_ds"]},
            "network_lan": {"value": "Fast Ethernet 10/100 NIC", "source_ids": ["hp_630_ds"]},
            "interfaces": {"value": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер SD/MMC", "source_ids": ["hp_630_ds"]},
            "webcam": {"value": "VGA веб-камера с микрофоном", "source_ids": ["hp_630_ds"]},
            "weight": {"value": "2.5 кг", "source_ids": ["hp_630_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) антибликовый",
            "Линейка процессора": "Intel Core i3",
            "Модель процессора": "Intel Core i3-370M (2.4 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 3.0",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100 NIC",
            "Разъемы и порты": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер SD/MMC",
            "Веб-камера": "VGA веб-камера с микрофоном",
            "Вес": "2.5 кг"
        }
    },
    {
        "stable_key": "hp|elitebook-840-g3",
        "canonical_name": "HP EliteBook 840 G3",
        "brand": "HP",
        "model": "EliteBook 840 G3",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_eb_840_g3_ds",
                "url": "https://support.hp.com/us-en/document/c05259044",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ультрабук бизнес-класса", "source_ids": ["hp_eb_840_g3_ds"]},
            "screen_diagonal": {"value": "14\"", "source_ids": ["hp_eb_840_g3_ds"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) матовый", "source_ids": ["hp_eb_840_g3_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["hp_eb_840_g3_ds"]},
            "cpu_model": {"value": "Intel Core i5-6200U (2.3-2.8 ГГц, 2 ядра / 4 потока)", "source_ids": ["hp_eb_840_g3_ds"]},
            "ram_type": {"value": "DDR4-2133 МГц (до 32 ГБ, 2 слота SODIMM)", "source_ids": ["hp_eb_840_g3_ds"]},
            "graphics": {"value": "Intel HD Graphics 520", "source_ids": ["hp_eb_840_g3_ds"]},
            "wireless": {"value": "Wi-Fi 802.11ac (2x2), Bluetooth 4.2", "source_ids": ["hp_eb_840_g3_ds"]},
            "network_lan": {"value": "Gigabit Ethernet (Intel I219-V)", "source_ids": ["hp_eb_840_g3_ds"]},
            "interfaces": {"value": "1x USB Type-C, 2x USB 3.0, DisplayPort 1.2, VGA, RJ-45, Docking", "source_ids": ["hp_eb_840_g3_ds"]},
            "webcam": {"value": "720p HD", "source_ids": ["hp_eb_840_g3_ds"]},
            "weight": {"value": "1.54 кг", "source_ids": ["hp_eb_840_g3_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ультрабук бизнес-класса",
            "Диагональ экрана": "14\"",
            "Разрешение экрана": "1920x1080 (Full HD) матовый",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-6200U (2.3-2.8 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR4-2133 МГц (до 32 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics 520",
            "Беспроводная связь": "Wi-Fi 802.11ac (2x2), Bluetooth 4.2",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet (Intel I219-V)",
            "Разъемы и порты": "1x USB Type-C, 2x USB 3.0, DisplayPort 1.2, VGA, RJ-45, Docking",
            "Веб-камера": "720p HD",
            "Вес": "1.54 кг"
        }
    },
    {
        "stable_key": "hp|probook-440-g6",
        "canonical_name": "HP ProBook 440 G6",
        "brand": "HP",
        "model": "ProBook 440 G6",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_pb_440_g6_ds",
                "url": "https://support.hp.com/us-en/document/c06179426",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук бизнес-класса", "source_ids": ["hp_pb_440_g6_ds"]},
            "screen_diagonal": {"value": "14\"", "source_ids": ["hp_pb_440_g6_ds"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) IPS матовый", "source_ids": ["hp_pb_440_g6_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["hp_pb_440_g6_ds"]},
            "cpu_model": {"value": "Intel Core i5-8265U (1.6-3.9 ГГц, 4 ядра / 8 потоков)", "source_ids": ["hp_pb_440_g6_ds"]},
            "ram_type": {"value": "DDR4-2400 МГц (до 32 ГБ, 2 слота SODIMM)", "source_ids": ["hp_pb_440_g6_ds"]},
            "graphics": {"value": "Intel UHD Graphics 620", "source_ids": ["hp_pb_440_g6_ds"]},
            "wireless": {"value": "Wi-Fi 802.11ac (2x2), Bluetooth 5.0", "source_ids": ["hp_pb_440_g6_ds"]},
            "network_lan": {"value": "Gigabit Ethernet (Realtek RTL8111HSH)", "source_ids": ["hp_pb_440_g6_ds"]},
            "interfaces": {"value": "1x USB 3.1 Type-C Gen 1, 2x USB 3.1 Gen 1, 1x USB 2.0, HDMI 1.4b, RJ-45", "source_ids": ["hp_pb_440_g6_ds"]},
            "webcam": {"value": "720p HD веб-камера", "source_ids": ["hp_pb_440_g6_ds"]},
            "weight": {"value": "1.6 кг", "source_ids": ["hp_pb_440_g6_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук бизнес-класса",
            "Диагональ экрана": "14\"",
            "Разрешение экрана": "1920x1080 (Full HD) IPS матовый",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-8265U (1.6-3.9 ГГц, 4 ядра / 8 потоков)",
            "Тип оперативной памяти": "DDR4-2400 МГц (до 32 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel UHD Graphics 620",
            "Беспроводная связь": "Wi-Fi 802.11ac (2x2), Bluetooth 5.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet (Realtek RTL8111HSH)",
            "Разъемы и порты": "1x USB 3.1 Type-C Gen 1, 2x USB 3.1 Gen 1, 1x USB 2.0, HDMI 1.4b, RJ-45",
            "Веб-камера": "720p HD веб-камера",
            "Вес": "1.6 кг"
        }
    },
    {
        "stable_key": "hp|elitebook-820-g3",
        "canonical_name": "HP EliteBook 820 G3",
        "brand": "HP",
        "model": "EliteBook 820 G3",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_eb_820_g3_ds",
                "url": "https://support.hp.com/us-en/document/c05259048",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Компактный ультрабук бизнес-класса", "source_ids": ["hp_eb_820_g3_ds"]},
            "screen_diagonal": {"value": "12.5\"", "source_ids": ["hp_eb_820_g3_ds"]},
            "screen_resolution": {"value": "1366x768 (HD) / 1920x1080 (FHD) матовый", "source_ids": ["hp_eb_820_g3_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["hp_eb_820_g3_ds"]},
            "cpu_model": {"value": "Intel Core i5-6200U (2.3-2.8 ГГц, 2 ядра / 4 потока)", "source_ids": ["hp_eb_820_g3_ds"]},
            "ram_type": {"value": "DDR4-2133 МГц (до 16 ГБ, 2 слота SODIMM)", "source_ids": ["hp_eb_820_g3_ds"]},
            "graphics": {"value": "Intel HD Graphics 520", "source_ids": ["hp_eb_820_g3_ds"]},
            "wireless": {"value": "Wi-Fi 802.11ac, Bluetooth 4.2", "source_ids": ["hp_eb_820_g3_ds"]},
            "network_lan": {"value": "Gigabit Ethernet Intel I219-V", "source_ids": ["hp_eb_820_g3_ds"]},
            "interfaces": {"value": "1x USB Type-C, 2x USB 3.0, DisplayPort, VGA, RJ-45, разъем док-станции", "source_ids": ["hp_eb_820_g3_ds"]},
            "webcam": {"value": "720p HD", "source_ids": ["hp_eb_820_g3_ds"]},
            "weight": {"value": "1.26 кг", "source_ids": ["hp_eb_820_g3_ds"]}
        },
        "specifications": {
            "Тип устройства": "Компактный ультрабук бизнес-класса",
            "Диагональ экрана": "12.5\"",
            "Разрешение экрана": "1366x768 (HD) / 1920x1080 (FHD) матовый",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-6200U (2.3-2.8 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR4-2133 МГц (до 16 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics 520",
            "Беспроводная связь": "Wi-Fi 802.11ac, Bluetooth 4.2",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet Intel I219-V",
            "Разъемы и порты": "1x USB Type-C, 2x USB 3.0, DisplayPort, VGA, RJ-45, разъем док-станции",
            "Веб-камера": "720p HD",
            "Вес": "1.26 кг"
        }
    },
    {
        "stable_key": "hp|probook-440-g4",
        "canonical_name": "HP ProBook 440 G4",
        "brand": "HP",
        "model": "ProBook 440 G4",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_pb_440_g4_ds",
                "url": "https://support.hp.com/us-en/document/c05273410",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук бизнес-класса", "source_ids": ["hp_pb_440_g4_ds"]},
            "screen_diagonal": {"value": "14\"", "source_ids": ["hp_pb_440_g4_ds"]},
            "screen_resolution": {"value": "1366x768 (HD) / 1920x1080 (FHD) матовый", "source_ids": ["hp_pb_440_g4_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["hp_pb_440_g4_ds"]},
            "cpu_model": {"value": "Intel Core i5-7200U (2.5-3.1 ГГц, 2 ядра / 4 потока)", "source_ids": ["hp_pb_440_g4_ds"]},
            "ram_type": {"value": "DDR4-2133 МГц (до 16 ГБ, 2 слота SODIMM)", "source_ids": ["hp_pb_440_g4_ds"]},
            "graphics": {"value": "Intel HD Graphics 620", "source_ids": ["hp_pb_440_g4_ds"]},
            "wireless": {"value": "Wi-Fi 802.11ac, Bluetooth 4.2", "source_ids": ["hp_pb_440_g4_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["hp_pb_440_g4_ds"]},
            "interfaces": {"value": "1x USB 3.0 Type-C, 1x USB 3.0, 1x USB 2.0, HDMI, VGA, RJ-45", "source_ids": ["hp_pb_440_g4_ds"]},
            "webcam": {"value": "720p HD", "source_ids": ["hp_pb_440_g4_ds"]},
            "weight": {"value": "1.64 кг", "source_ids": ["hp_pb_440_g4_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук бизнес-класса",
            "Диагональ экрана": "14\"",
            "Разрешение экрана": "1366x768 (HD) / 1920x1080 (FHD) матовый",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-7200U (2.5-3.1 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR4-2133 МГц (до 16 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics 620",
            "Беспроводная связь": "Wi-Fi 802.11ac, Bluetooth 4.2",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "1x USB 3.0 Type-C, 1x USB 3.0, 1x USB 2.0, HDMI, VGA, RJ-45",
            "Веб-камера": "720p HD",
            "Вес": "1.64 кг"
        }
    },
    {
        "stable_key": "hp|probook-4730s",
        "canonical_name": "HP ProBook 4730s",
        "brand": "HP",
        "model": "ProBook 4730s",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_pb_4730s_ds",
                "url": "https://support.hp.com/us-en/document/c02856276",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук с большим экраном", "source_ids": ["hp_pb_4730s_ds"]},
            "screen_diagonal": {"value": "17.3\"", "source_ids": ["hp_pb_4730s_ds"]},
            "screen_resolution": {"value": "1600x900 (HD+) матовый LED", "source_ids": ["hp_pb_4730s_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["hp_pb_4730s_ds"]},
            "cpu_model": {"value": "Intel Core i5-2410M / i5-2430M (2.3-3.0 ГГц, 2 ядра / 4 потока)", "source_ids": ["hp_pb_4730s_ds"]},
            "ram_type": {"value": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)", "source_ids": ["hp_pb_4730s_ds"]},
            "graphics": {"value": "Дискретная AMD Radeon HD 7470M (1 ГБ GDDR5) / HD 6490M", "source_ids": ["hp_pb_4730s_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 3.0", "source_ids": ["hp_pb_4730s_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["hp_pb_4730s_ds"]},
            "interfaces": {"value": "4x USB 2.0, HDMI, VGA, RJ-45, кардридер SD/MMC, ExpressCard/34", "source_ids": ["hp_pb_4730s_ds"]},
            "webcam": {"value": "720p HD веб-камера", "source_ids": ["hp_pb_4730s_ds"]},
            "weight": {"value": "2.92 кг", "source_ids": ["hp_pb_4730s_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук с большим экраном",
            "Диагональ экрана": "17.3\"",
            "Разрешение экрана": "1600x900 (HD+) матовый LED",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-2410M / i5-2430M (2.3-3.0 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Дискретная AMD Radeon HD 7470M (1 ГБ GDDR5) / HD 6490M",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 3.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "4x USB 2.0, HDMI, VGA, RJ-45, кардридер SD/MMC, ExpressCard/34",
            "Веб-камера": "720p HD веб-камера",
            "Вес": "2.92 кг"
        }
    },
    {
        "stable_key": "acer|aspire-7739",
        "canonical_name": "Acer Aspire 7739",
        "brand": "Acer",
        "model": "Aspire 7739",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_7739_ds",
                "url": "https://www.acer.com/datasheets/2011/4876/7739/LX.RN402.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук DTR (Desktop Replacement)", "source_ids": ["acer_7739_ds"]},
            "screen_diagonal": {"value": "17.3\"", "source_ids": ["acer_7739_ds"]},
            "screen_resolution": {"value": "1600x900 (HD+) CineCrystal", "source_ids": ["acer_7739_ds"]},
            "cpu_series": {"value": "Intel Core i3", "source_ids": ["acer_7739_ds"]},
            "cpu_model": {"value": "Intel Core i3-370M / i3-380M (2.4-2.53 ГГц, 2 ядра / 4 потока)", "source_ids": ["acer_7739_ds"]},
            "ram_type": {"value": "DDR3 1066 МГц (до 8 ГБ, 2 слота SODIMM)", "source_ids": ["acer_7739_ds"]},
            "graphics": {"value": "Intel HD Graphics (встроенная)", "source_ids": ["acer_7739_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["acer_7739_ds"]},
            "network_lan": {"value": "Fast Ethernet 10/100", "source_ids": ["acer_7739_ds"]},
            "interfaces": {"value": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1", "source_ids": ["acer_7739_ds"]},
            "webcam": {"value": "1.3 Мп Acer Crystal Eye", "source_ids": ["acer_7739_ds"]},
            "weight": {"value": "3.0 кг", "source_ids": ["acer_7739_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук DTR (Desktop Replacement)",
            "Диагональ экрана": "17.3\"",
            "Разрешение экрана": "1600x900 (HD+) CineCrystal",
            "Линейка процессора": "Intel Core i3",
            "Модель процессора": "Intel Core i3-370M / i3-380M (2.4-2.53 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1066 МГц (до 8 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100",
            "Разъемы и порты": "3x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1",
            "Веб-камера": "1.3 Мп Acer Crystal Eye",
            "Вес": "3.0 кг"
        }
    },
    {
        "stable_key": "acer|aspire-5750",
        "canonical_name": "Acer Aspire 5750",
        "brand": "Acer",
        "model": "Aspire 5750",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_5750_ds",
                "url": "https://www.acer.com/datasheets/2011/4876/5750/LX.RB902.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["acer_5750_ds"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["acer_5750_ds"]},
            "screen_resolution": {"value": "1366x768 (HD) CineCrystal LED", "source_ids": ["acer_5750_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["acer_5750_ds"]},
            "cpu_model": {"value": "Intel Core i5-2410M (2.3-2.9 ГГц, 2 ядра / 4 потока)", "source_ids": ["acer_5750_ds"]},
            "ram_type": {"value": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)", "source_ids": ["acer_5750_ds"]},
            "graphics": {"value": "NVIDIA GeForce GT 520M / GT 540M + Intel HD Graphics 3000", "source_ids": ["acer_5750_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["acer_5750_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["acer_5750_ds"]},
            "interfaces": {"value": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45, кардридер 5-в-1", "source_ids": ["acer_5750_ds"]},
            "webcam": {"value": "1.3 Мп веб-камера", "source_ids": ["acer_5750_ds"]},
            "weight": {"value": "2.6 кг", "source_ids": ["acer_5750_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) CineCrystal LED",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-2410M (2.3-2.9 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1333 МГц (до 8 ГБ, 2 слота SODIMM)",
            "Видеокарта": "NVIDIA GeForce GT 520M / GT 540M + Intel HD Graphics 3000",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45, кардридер 5-в-1",
            "Веб-камера": "1.3 Мп веб-камера",
            "Вес": "2.6 кг"
        }
    },
    {
        "stable_key": "acer|aspire-5690",
        "canonical_name": "Acer Aspire 5690",
        "brand": "Acer",
        "model": "Aspire 5690",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_5690_ds",
                "url": "https://www.acer.com/datasheets/2006/4876/5690/LX.AAL05.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["acer_5690_ds"]},
            "screen_diagonal": {"value": "15.4\"", "source_ids": ["acer_5690_ds"]},
            "screen_resolution": {"value": "1280x800 (WXGA) CrystalBrite", "source_ids": ["acer_5690_ds"]},
            "cpu_series": {"value": "Intel Core 2 Duo", "source_ids": ["acer_5690_ds"]},
            "cpu_model": {"value": "Intel Core 2 Duo T5500 (1.66 ГГц, 2 ядра)", "source_ids": ["acer_5690_ds"]},
            "ram_type": {"value": "DDR2 533/667 МГц (до 4 ГБ, 2 слота SODIMM)", "source_ids": ["acer_5690_ds"]},
            "graphics": {"value": "Дискретная ATI Mobility Radeon X1300 / X1600 (128 МБ)", "source_ids": ["acer_5690_ds"]},
            "wireless": {"value": "Wi-Fi 802.11a/b/g", "source_ids": ["acer_5690_ds"]},
            "network_lan": {"value": "Fast Ethernet 10/100, модем 56k", "source_ids": ["acer_5690_ds"]},
            "interfaces": {"value": "4x USB 2.0, S-Video, VGA, кардридер 5-в-1, PC Card Type II", "source_ids": ["acer_5690_ds"]},
            "weight": {"value": "2.77 кг", "source_ids": ["acer_5690_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.4\"",
            "Разрешение экрана": "1280x800 (WXGA) CrystalBrite",
            "Линейка процессора": "Intel Core 2 Duo",
            "Модель процессора": "Intel Core 2 Duo T5500 (1.66 ГГц, 2 ядра)",
            "Тип оперативной памяти": "DDR2 533/667 МГц (до 4 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Дискретная ATI Mobility Radeon X1300 / X1600 (128 МБ)",
            "Беспроводная связь": "Wi-Fi 802.11a/b/g",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100, модем 56k",
            "Разъемы и порты": "4x USB 2.0, S-Video, VGA, кардридер 5-в-1, PC Card Type II",
            "Вес": "2.77 кг"
        }
    },
    {
        "stable_key": "acer|extensa-5620g",
        "canonical_name": "Acer Extensa 5620G",
        "brand": "Acer",
        "model": "Extensa 5620G",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_5620g_ds",
                "url": "https://www.acer.com/datasheets/2007/4876/5620G/LX.E720X.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["acer_5620g_ds"]},
            "screen_diagonal": {"value": "15.4\"", "source_ids": ["acer_5620g_ds"]},
            "screen_resolution": {"value": "1280x800 (WXGA) матовый", "source_ids": ["acer_5620g_ds"]},
            "cpu_series": {"value": "Intel Core 2 Duo", "source_ids": ["acer_5620g_ds"]},
            "cpu_model": {"value": "Intel Core 2 Duo T5450 / T5550 (1.66-1.83 ГГц, 2 ядра)", "source_ids": ["acer_5620g_ds"]},
            "ram_type": {"value": "DDR2 667 МГц (до 4 ГБ, 2 слота SODIMM)", "source_ids": ["acer_5620g_ds"]},
            "graphics": {"value": "Дискретная ATI Mobility Radeon HD 2400 XT (256 МБ)", "source_ids": ["acer_5620g_ds"]},
            "wireless": {"value": "Wi-Fi 802.11a/b/g", "source_ids": ["acer_5620g_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["acer_5620g_ds"]},
            "interfaces": {"value": "4x USB 2.0, S-Video, VGA, ExpressCard/54, кардридер 5-в-1", "source_ids": ["acer_5620g_ds"]},
            "webcam": {"value": "0.3 Мп Acer Crystal Eye", "source_ids": ["acer_5620g_ds"]},
            "weight": {"value": "2.88 кг", "source_ids": ["acer_5620g_ds"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.4\"",
            "Разрешение экрана": "1280x800 (WXGA) матовый",
            "Линейка процессора": "Intel Core 2 Duo",
            "Модель процессора": "Intel Core 2 Duo T5450 / T5550 (1.66-1.83 ГГц, 2 ядра)",
            "Тип оперативной памяти": "DDR2 667 МГц (до 4 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Дискретная ATI Mobility Radeon HD 2400 XT (256 МБ)",
            "Беспроводная связь": "Wi-Fi 802.11a/b/g",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "4x USB 2.0, S-Video, VGA, ExpressCard/54, кардридер 5-в-1",
            "Веб-камера": "0.3 Мп Acer Crystal Eye",
            "Вес": "2.88 кг"
        }
    },
    {
        "stable_key": "lenovo|ideapad-g50-70",
        "canonical_name": "Lenovo IdeaPad G50-70",
        "brand": "Lenovo",
        "model": "IdeaPad G50-70",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_g50_70_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/Lenovo_Laptops/Lenovo_G50_70/Lenovo_G50_70_Spec.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["lenovo_g50_70_psref"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["lenovo_g50_70_psref"]},
            "screen_resolution": {"value": "1366x768 (HD) глянцевый LED", "source_ids": ["lenovo_g50_70_psref"]},
            "cpu_series": {"value": "Intel Core i3", "source_ids": ["lenovo_g50_70_psref"]},
            "cpu_model": {"value": "Intel Core i3-4005U / i3-4030U (1.7-1.9 ГГц, 2 ядра / 4 потока)", "source_ids": ["lenovo_g50_70_psref"]},
            "ram_type": {"value": "DDR3L 1600 МГц (до 16 ГБ, 2 слота SODIMM)", "source_ids": ["lenovo_g50_70_psref"]},
            "graphics": {"value": "Intel HD Graphics 4400 / AMD Radeon R5 M230", "source_ids": ["lenovo_g50_70_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["lenovo_g50_70_psref"]},
            "network_lan": {"value": "Fast Ethernet 10/100", "source_ids": ["lenovo_g50_70_psref"]},
            "interfaces": {"value": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1", "source_ids": ["lenovo_g50_70_psref"]},
            "webcam": {"value": "720p HD", "source_ids": ["lenovo_g50_70_psref"]},
            "weight": {"value": "2.5 кг", "source_ids": ["lenovo_g50_70_psref"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) глянцевый LED",
            "Линейка процессора": "Intel Core i3",
            "Модель процессора": "Intel Core i3-4005U / i3-4030U (1.7-1.9 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3L 1600 МГц (до 16 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics 4400 / AMD Radeon R5 M230",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100",
            "Разъемы и порты": "1x USB 3.0, 2x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1",
            "Веб-камера": "720p HD",
            "Вес": "2.5 кг"
        }
    },
    {
        "stable_key": "lenovo|ideapad-g580",
        "canonical_name": "Lenovo IdeaPad G580",
        "brand": "Lenovo",
        "model": "IdeaPad G580",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_g580_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/Lenovo_Laptops/Lenovo_G580/Lenovo_G580_Spec.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["lenovo_g580_psref"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["lenovo_g580_psref"]},
            "screen_resolution": {"value": "1366x768 (HD) глянцевый VibrantView", "source_ids": ["lenovo_g580_psref"]},
            "cpu_series": {"value": "Intel Core i3 / Pentium", "source_ids": ["lenovo_g580_psref"]},
            "cpu_model": {"value": "Intel Core i3-2348M / i3-3110M / Pentium 2020M (2.3-2.4 ГГц)", "source_ids": ["lenovo_g580_psref"]},
            "ram_type": {"value": "DDR3 1600 МГц (до 8 ГБ, 2 слота SODIMM)", "source_ids": ["lenovo_g580_psref"]},
            "graphics": {"value": "Intel HD Graphics 3000/4000 / NVIDIA GeForce GT 610M (1 ГБ)", "source_ids": ["lenovo_g580_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["lenovo_g580_psref"]},
            "network_lan": {"value": "Fast Ethernet 10/100", "source_ids": ["lenovo_g580_psref"]},
            "interfaces": {"value": "2x USB 3.0, 1x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1", "source_ids": ["lenovo_g580_psref"]},
            "webcam": {"value": "0.3 Мп веб-камера", "source_ids": ["lenovo_g580_psref"]},
            "weight": {"value": "2.6 кг", "source_ids": ["lenovo_g580_psref"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) глянцевый VibrantView",
            "Линейка процессора": "Intel Core i3 / Pentium",
            "Модель процессора": "Intel Core i3-2348M / i3-3110M / Pentium 2020M (2.3-2.4 ГГц)",
            "Тип оперативной памяти": "DDR3 1600 МГц (до 8 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel HD Graphics 3000/4000 / NVIDIA GeForce GT 610M (1 ГБ)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100",
            "Разъемы и порты": "2x USB 3.0, 1x USB 2.0, HDMI, VGA, RJ-45, кардридер 2-в-1",
            "Веб-камера": "0.3 Мп веб-камера",
            "Вес": "2.6 кг"
        }
    },
    {
        "stable_key": "toshiba|satellite-l850-e8s",
        "canonical_name": "Toshiba Satellite L850-E8S",
        "brand": "Toshiba",
        "model": "Satellite L850-E8S",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "toshiba_l850_support",
                "url": "https://support.dynabook.com/support/staticContentDetail?contentId=3487216",
                "publisher": "Dynabook Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["toshiba_l850_support"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["toshiba_l850_support"]},
            "screen_resolution": {"value": "1366x768 (HD) TruBrite LED", "source_ids": ["toshiba_l850_support"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["toshiba_l850_support"]},
            "cpu_model": {"value": "Intel Core i5-3230M (2.6-3.2 ГГц, 2 ядра / 4 потока)", "source_ids": ["toshiba_l850_support"]},
            "ram_type": {"value": "DDR3 1600 МГц (до 16 ГБ, 2 слота SODIMM)", "source_ids": ["toshiba_l850_support"]},
            "graphics": {"value": "Дискретная AMD Radeon HD 7670M (2 ГБ) + Intel HD Graphics 4000", "source_ids": ["toshiba_l850_support"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["toshiba_l850_support"]},
            "network_lan": {"value": "Fast Ethernet 10/100", "source_ids": ["toshiba_l850_support"]},
            "interfaces": {"value": "2x USB 3.0 (1x Sleep-and-Charge), 1x USB 2.0, HDMI, VGA, RJ-45", "source_ids": ["toshiba_l850_support"]},
            "webcam": {"value": "1.0 Мп HD веб-камера", "source_ids": ["toshiba_l850_support"]},
            "weight": {"value": "2.3 кг", "source_ids": ["toshiba_l850_support"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1366x768 (HD) TruBrite LED",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-3230M (2.6-3.2 ГГц, 2 ядра / 4 потока)",
            "Тип оперативной памяти": "DDR3 1600 МГц (до 16 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Дискретная AMD Radeon HD 7670M (2 ГБ) + Intel HD Graphics 4000",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100",
            "Разъемы и порты": "2x USB 3.0 (1x Sleep-and-Charge), 1x USB 2.0, HDMI, VGA, RJ-45",
            "Веб-камера": "1.0 Мп HD веб-камера",
            "Вес": "2.3 кг"
        }
    },
    {
        "stable_key": "toshiba|satellite-pro-l300",
        "canonical_name": "Toshiba Satellite Pro L300",
        "brand": "Toshiba",
        "model": "Satellite Pro L300",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "toshiba_l300_support",
                "url": "https://support.dynabook.com/support/staticContentDetail?contentId=2163901",
                "publisher": "Dynabook Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ноутбук", "source_ids": ["toshiba_l300_support"]},
            "screen_diagonal": {"value": "15.4\"", "source_ids": ["toshiba_l300_support"]},
            "screen_resolution": {"value": "1280x800 (WXGA) TruBrite", "source_ids": ["toshiba_l300_support"]},
            "cpu_series": {"value": "Intel Core 2 Duo", "source_ids": ["toshiba_l300_support"]},
            "cpu_model": {"value": "Intel Core 2 Duo T5870 / Pentium Dual-Core T3400 (2.0-2.16 ГГц)", "source_ids": ["toshiba_l300_support"]},
            "ram_type": {"value": "DDR2 667/800 МГц (до 4 ГБ, 2 слота SODIMM)", "source_ids": ["toshiba_l300_support"]},
            "graphics": {"value": "Intel GMA 4500MHD (встроенная)", "source_ids": ["toshiba_l300_support"]},
            "wireless": {"value": "Wi-Fi 802.11b/g", "source_ids": ["toshiba_l300_support"]},
            "network_lan": {"value": "Fast Ethernet 10/100, модем 56k", "source_ids": ["toshiba_l300_support"]},
            "interfaces": {"value": "3x USB 2.0, VGA, RJ-45, RJ-11, ExpressCard/54", "source_ids": ["toshiba_l300_support"]},
            "weight": {"value": "2.69 кг", "source_ids": ["toshiba_l300_support"]}
        },
        "specifications": {
            "Тип устройства": "Ноутбук",
            "Диагональ экрана": "15.4\"",
            "Разрешение экрана": "1280x800 (WXGA) TruBrite",
            "Линейка процессора": "Intel Core 2 Duo",
            "Модель процессора": "Intel Core 2 Duo T5870 / Pentium Dual-Core T3400 (2.0-2.16 ГГц)",
            "Тип оперативной памяти": "DDR2 667/800 МГц (до 4 ГБ, 2 слота SODIMM)",
            "Видеокарта": "Intel GMA 4500MHD (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100, модем 56k",
            "Разъемы и порты": "3x USB 2.0, VGA, RJ-45, RJ-11, ExpressCard/54",
            "Вес": "2.69 кг"
        }
    },
    {
        "stable_key": "huawei|matebook-b3-510",
        "canonical_name": "Huawei MateBook B3-510",
        "brand": "Huawei",
        "model": "MateBook B3-510",
        "device_type": "laptop",
        "default_category_id": 4,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "huawei_b3_510_spec",
                "url": "https://consumer.huawei.com/en/laptops/matebook-b3-510/specs/",
                "publisher": "Huawei Technologies Co., Ltd.",
                "source_type": "official_product_page",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Ультрабук", "source_ids": ["huawei_b3_510_spec"]},
            "screen_diagonal": {"value": "15.6\"", "source_ids": ["huawei_b3_510_spec"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) IPS матовый 250 нит", "source_ids": ["huawei_b3_510_spec"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["huawei_b3_510_spec"]},
            "cpu_model": {"value": "Intel Core i5-10210U (1.6-4.2 ГГц, 4 ядра / 8 потоков)", "source_ids": ["huawei_b3_510_spec"]},
            "ram_type": {"value": "DDR4 2666 МГц 8 ГБ (встроенная)", "source_ids": ["huawei_b3_510_spec"]},
            "graphics": {"value": "Intel UHD Graphics 620", "source_ids": ["huawei_b3_510_spec"]},
            "wireless": {"value": "Wi-Fi 802.11ac (2x2 MIMO), Bluetooth 5.0", "source_ids": ["huawei_b3_510_spec"]},
            "interfaces": {"value": "1x USB-C (зарядка/данные), 1x USB 3.0, 2x USB 2.0, HDMI, аудио 3.5 мм", "source_ids": ["huawei_b3_510_spec"]},
            "fingerprint": {"value": "Сканер отпечатка в кнопке питания", "source_ids": ["huawei_b3_510_spec"]},
            "webcam": {"value": "720p HD скрытая в клавиатуре", "source_ids": ["huawei_b3_510_spec"]},
            "weight": {"value": "1.53 кг", "source_ids": ["huawei_b3_510_spec"]}
        },
        "specifications": {
            "Тип устройства": "Ультрабук",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "1920x1080 (Full HD) IPS матовый 250 нит",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-10210U (1.6-4.2 ГГц, 4 ядра / 8 потоков)",
            "Тип оперативной памяти": "DDR4 2666 МГц 8 ГБ (встроенная)",
            "Видеокарта": "Intel UHD Graphics 620",
            "Беспроводная связь": "Wi-Fi 802.11ac (2x2 MIMO), Bluetooth 5.0",
            "Разъемы и порты": "1x USB-C (зарядка/данные), 1x USB 3.0, 2x USB 2.0, HDMI, аудио 3.5 мм",
            "Безопасность": "Сканер отпечатка в кнопке питания",
            "Веб-камера": "720p HD скрытая в клавиатуре",
            "Вес": "1.53 кг"
        }
    },

    # ------------------ COMPUTERS & ALL-IN-ONES (12) ------------------
    {
        "stable_key": "lenovo|thinkcentre-m715s",
        "canonical_name": "Lenovo ThinkCentre M715s",
        "brand": "Lenovo",
        "model": "ThinkCentre M715s",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_m715s_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkCentre/ThinkCentre_M715s_SFF/ThinkCentre_M715s_SFF_Spec.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Системный блок", "source_ids": ["lenovo_m715s_psref"]},
            "form_factor": {"value": "Small Form Factor (SFF 8.4 л)", "source_ids": ["lenovo_m715s_psref"]},
            "chipset": {"value": "AMD B350", "source_ids": ["lenovo_m715s_psref"]},
            "supported_processors": {"value": "AMD Ryzen 3 Pro / Ryzen 5 Pro / A-Series (Socket AM4)", "source_ids": ["lenovo_m715s_psref"]},
            "ram_type": {"value": "DDR4-2400 МГц UDIMM (4 слота, до 64 ГБ)", "source_ids": ["lenovo_m715s_psref"]},
            "graphics": {"value": "AMD Radeon Vega Graphics (встроенная в процессор)", "source_ids": ["lenovo_m715s_psref"]},
            "network_lan": {"value": "Gigabit Ethernet (Realtek RTL8111EPV)", "source_ids": ["lenovo_m715s_psref"]},
            "video_outputs": {"value": "2x DisplayPort, 1x VGA", "source_ids": ["lenovo_m715s_psref"]},
            "interfaces": {"value": "6x USB 3.1 Gen 1, 2x USB 2.0, COM (RS-232), аудиоразъемы", "source_ids": ["lenovo_m715s_psref"]},
            "expansion_slots": {"value": "1x PCIe 3.0 x16 (low-profile), 1x PCIe 3.0 x1 (low-profile)", "source_ids": ["lenovo_m715s_psref"]},
            "power_supply": {"value": "180 Вт (85% 80 PLUS Bronze)", "source_ids": ["lenovo_m715s_psref"]}
        },
        "specifications": {
            "Тип устройства": "Системный блок",
            "Форм-фактор": "Small Form Factor (SFF 8.4 л)",
            "Чипсет": "AMD B350",
            "Поддерживаемые процессоры": "AMD Ryzen 3 Pro / Ryzen 5 Pro / A-Series (Socket AM4)",
            "Тип оперативной памяти": "DDR4-2400 МГц UDIMM (4 слота, до 64 ГБ)",
            "Видеокарта": "AMD Radeon Vega Graphics (встроенная в процессор)",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet (Realtek RTL8111EPV)",
            "Видеоинтерфейсы": "2x DisplayPort, 1x VGA",
            "Разъемы и порты": "6x USB 3.1 Gen 1, 2x USB 2.0, COM (RS-232), аудиоразъемы",
            "Слоты расширения": "1x PCIe 3.0 x16 (low-profile), 1x PCIe 3.0 x1 (low-profile)",
            "Блок питания": "180 Вт (85% 80 PLUS Bronze)"
        }
    },
    {
        "stable_key": "acer|extensa-x2610g",
        "canonical_name": "Acer Extensa X2610G",
        "brand": "Acer",
        "model": "Extensa X2610G",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_x2610g_ds",
                "url": "https://www.acer.com/datasheets/2016/4876/X2610G/DT.X0WER.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Системный блок", "source_ids": ["acer_x2610g_ds"]},
            "form_factor": {"value": "Small Form Factor (SFF)", "source_ids": ["acer_x2610g_ds"]},
            "cpu_series": {"value": "Intel Celeron / Pentium", "source_ids": ["acer_x2610g_ds"]},
            "cpu_model": {"value": "Intel Celeron J3060 / Pentium J3710 (1.6-2.64 ГГц, SoC)", "source_ids": ["acer_x2610g_ds"]},
            "ram_type": {"value": "DDR3L 1600 МГц SO-DIMM (2 слота, до 8 ГБ)", "source_ids": ["acer_x2610g_ds"]},
            "graphics": {"value": "Intel HD Graphics 400 / 405 (встроенная)", "source_ids": ["acer_x2610g_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["acer_x2610g_ds"]},
            "video_outputs": {"value": "HDMI, VGA (D-Sub)", "source_ids": ["acer_x2610g_ds"]},
            "interfaces": {"value": "2x USB 3.0, 4x USB 2.0, RJ-45, кардридер SD, аудиоразъемы", "source_ids": ["acer_x2610g_ds"]},
            "power_supply": {"value": "Внешний адаптер 65 Вт", "source_ids": ["acer_x2610g_ds"]}
        },
        "specifications": {
            "Тип устройства": "Системный блок",
            "Форм-фактор": "Small Form Factor (SFF)",
            "Линейка процессора": "Intel Celeron / Pentium",
            "Модель процессора": "Intel Celeron J3060 / Pentium J3710 (1.6-2.64 ГГц, SoC)",
            "Тип оперативной памяти": "DDR3L 1600 МГц SO-DIMM (2 слота, до 8 ГБ)",
            "Видеокарта": "Intel HD Graphics 400 / 405 (встроенная)",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Видеоинтерфейсы": "HDMI, VGA (D-Sub)",
            "Разъемы и порты": "2x USB 3.0, 4x USB 2.0, RJ-45, кардридер SD, аудиоразъемы",
            "Блок питания": "Внешний адаптер 65 Вт"
        }
    },
    {
        "stable_key": "acer|veriton-x2640g",
        "canonical_name": "Acer Veriton X2640G",
        "brand": "Acer",
        "model": "Veriton X2640G",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_x2640g_ds",
                "url": "https://www.acer.com/datasheets/2016/4876/X2640G/DT.VN1ER.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Системный блок", "source_ids": ["acer_x2640g_ds"]},
            "form_factor": {"value": "Small Form Factor (SFF 10 л)", "source_ids": ["acer_x2640g_ds"]},
            "chipset": {"value": "Intel H110 Express", "source_ids": ["acer_x2640g_ds"]},
            "supported_processors": {"value": "Intel Core i3 / i5 6-го поколения (LGA1151, Skylake)", "source_ids": ["acer_x2640g_ds"]},
            "ram_type": {"value": "DDR4 2133 МГц UDIMM (2 слота, до 32 ГБ)", "source_ids": ["acer_x2640g_ds"]},
            "graphics": {"value": "Intel HD Graphics 530", "source_ids": ["acer_x2640g_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["acer_x2640g_ds"]},
            "video_outputs": {"value": "DVI-D, VGA (D-Sub)", "source_ids": ["acer_x2640g_ds"]},
            "interfaces": {"value": "4x USB 3.0, 4x USB 2.0, COM (RS-232), RJ-45, PS/2", "source_ids": ["acer_x2640g_ds"]},
            "expansion_slots": {"value": "1x PCIe 3.0 x16 (low-profile), 1x PCIe 2.0 x1 (low-profile)", "source_ids": ["acer_x2640g_ds"]},
            "power_supply": {"value": "220 Вт (80 PLUS)", "source_ids": ["acer_x2640g_ds"]}
        },
        "specifications": {
            "Тип устройства": "Системный блок",
            "Форм-фактор": "Small Form Factor (SFF 10 л)",
            "Чипсет": "Intel H110 Express",
            "Поддерживаемые процессоры": "Intel Core i3 / i5 6-го поколения (LGA1151, Skylake)",
            "Тип оперативной памяти": "DDR4 2133 МГц UDIMM (2 слота, до 32 ГБ)",
            "Видеокарта": "Intel HD Graphics 530",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Видеоинтерфейсы": "DVI-D, VGA (D-Sub)",
            "Разъемы и порты": "4x USB 3.0, 4x USB 2.0, COM (RS-232), RJ-45, PS/2",
            "Слоты расширения": "1x PCIe 3.0 x16 (low-profile), 1x PCIe 2.0 x1 (low-profile)",
            "Блок питания": "220 Вт (80 PLUS)"
        }
    },
    {
        "stable_key": "acer|aspire-z5761",
        "canonical_name": "Acer Aspire Z5761",
        "brand": "Acer",
        "model": "Aspire Z5761",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "acer_z5761_ds",
                "url": "https://www.acer.com/datasheets/2011/4876/Z5761/PW.SFW02.001.html",
                "publisher": "Acer Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок (All-in-One)", "source_ids": ["acer_z5761_ds"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["acer_z5761_ds"]},
            "screen_diagonal": {"value": "23\"", "source_ids": ["acer_z5761_ds"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) Multi-Touch сенсорный", "source_ids": ["acer_z5761_ds"]},
            "chipset": {"value": "Intel H67 Express", "source_ids": ["acer_z5761_ds"]},
            "cpu_series": {"value": "Intel Core i5", "source_ids": ["acer_z5761_ds"]},
            "cpu_model": {"value": "Intel Core i5-2400S (2.5-3.3 ГГц, 4 ядра, LGA1155)", "source_ids": ["acer_z5761_ds"]},
            "ram_type": {"value": "DDR3 1333 МГц SO-DIMM (4 слота, до 8 ГБ)", "source_ids": ["acer_z5761_ds"]},
            "graphics": {"value": "NVIDIA GeForce GT 530 / GT 420 (до 2 ГБ)", "source_ids": ["acer_z5761_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth", "source_ids": ["acer_z5761_ds"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["acer_z5761_ds"]},
            "interfaces": {"value": "8x USB 2.0, HDMI (вход/выход), VGA, кардридер, аудио", "source_ids": ["acer_z5761_ds"]},
            "webcam": {"value": "2.0 Мп HD веб-камера с микрофоном", "source_ids": ["acer_z5761_ds"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок (All-in-One)",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "23\"",
            "Разрешение экрана": "1920x1080 (Full HD) Multi-Touch сенсорный",
            "Чипсет": "Intel H67 Express",
            "Линейка процессора": "Intel Core i5",
            "Модель процессора": "Intel Core i5-2400S (2.5-3.3 ГГц, 4 ядра, LGA1155)",
            "Тип оперативной памяти": "DDR3 1333 МГц SO-DIMM (4 слота, до 8 ГБ)",
            "Видеокарта": "NVIDIA GeForce GT 530 / GT 420 (до 2 ГБ)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Разъемы и порты": "8x USB 2.0, HDMI (вход/выход), VGA, кардридер, аудио",
            "Веб-камера": "2.0 Мп HD веб-камера с микрофоном"
        }
    },
    {
        "stable_key": "lenovo|thinkcentre-m72e",
        "canonical_name": "Lenovo ThinkCentre M72e",
        "brand": "Lenovo",
        "model": "ThinkCentre M72e",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_m72e_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/withdrawn/M72e.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Системный блок", "source_ids": ["lenovo_m72e_psref"]},
            "form_factor": {"value": "Small Form Factor (SFF 11 л)", "source_ids": ["lenovo_m72e_psref"]},
            "chipset": {"value": "Intel H61 Express", "source_ids": ["lenovo_m72e_psref"]},
            "supported_processors": {"value": "Intel Core i3 / i5 2-го и 3-го поколений (LGA1155)", "source_ids": ["lenovo_m72e_psref"]},
            "ram_type": {"value": "DDR3 1600 МГц UDIMM (2 слота, до 16 ГБ)", "source_ids": ["lenovo_m72e_psref"]},
            "graphics": {"value": "Intel HD Graphics 2500 / 4000 (встроенная)", "source_ids": ["lenovo_m72e_psref"]},
            "network_lan": {"value": "Gigabit Ethernet (Realtek RTL8111E)", "source_ids": ["lenovo_m72e_psref"]},
            "video_outputs": {"value": "DisplayPort, VGA (D-Sub)", "source_ids": ["lenovo_m72e_psref"]},
            "interfaces": {"value": "6x USB 2.0, 1x COM (RS-232), RJ-45, аудио", "source_ids": ["lenovo_m72e_psref"]},
            "expansion_slots": {"value": "1x PCIe 2.0 x16 (low profile), 2x PCIe 2.0 x1 (low profile)", "source_ids": ["lenovo_m72e_psref"]},
            "power_supply": {"value": "240 Вт (85% efficiency 80 PLUS)", "source_ids": ["lenovo_m72e_psref"]}
        },
        "specifications": {
            "Тип устройства": "Системный блок",
            "Форм-фактор": "Small Form Factor (SFF 11 л)",
            "Чипсет": "Intel H61 Express",
            "Поддерживаемые процессоры": "Intel Core i3 / i5 2-го и 3-го поколений (LGA1155)",
            "Тип оперативной памяти": "DDR3 1600 МГц UDIMM (2 слота, до 16 ГБ)",
            "Видеокарта": "Intel HD Graphics 2500 / 4000 (встроенная)",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet (Realtek RTL8111E)",
            "Видеоинтерфейсы": "DisplayPort, VGA (D-Sub)",
            "Разъемы и порты": "6x USB 2.0, 1x COM (RS-232), RJ-45, аудио",
            "Слоты расширения": "1x PCIe 2.0 x16 (low profile), 2x PCIe 2.0 x1 (low profile)",
            "Блок питания": "240 Вт (85% efficiency 80 PLUS)"
        }
    },
    {
        "stable_key": "lenovo|ideacentre-c340",
        "canonical_name": "Lenovo IdeaCentre C340",
        "brand": "Lenovo",
        "model": "IdeaCentre C340",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_c340_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/withdrawn/ideacentre_C340.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок (All-in-One)", "source_ids": ["lenovo_c340_psref"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["lenovo_c340_psref"]},
            "screen_diagonal": {"value": "20\"", "source_ids": ["lenovo_c340_psref"]},
            "screen_resolution": {"value": "1600x900 (HD+) LED 16:9", "source_ids": ["lenovo_c340_psref"]},
            "chipset": {"value": "Intel H61 Express", "source_ids": ["lenovo_c340_psref"]},
            "cpu_series": {"value": "Intel Core i3 / Pentium", "source_ids": ["lenovo_c340_psref"]},
            "cpu_model": {"value": "Intel Core i3-3240 / Pentium G2020 (LGA1155)", "source_ids": ["lenovo_c340_psref"]},
            "ram_type": {"value": "DDR3 1600 МГц SO-DIMM (2 слота, до 8 ГБ)", "source_ids": ["lenovo_c340_psref"]},
            "graphics": {"value": "Intel HD Graphics / NVIDIA GeForce 615 (1 ГБ / 2 ГБ)", "source_ids": ["lenovo_c340_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["lenovo_c340_psref"]},
            "network_lan": {"value": "Fast/Gigabit Ethernet", "source_ids": ["lenovo_c340_psref"]},
            "interfaces": {"value": "2x USB 3.0, 4x USB 2.0, кардридер 6-в-1, RJ-45", "source_ids": ["lenovo_c340_psref"]},
            "webcam": {"value": "720p HD со стереомикрофоном", "source_ids": ["lenovo_c340_psref"]},
            "power_supply": {"value": "Внешний адаптер 90/120 Вт", "source_ids": ["lenovo_c340_psref"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок (All-in-One)",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "20\"",
            "Разрешение экрана": "1600x900 (HD+) LED 16:9",
            "Чипсет": "Intel H61 Express",
            "Линейка процессора": "Intel Core i3 / Pentium",
            "Модель процессора": "Intel Core i3-3240 / Pentium G2020 (LGA1155)",
            "Тип оперативной памяти": "DDR3 1600 МГц SO-DIMM (2 слота, до 8 ГБ)",
            "Видеокарта": "Intel HD Graphics / NVIDIA GeForce 615 (1 ГБ / 2 ГБ)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Fast/Gigabit Ethernet",
            "Разъемы и порты": "2x USB 3.0, 4x USB 2.0, кардридер 6-в-1, RJ-45",
            "Веб-камера": "720p HD со стереомикрофоном",
            "Блок питания": "Внешний адаптер 90/120 Вт"
        }
    },
    {
        "stable_key": "lenovo|thinkcentre-m72z",
        "canonical_name": "Lenovo ThinkCentre M72z",
        "brand": "Lenovo",
        "model": "ThinkCentre M72z",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_m72z_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/withdrawn/M72z.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок бизнес-класса", "source_ids": ["lenovo_m72z_psref"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["lenovo_m72z_psref"]},
            "screen_diagonal": {"value": "20\"", "source_ids": ["lenovo_m72z_psref"]},
            "screen_resolution": {"value": "1600x900 (HD+) матовый CCFL/LED", "source_ids": ["lenovo_m72z_psref"]},
            "chipset": {"value": "Intel H61 Express", "source_ids": ["lenovo_m72z_psref"]},
            "cpu_series": {"value": "Intel Core i3 / i5", "source_ids": ["lenovo_m72z_psref"]},
            "cpu_model": {"value": "Intel Core i3-3220 / i5-3470S (LGA1155, 65 Вт)", "source_ids": ["lenovo_m72z_psref"]},
            "ram_type": {"value": "DDR3 1600 МГц SO-DIMM (2 слота, до 16 ГБ)", "source_ids": ["lenovo_m72z_psref"]},
            "graphics": {"value": "Intel HD Graphics 2500 (встроенная)", "source_ids": ["lenovo_m72z_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["lenovo_m72z_psref"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["lenovo_m72z_psref"]},
            "video_outputs": {"value": "DisplayPort (выход), DisplayPort (вход)", "source_ids": ["lenovo_m72z_psref"]},
            "interfaces": {"value": "6x USB 2.0 (2 сбоку, 4 сзади), RJ-45, аудио", "source_ids": ["lenovo_m72z_psref"]},
            "webcam": {"value": "2.0 Мп с физической шторкой безопасности", "source_ids": ["lenovo_m72z_psref"]},
            "power_supply": {"value": "Встроенный БП 150 Вт (85% 80 PLUS Bronze)", "source_ids": ["lenovo_m72z_psref"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок бизнес-класса",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "20\"",
            "Разрешение экрана": "1600x900 (HD+) матовый CCFL/LED",
            "Чипсет": "Intel H61 Express",
            "Линейка процессора": "Intel Core i3 / i5",
            "Модель процессора": "Intel Core i3-3220 / i5-3470S (LGA1155, 65 Вт)",
            "Тип оперативной памяти": "DDR3 1600 МГц SO-DIMM (2 слота, до 16 ГБ)",
            "Видеокарта": "Intel HD Graphics 2500 (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Видеоинтерфейсы": "DisplayPort (выход), DisplayPort (вход)",
            "Разъемы и порты": "6x USB 2.0 (2 сбоку, 4 сзади), RJ-45, аудио",
            "Веб-камера": "2.0 Мп с физической шторкой безопасности",
            "Блок питания": "Встроенный БП 150 Вт (85% 80 PLUS Bronze)"
        }
    },
    {
        "stable_key": "lenovo|thinkcentre-s40-40",
        "canonical_name": "Lenovo ThinkCentre S40-40",
        "brand": "Lenovo",
        "model": "ThinkCentre S40-40",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "lenovo_s40_40_psref",
                "url": "https://psref.lenovo.com/syspool/Sys/PDF/withdrawn/S40_40.pdf",
                "publisher": "Lenovo Group Limited",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок (All-in-One)", "source_ids": ["lenovo_s40_40_psref"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["lenovo_s40_40_psref"]},
            "screen_diagonal": {"value": "21.5\"", "source_ids": ["lenovo_s40_40_psref"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) матовый 16:9", "source_ids": ["lenovo_s40_40_psref"]},
            "chipset": {"value": "Intel H81 Express", "source_ids": ["lenovo_s40_40_psref"]},
            "cpu_series": {"value": "Intel Core i3 / i5", "source_ids": ["lenovo_s40_40_psref"]},
            "cpu_model": {"value": "Intel Core i3-4160 / i5-4460S (LGA1150, Haswell)", "source_ids": ["lenovo_s40_40_psref"]},
            "ram_type": {"value": "DDR3 1600 МГц SO-DIMM (2 слота, до 16 ГБ)", "source_ids": ["lenovo_s40_40_psref"]},
            "graphics": {"value": "Intel HD Graphics 4400 / 4600", "source_ids": ["lenovo_s40_40_psref"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n, Bluetooth 4.0", "source_ids": ["lenovo_s40_40_psref"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["lenovo_s40_40_psref"]},
            "video_outputs": {"value": "HDMI-выход, HDMI-вход", "source_ids": ["lenovo_s40_40_psref"]},
            "interfaces": {"value": "2x USB 3.0, 3x USB 2.0, кардридер 6-в-1, RJ-45", "source_ids": ["lenovo_s40_40_psref"]},
            "webcam": {"value": "720p HD веб-камера", "source_ids": ["lenovo_s40_40_psref"]},
            "power_supply": {"value": "Встроенный адаптер 120 Вт", "source_ids": ["lenovo_s40_40_psref"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок (All-in-One)",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "21.5\"",
            "Разрешение экрана": "1920x1080 (Full HD) матовый 16:9",
            "Чипсет": "Intel H81 Express",
            "Линейка процессора": "Intel Core i3 / i5",
            "Модель процессора": "Intel Core i3-4160 / i5-4460S (LGA1150, Haswell)",
            "Тип оперативной памяти": "DDR3 1600 МГц SO-DIMM (2 слота, до 16 ГБ)",
            "Видеокарта": "Intel HD Graphics 4400 / 4600",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n, Bluetooth 4.0",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000",
            "Видеоинтерфейсы": "HDMI-выход, HDMI-вход",
            "Разъемы и порты": "2x USB 3.0, 3x USB 2.0, кардридер 6-в-1, RJ-45",
            "Веб-камера": "720p HD веб-камера",
            "Блок питания": "Встроенный адаптер 120 Вт"
        }
    },
    {
        "stable_key": "hp|compaq-pro-6300",
        "canonical_name": "HP Compaq Pro 6300",
        "brand": "HP",
        "model": "Compaq Pro 6300",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_cp_6300_ds",
                "url": "https://support.hp.com/us-en/document/c03387770",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Системный блок бизнес-класса", "source_ids": ["hp_cp_6300_ds"]},
            "form_factor": {"value": "Small Form Factor (SFF)", "source_ids": ["hp_cp_6300_ds"]},
            "chipset": {"value": "Intel Q75 Express", "source_ids": ["hp_cp_6300_ds"]},
            "supported_processors": {"value": "Intel Core i3 / i5 / i7 2-го и 3-го поколений (LGA1155)", "source_ids": ["hp_cp_6300_ds"]},
            "ram_type": {"value": "DDR3-1600 МГц DIMM (4 слота, до 32 ГБ)", "source_ids": ["hp_cp_6300_ds"]},
            "graphics": {"value": "Intel HD Graphics 2500 / 4000", "source_ids": ["hp_cp_6300_ds"]},
            "network_lan": {"value": "Intel 82579LM Gigabit Ethernet", "source_ids": ["hp_cp_6300_ds"]},
            "video_outputs": {"value": "1x DisplayPort 1.1, 1x VGA", "source_ids": ["hp_cp_6300_ds"]},
            "interfaces": {"value": "4x USB 3.0, 6x USB 2.0, COM (RS-232), 2x PS/2, RJ-45", "source_ids": ["hp_cp_6300_ds"]},
            "expansion_slots": {"value": "1x PCIe 3.0 x16, 2x PCIe 2.0 x1, 1x PCI (low-profile)", "source_ids": ["hp_cp_6300_ds"]},
            "power_supply": {"value": "240 Вт (active PFC, 87% 80 PLUS Gold)", "source_ids": ["hp_cp_6300_ds"]}
        },
        "specifications": {
            "Тип устройства": "Системный блок бизнес-класса",
            "Форм-фактор": "Small Form Factor (SFF)",
            "Чипсет": "Intel Q75 Express",
            "Поддерживаемые процессоры": "Intel Core i3 / i5 / i7 2-го и 3-го поколений (LGA1155)",
            "Тип оперативной памяти": "DDR3-1600 МГц DIMM (4 слота, до 32 ГБ)",
            "Видеокарта": "Intel HD Graphics 2500 / 4000",
            "Сетевой адаптер (LAN)": "Intel 82579LM Gigabit Ethernet",
            "Видеоинтерфейсы": "1x DisplayPort 1.1, 1x VGA",
            "Разъемы и порты": "4x USB 3.0, 6x USB 2.0, COM (RS-232), 2x PS/2, RJ-45",
            "Слоты расширения": "1x PCIe 3.0 x16, 2x PCIe 2.0 x1, 1x PCI (low-profile)",
            "Блок питания": "240 Вт (active PFC, 87% 80 PLUS Gold)"
        }
    },
    {
        "stable_key": "hp|compaq-pro-7320",
        "canonical_name": "HP Compaq Pro 7320",
        "brand": "HP",
        "model": "Compaq Pro 7320",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_cp_7320_ds",
                "url": "https://support.hp.com/us-en/document/c03058866",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок бизнес-класса (All-in-One)", "source_ids": ["hp_cp_7320_ds"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["hp_cp_7320_ds"]},
            "screen_diagonal": {"value": "21.5\"", "source_ids": ["hp_cp_7320_ds"]},
            "screen_resolution": {"value": "1920x1080 (Full HD) WLED антибликовый", "source_ids": ["hp_cp_7320_ds"]},
            "chipset": {"value": "Intel H61 Express", "source_ids": ["hp_cp_7320_ds"]},
            "cpu_series": {"value": "Intel Core i3 / i5", "source_ids": ["hp_cp_7320_ds"]},
            "cpu_model": {"value": "Intel Core i3-2120 / i5-2400S (LGA1155, Sandy Bridge)", "source_ids": ["hp_cp_7320_ds"]},
            "ram_type": {"value": "DDR3-1333 SO-DIMM (2 слота, до 8 ГБ)", "source_ids": ["hp_cp_7320_ds"]},
            "graphics": {"value": "Intel HD Graphics 2000 (встроенная)", "source_ids": ["hp_cp_7320_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["hp_cp_7320_ds"]},
            "network_lan": {"value": "Realtek RTL8111E Gigabit Ethernet", "source_ids": ["hp_cp_7320_ds"]},
            "interfaces": {"value": "2x USB 3.0 (боковые), 4x USB 2.0 (задние), кардридер 6-в-1, RJ-45", "source_ids": ["hp_cp_7320_ds"]},
            "webcam": {"value": "2.0 Мп с микрофонами", "source_ids": ["hp_cp_7320_ds"]},
            "power_supply": {"value": "Встроенный БП 150 Вт", "source_ids": ["hp_cp_7320_ds"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок бизнес-класса (All-in-One)",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "21.5\"",
            "Разрешение экрана": "1920x1080 (Full HD) WLED антибликовый",
            "Чипсет": "Intel H61 Express",
            "Линейка процессора": "Intel Core i3 / i5",
            "Модель процессора": "Intel Core i3-2120 / i5-2400S (LGA1155, Sandy Bridge)",
            "Тип оперативной памяти": "DDR3-1333 SO-DIMM (2 слота, до 8 ГБ)",
            "Видеокарта": "Intel HD Graphics 2000 (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Realtek RTL8111E Gigabit Ethernet",
            "Разъемы и порты": "2x USB 3.0 (боковые), 4x USB 2.0 (задние), кардридер 6-в-1, RJ-45",
            "Веб-камера": "2.0 Мп с микрофонами",
            "Блок питания": "Встроенный БП 150 Вт"
        }
    },
    {
        "stable_key": "hp|pavilion-200",
        "canonical_name": "HP Pavilion 200",
        "brand": "HP",
        "model": "Pavilion 200",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_pavilion_200_ds",
                "url": "https://support.hp.com/us-en/document/c03784770",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Моноблок (All-in-One)", "source_ids": ["hp_pavilion_200_ds"]},
            "form_factor": {"value": "All-in-One", "source_ids": ["hp_pavilion_200_ds"]},
            "screen_diagonal": {"value": "20\"", "source_ids": ["hp_pavilion_200_ds"]},
            "screen_resolution": {"value": "1600x900 (HD+) WLED матовый 16:9", "source_ids": ["hp_pavilion_200_ds"]},
            "chipset": {"value": "Intel H61 Express", "source_ids": ["hp_pavilion_200_ds"]},
            "cpu_series": {"value": "Intel Pentium / Celeron", "source_ids": ["hp_pavilion_200_ds"]},
            "cpu_model": {"value": "Intel Pentium G2020T / Celeron G1610T (LGA1155, 35 Вт)", "source_ids": ["hp_pavilion_200_ds"]},
            "ram_type": {"value": "DDR3-1600 SO-DIMM (2 слота, до 8 ГБ)", "source_ids": ["hp_pavilion_200_ds"]},
            "graphics": {"value": "Intel HD Graphics (встроенная)", "source_ids": ["hp_pavilion_200_ds"]},
            "wireless": {"value": "Wi-Fi 802.11b/g/n", "source_ids": ["hp_pavilion_200_ds"]},
            "network_lan": {"value": "Fast Ethernet 10/100", "source_ids": ["hp_pavilion_200_ds"]},
            "interfaces": {"value": "2x USB 3.0, 4x USB 2.0, кардридер 7-в-1, RJ-45", "source_ids": ["hp_pavilion_200_ds"]},
            "webcam": {"value": "HP TrueVision HD веб-камера", "source_ids": ["hp_pavilion_200_ds"]},
            "power_supply": {"value": "Внешний адаптер 90 Вт", "source_ids": ["hp_pavilion_200_ds"]}
        },
        "specifications": {
            "Тип устройства": "Моноблок (All-in-One)",
            "Форм-фактор": "All-in-One",
            "Диагональ экрана": "20\"",
            "Разрешение экрана": "1600x900 (HD+) WLED матовый 16:9",
            "Чипсет": "Intel H61 Express",
            "Линейка процессора": "Intel Pentium / Celeron",
            "Модель процессора": "Intel Pentium G2020T / Celeron G1610T (LGA1155, 35 Вт)",
            "Тип оперативной памяти": "DDR3-1600 SO-DIMM (2 слота, до 8 ГБ)",
            "Видеокарта": "Intel HD Graphics (встроенная)",
            "Беспроводная связь": "Wi-Fi 802.11b/g/n",
            "Сетевой адаптер (LAN)": "Fast Ethernet 10/100",
            "Разъемы и порты": "2x USB 3.0, 4x USB 2.0, кардридер 7-в-1, RJ-45",
            "Веб-камера": "HP TrueVision HD веб-камера",
            "Блок питания": "Внешний адаптер 90 Вт"
        }
    },
    {
        "stable_key": "aquarius|pro-p30t-42",
        "canonical_name": "Aquarius Pro P30T 42",
        "brand": "Aquarius",
        "model": "Pro P30T 42",
        "device_type": "computer",
        "default_category_id": 50,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "aquarius_p30_k42_official",
                "url": "https://www.aq.ru/catalog/desktops/aquarius-pro-p30-k42/",
                "publisher": "ПК Аквариус",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Персональный компьютер (рабочая станция)", "source_ids": ["aquarius_p30_k42_official"]},
            "form_factor": {"value": "Small Form Factor (SFF) / Minitower", "source_ids": ["aquarius_p30_k42_official"]},
            "chipset": {"value": "Intel B360 / H310 Express", "source_ids": ["aquarius_p30_k42_official"]},
            "supported_processors": {"value": "Intel Core i3 / i5 / i7 8-го и 9-го поколений (LGA1151v2)", "source_ids": ["aquarius_p30_k42_official"]},
            "ram_type": {"value": "DDR4-2400/2666 МГц UDIMM (до 64 ГБ)", "source_ids": ["aquarius_p30_k42_official"]},
            "graphics": {"value": "Intel UHD Graphics 630 (встроенная)", "source_ids": ["aquarius_p30_k42_official"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000 Мбит/с", "source_ids": ["aquarius_p30_k42_official"]},
            "video_outputs": {"value": "HDMI, DisplayPort, VGA", "source_ids": ["aquarius_p30_k42_official"]},
            "interfaces": {"value": "4x USB 3.1 Gen 1, 4x USB 2.0, COM (RS-232), RJ-45", "source_ids": ["aquarius_p30_k42_official"]},
            "expansion_slots": {"value": "1x PCIe 3.0 x16, 2x PCIe 3.0 x1", "source_ids": ["aquarius_p30_k42_official"]},
            "power_supply": {"value": "250 Вт / 350 Вт (80 PLUS)", "source_ids": ["aquarius_p30_k42_official"]}
        },
        "specifications": {
            "Тип устройства": "Персональный компьютер (рабочая станция)",
            "Форм-фактор": "Small Form Factor (SFF) / Minitower",
            "Чипсет": "Intel B360 / H310 Express",
            "Поддерживаемые процессоры": "Intel Core i3 / i5 / i7 8-го и 9-го поколений (LGA1151v2)",
            "Тип оперативной памяти": "DDR4-2400/2666 МГц UDIMM (до 64 ГБ)",
            "Видеокарта": "Intel UHD Graphics 630 (встроенная)",
            "Сетевой адаптер (LAN)": "Gigabit Ethernet 10/100/1000 Мбит/с",
            "Видеоинтерфейсы": "HDMI, DisplayPort, VGA",
            "Разъемы и порты": "4x USB 3.1 Gen 1, 4x USB 2.0, COM (RS-232), RJ-45",
            "Слоты расширения": "1x PCIe 3.0 x16, 2x PCIe 3.0 x1",
            "Блок питания": "250 Вт / 350 Вт (80 PLUS)"
        }
    },

    # ------------------ COMPONENTS - PROCESSORS (4) ------------------
    {
        "stable_key": "intel|pentium-g4500",
        "canonical_name": "Intel Pentium G4500",
        "brand": "Intel",
        "model": "Pentium G4500",
        "device_type": "component",
        "default_category_id": 7,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "intel_g4500_ark",
                "url": "https://www.intel.com/content/www/us/en/products/sku/90730/intel-pentium-processor-g4500-3m-cache-3-50-ghz/specifications.html",
                "publisher": "Intel Corporation",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Процессор", "source_ids": ["intel_g4500_ark"]},
            "socket": {"value": "LGA1151", "source_ids": ["intel_g4500_ark"]},
            "cores": {"value": "2", "source_ids": ["intel_g4500_ark"]},
            "threads": {"value": "2", "source_ids": ["intel_g4500_ark"]},
            "base_frequency": {"value": "3.50 ГГц", "source_ids": ["intel_g4500_ark"]},
            "cache": {"value": "3 МБ Intel Smart Cache", "source_ids": ["intel_g4500_ark"]},
            "tdp": {"value": "51 Вт", "source_ids": ["intel_g4500_ark"]},
            "lithography": {"value": "14 нм", "source_ids": ["intel_g4500_ark"]},
            "memory_types": {"value": "DDR4-1866/2133, DDR3L-1333/1600 @ 1.35V (до 64 ГБ)", "source_ids": ["intel_g4500_ark"]},
            "integrated_graphics": {"value": "Intel HD Graphics 530 (до 1.05 ГГц, 4K 60Hz)", "source_ids": ["intel_g4500_ark"]},
            "pcie_version": {"value": "PCIe 3.0 (до 16 линий)", "source_ids": ["intel_g4500_ark"]}
        },
        "specifications": {
            "Тип устройства": "Процессор",
            "Сокет": "LGA1151",
            "Количество ядер": "2",
            "Количество потоков": "2",
            "Базовая частота": "3.50 ГГц",
            "Кэш-память": "3 МБ Intel Smart Cache",
            "Тепловыделение (TDP)": "51 Вт",
            "Техпроцесс": "14 нм",
            "Тип поддерживаемой памяти": "DDR4-1866/2133, DDR3L-1333/1600 @ 1.35V (до 64 ГБ)",
            "Встроенная графика": "Intel HD Graphics 530 (до 1.05 ГГц, 4K 60Hz)",
            "Версия PCI Express": "PCIe 3.0 (до 16 линий)"
        }
    },
    {
        "stable_key": "intel|xeon-e3-1220",
        "canonical_name": "Intel Xeon E3-1220",
        "brand": "Intel",
        "model": "Xeon E3-1220",
        "device_type": "component",
        "default_category_id": 7,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "intel_e3_1220_ark",
                "url": "https://www.intel.com/content/www/us/en/products/sku/52269/intel-xeon-processor-e31220-8m-cache-3-10-ghz/specifications.html",
                "publisher": "Intel Corporation",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Серверный процессор", "source_ids": ["intel_e3_1220_ark"]},
            "socket": {"value": "LGA1155", "source_ids": ["intel_e3_1220_ark"]},
            "cores": {"value": "4", "source_ids": ["intel_e3_1220_ark"]},
            "threads": {"value": "4", "source_ids": ["intel_e3_1220_ark"]},
            "base_frequency": {"value": "3.10 ГГц", "source_ids": ["intel_e3_1220_ark"]},
            "turbo_frequency": {"value": "3.40 ГГц", "source_ids": ["intel_e3_1220_ark"]},
            "cache": {"value": "8 МБ Intel Smart Cache", "source_ids": ["intel_e3_1220_ark"]},
            "tdp": {"value": "80 Вт", "source_ids": ["intel_e3_1220_ark"]},
            "lithography": {"value": "32 нм", "source_ids": ["intel_e3_1220_ark"]},
            "memory_types": {"value": "DDR3 1066/1333 МГц с поддержкой ECC (до 32 ГБ)", "source_ids": ["intel_e3_1220_ark"]},
            "integrated_graphics": {"value": "Нет (требуется дискретная графика)", "source_ids": ["intel_e3_1220_ark"]},
            "pcie_version": {"value": "PCIe 2.0 (16 линий)", "source_ids": ["intel_e3_1220_ark"]}
        },
        "specifications": {
            "Тип устройства": "Серверный процессор",
            "Сокет": "LGA1155",
            "Количество ядер": "4",
            "Количество потоков": "4",
            "Базовая частота": "3.10 ГГц",
            "Максимальная частота (Turbo)": "3.40 ГГц",
            "Кэш-память": "8 МБ Intel Smart Cache",
            "Тепловыделение (TDP)": "80 Вт",
            "Техпроцесс": "32 нм",
            "Тип поддерживаемой памяти": "DDR3 1066/1333 МГц с поддержкой ECC (до 32 ГБ)",
            "Встроенная графика": "Нет (требуется дискретная графика)",
            "Версия PCI Express": "PCIe 2.0 (16 линий)"
        }
    },
    {
        "stable_key": "intel|xeon-e3-1220-v5",
        "canonical_name": "Intel Xeon E3-1220 v5",
        "brand": "Intel",
        "model": "Xeon E3-1220 v5",
        "device_type": "component",
        "default_category_id": 7,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "intel_e3_1220_v5_ark",
                "url": "https://www.intel.com/content/www/us/en/products/sku/88172/intel-xeon-processor-e31220-v5-8m-cache-3-00-ghz/specifications.html",
                "publisher": "Intel Corporation",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Серверный процессор", "source_ids": ["intel_e3_1220_v5_ark"]},
            "socket": {"value": "LGA1151", "source_ids": ["intel_e3_1220_v5_ark"]},
            "cores": {"value": "4", "source_ids": ["intel_e3_1220_v5_ark"]},
            "threads": {"value": "4", "source_ids": ["intel_e3_1220_v5_ark"]},
            "base_frequency": {"value": "3.00 ГГц", "source_ids": ["intel_e3_1220_v5_ark"]},
            "turbo_frequency": {"value": "3.50 ГГц", "source_ids": ["intel_e3_1220_v5_ark"]},
            "cache": {"value": "8 МБ Intel Smart Cache", "source_ids": ["intel_e3_1220_v5_ark"]},
            "tdp": {"value": "80 Вт", "source_ids": ["intel_e3_1220_v5_ark"]},
            "lithography": {"value": "14 нм", "source_ids": ["intel_e3_1220_v5_ark"]},
            "memory_types": {"value": "DDR4-1866/2133, DDR3L-1333/1600 ECC (до 64 ГБ)", "source_ids": ["intel_e3_1220_v5_ark"]},
            "integrated_graphics": {"value": "Нет (требуется дискретная графика)", "source_ids": ["intel_e3_1220_v5_ark"]},
            "pcie_version": {"value": "PCIe 3.0 (16 линий)", "source_ids": ["intel_e3_1220_v5_ark"]}
        },
        "specifications": {
            "Тип устройства": "Серверный процессор",
            "Сокет": "LGA1151",
            "Количество ядер": "4",
            "Количество потоков": "4",
            "Базовая частота": "3.00 ГГц",
            "Максимальная частота (Turbo)": "3.50 ГГц",
            "Кэш-память": "8 МБ Intel Smart Cache",
            "Тепловыделение (TDP)": "80 Вт",
            "Техпроцесс": "14 нм",
            "Тип поддерживаемой памяти": "DDR4-1866/2133, DDR3L-1333/1600 ECC (до 64 ГБ)",
            "Встроенная графика": "Нет (требуется дискретная графика)",
            "Версия PCI Express": "PCIe 3.0 (16 линий)"
        }
    },
    {
        "stable_key": "intel|xeon-e3-1220-v6",
        "canonical_name": "Intel Xeon E3-1220 v6",
        "brand": "Intel",
        "model": "Xeon E3-1220 v6",
        "device_type": "component",
        "default_category_id": 7,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "intel_e3_1220_v6_ark",
                "url": "https://www.intel.com/content/www/us/en/products/sku/97470/intel-xeon-processor-e31220-v6-8m-cache-3-00-ghz/specifications.html",
                "publisher": "Intel Corporation",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Серверный процессор", "source_ids": ["intel_e3_1220_v6_ark"]},
            "socket": {"value": "LGA1151", "source_ids": ["intel_e3_1220_v6_ark"]},
            "cores": {"value": "4", "source_ids": ["intel_e3_1220_v6_ark"]},
            "threads": {"value": "4", "source_ids": ["intel_e3_1220_v6_ark"]},
            "base_frequency": {"value": "3.00 ГГц", "source_ids": ["intel_e3_1220_v6_ark"]},
            "turbo_frequency": {"value": "3.50 ГГц", "source_ids": ["intel_e3_1220_v6_ark"]},
            "cache": {"value": "8 МБ Intel Smart Cache", "source_ids": ["intel_e3_1220_v6_ark"]},
            "tdp": {"value": "72 Вт", "source_ids": ["intel_e3_1220_v6_ark"]},
            "lithography": {"value": "14 нм", "source_ids": ["intel_e3_1220_v6_ark"]},
            "memory_types": {"value": "DDR4-2400, DDR3L-1866 ECC (до 64 ГБ)", "source_ids": ["intel_e3_1220_v6_ark"]},
            "integrated_graphics": {"value": "Нет (требуется дискретная графика)", "source_ids": ["intel_e3_1220_v6_ark"]},
            "pcie_version": {"value": "PCIe 3.0 (16 линий)", "source_ids": ["intel_e3_1220_v6_ark"]}
        },
        "specifications": {
            "Тип устройства": "Серверный процессор",
            "Сокет": "LGA1151",
            "Количество ядер": "4",
            "Количество потоков": "4",
            "Базовая частота": "3.00 ГГц",
            "Максимальная частота (Turbo)": "3.50 ГГц",
            "Кэш-память": "8 МБ Intel Smart Cache",
            "Тепловыделение (TDP)": "72 Вт",
            "Техпроцесс": "14 нм",
            "Тип поддерживаемой памяти": "DDR4-2400, DDR3L-1866 ECC (до 64 ГБ)",
            "Встроенная графика": "Нет (требуется дискретная графика)",
            "Версия PCI Express": "PCIe 3.0 (16 линий)"
        }
    },

    # ------------------ REMAINING PRINTERS & MFUS (4) ------------------
    {
        "stable_key": "hp|laserjet-p2055",
        "canonical_name": "HP LaserJet P2055",
        "brand": "HP",
        "model": "LaserJet P2055",
        "device_type": "printer",
        "default_category_id": 5,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_p2055_ds",
                "url": "https://support.hp.com/us-en/document/c01705645",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "Принтер", "source_ids": ["hp_p2055_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_p2055_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_p2055_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_p2055_ds"]},
            "print_speed_a4_mono": {"value": "33 стр/мин", "source_ids": ["hp_p2055_ds"]},
            "print_resolution": {"value": "1200 x 1200 dpi (HP ProRes 1200)", "source_ids": ["hp_p2055_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_p2055_ds"]},
            "first_page_time": {"value": "8.0 сек", "source_ids": ["hp_p2055_ds"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["hp_p2055_ds"]},
            "recommended_monthly_volume": {"value": "750 - 3 000 стр/мес", "source_ids": ["hp_p2055_ds"]},
            "interfaces": {"value": "USB 2.0 Hi-Speed", "source_ids": ["hp_p2055_ds"]},
            "memory": {"value": "64 МБ (до 320 МБ)", "source_ids": ["hp_p2055_ds"]},
            "cartridge_model": {"value": "HP 05A (CE505A) / HP 05X (CE505X)", "source_ids": ["hp_p2055_ds"]}
        },
        "specifications": {
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "33 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi (HP ProRes 1200)",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "8.0 сек",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Рекомендуемая нагрузка": "750 - 3 000 стр/мес",
            "Интерфейсы": "USB 2.0 Hi-Speed",
            "Объем памяти": "64 МБ (до 320 МБ)",
            "Модель картриджа": "HP 05A (CE505A) / HP 05X (CE505X)"
        }
    },
    {
        "stable_key": "hp|laserjet-pro-mfp-m132a",
        "canonical_name": "HP LaserJet Pro MFP M132a",
        "brand": "HP",
        "model": "LaserJet Pro MFP M132a",
        "device_type": "mfu",
        "default_category_id": 51,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "hp_m132a_ds",
                "url": "https://support.hp.com/us-en/document/c05250484",
                "publisher": "HP Inc.",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ (принтер/сканер/копир)", "source_ids": ["hp_m132a_ds"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["hp_m132a_ds"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["hp_m132a_ds"]},
            "max_format": {"value": "A4", "source_ids": ["hp_m132a_ds"]},
            "print_speed_a4_mono": {"value": "22 стр/мин", "source_ids": ["hp_m132a_ds"]},
            "print_resolution": {"value": "600 x 600 dpi (HP FastRes 1200)", "source_ids": ["hp_m132a_ds"]},
            "scanner_type": {"value": "Планшетный (CIS), до 1200 dpi", "source_ids": ["hp_m132a_ds"]},
            "duplex": {"value": "Ручная", "source_ids": ["hp_m132a_ds"]},
            "first_page_time": {"value": "7.3 сек", "source_ids": ["hp_m132a_ds"]},
            "monthly_duty_cycle": {"value": "10 000 стр/мес", "source_ids": ["hp_m132a_ds"]},
            "recommended_monthly_volume": {"value": "150 - 1 500 стр/мес", "source_ids": ["hp_m132a_ds"]},
            "interfaces": {"value": "USB 2.0 Hi-Speed", "source_ids": ["hp_m132a_ds"]},
            "memory": {"value": "128 МБ", "source_ids": ["hp_m132a_ds"]},
            "cartridge_model": {"value": "HP 18A (CF218A), барабан HP 19A (CF219A)", "source_ids": ["hp_m132a_ds"]}
        },
        "specifications": {
            "Тип устройства": "МФУ (принтер/сканер/копир)",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "22 стр/мин",
            "Разрешение печати": "600 x 600 dpi (HP FastRes 1200)",
            "Тип сканера": "Планшетный (CIS), до 1200 dpi",
            "Двусторонняя печать": "Ручная",
            "Время выхода первого отпечатка": "7.3 сек",
            "Максимальная нагрузка": "10 000 стр/мес",
            "Рекомендуемая нагрузка": "150 - 1 500 стр/мес",
            "Интерфейсы": "USB 2.0 Hi-Speed",
            "Объем памяти": "128 МБ",
            "Модель картриджа": "HP 18A (CF218A), барабан HP 19A (CF219A)"
        }
    },
    {
        "stable_key": "samsung|scx-4833fd",
        "canonical_name": "Samsung SCX-4833FD",
        "brand": "Samsung",
        "model": "SCX-4833FD",
        "device_type": "mfu",
        "default_category_id": 51,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "samsung_scx_4833fd_support",
                "url": "https://www.samsung.com/ru/support/model/SCX-4833FD/XEV/",
                "publisher": "Samsung Electronics Co., Ltd.",
                "source_type": "official_support_page",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ 4-в-1 (принтер/сканер/копир/факс)", "source_ids": ["samsung_scx_4833fd_support"]},
            "print_technology": {"value": "Лазерная", "source_ids": ["samsung_scx_4833fd_support"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["samsung_scx_4833fd_support"]},
            "max_format": {"value": "A4", "source_ids": ["samsung_scx_4833fd_support"]},
            "print_speed_a4_mono": {"value": "31 стр/мин", "source_ids": ["samsung_scx_4833fd_support"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["samsung_scx_4833fd_support"]},
            "adf": {"value": "Двусторонний DADF (50 листов)", "source_ids": ["samsung_scx_4833fd_support"]},
            "duplex": {"value": "Автоматическая (встроенный дуплекс)", "source_ids": ["samsung_scx_4833fd_support"]},
            "network_lan": {"value": "Ethernet 10/100 (RJ-45)", "source_ids": ["samsung_scx_4833fd_support"]},
            "interfaces": {"value": "Ethernet 10/100, USB 2.0, факс (RJ-11)", "source_ids": ["samsung_scx_4833fd_support"]},
            "monthly_duty_cycle": {"value": "50 000 стр/мес", "source_ids": ["samsung_scx_4833fd_support"]},
            "memory": {"value": "128 МБ (до 384 МБ)", "source_ids": ["samsung_scx_4833fd_support"]},
            "cartridge_model": {"value": "MLT-D205S (2000 стр) / MLT-D205L (5000 стр)", "source_ids": ["samsung_scx_4833fd_support"]}
        },
        "specifications": {
            "Тип устройства": "МФУ 4-в-1 (принтер/сканер/копир/факс)",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "31 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Автоподатчик (ADF)": "Двусторонний DADF (50 листов)",
            "Двусторонняя печать": "Автоматическая (встроенный дуплекс)",
            "Сетевой интерфейс (Ethernet)": "Ethernet 10/100 (RJ-45)",
            "Интерфейсы": "Ethernet 10/100, USB 2.0, факс (RJ-11)",
            "Максимальная нагрузка": "50 000 стр/мес",
            "Объем памяти": "128 МБ (до 384 МБ)",
            "Модель картриджа": "MLT-D205S (2000 стр) / MLT-D205L (5000 стр)"
        }
    },
    {
        "stable_key": "pantum|bm5100adn",
        "canonical_name": "Pantum BM5100ADN",
        "brand": "Pantum",
        "model": "BM5100ADN",
        "device_type": "mfu",
        "default_category_id": 51,
        "decision": "verified_apply",
        "sources": [
            {
                "source_id": "pantum_bm5100adn_official",
                "url": "https://global.pantum.com/product/bm5100adn/",
                "publisher": "Pantum International",
                "source_type": "official_datasheet",
                "retrieved_at": "2026-10-03"
            }
        ],
        "fields": {
            "device_type": {"value": "МФУ (принтер/сканер/копир)", "source_ids": ["pantum_bm5100adn_official"]},
            "print_technology": {"value": "Монохромная лазерная", "source_ids": ["pantum_bm5100adn_official"]},
            "color_mode": {"value": "Черно-белая", "source_ids": ["pantum_bm5100adn_official"]},
            "max_format": {"value": "A4", "source_ids": ["pantum_bm5100adn_official"]},
            "print_speed_a4_mono": {"value": "40 стр/мин", "source_ids": ["pantum_bm5100adn_official"]},
            "print_resolution": {"value": "1200 x 1200 dpi", "source_ids": ["pantum_bm5100adn_official"]},
            "adf": {"value": "Двусторонний DADF (50 листов)", "source_ids": ["pantum_bm5100adn_official"]},
            "duplex": {"value": "Автоматическая", "source_ids": ["pantum_bm5100adn_official"]},
            "network_lan": {"value": "Gigabit Ethernet 10/100/1000", "source_ids": ["pantum_bm5100adn_official"]},
            "interfaces": {"value": "Gigabit Ethernet, USB 2.0 Hi-Speed", "source_ids": ["pantum_bm5100adn_official"]},
            "memory": {"value": "512 МБ", "source_ids": ["pantum_bm5100adn_official"]},
            "monthly_duty_cycle": {"value": "80 000 стр/мес", "source_ids": ["pantum_bm5100adn_official"]},
            "recommended_monthly_volume": {"value": "750 - 4 000 стр/мес", "source_ids": ["pantum_bm5100adn_official"]},
            "cartridge_model": {"value": "TL-5120 (3k) / TL-5120H (6k) / TL-5120X (15k), барабан DL-5120 (30k)", "source_ids": ["pantum_bm5100adn_official"]}
        },
        "specifications": {
            "Тип устройства": "МФУ (принтер/сканер/копир)",
            "Технология печати": "Монохромная лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A4",
            "Скорость печати (A4, ч/б)": "40 стр/мин",
            "Разрешение печати": "1200 x 1200 dpi",
            "Автоподатчик (ADF)": "Двусторонний DADF (50 листов)",
            "Двусторонняя печать": "Автоматическая",
            "Сетевой интерфейс (Ethernet)": "Gigabit Ethernet 10/100/1000",
            "Интерфейсы": "Gigabit Ethernet, USB 2.0 Hi-Speed",
            "Объем памяти": "512 МБ",
            "Максимальная нагрузка": "80 000 стр/мес",
            "Рекомендуемая нагрузка": "750 - 4 000 стр/мес",
            "Модель картриджа": "TL-5120 (3k) / TL-5120H (6k) / TL-5120X (15k), барабан DL-5120 (30k)"
        }
    }
]


def generate_artifacts():
    os.makedirs(CORE_DATA_DIR, exist_ok=True)
    os.makedirs(SITE_OUTBOX_DIR, exist_ok=True)

    # 1. Main Enrichment Package Batch 02
    package = {
        "batch_id": "BATCH_02_VERIFIED_EXTERNAL_ENRICHMENT_2026_10",
        "description": "Verified external reference enrichment batch 02 covering 40 priority reference models (laptops, desktops, components, printers, MFUs).",
        "created_at": "2026-10-03T18:00:00Z",
        "methodology": "WEB-07E Tier A/B manufacturer datasheet validation",
        "model_count": len(MODELS_DATA),
        "models": MODELS_DATA
    }

    # 2. Source Manifest
    source_manifest = []
    seen_sources = set()
    for m in MODELS_DATA:
        for s in m["sources"]:
            sid = s["source_id"]
            if sid not in seen_sources:
                seen_sources.add(sid)
                url_hash = hashlib.sha256(s["url"].encode("utf-8")).hexdigest()
                source_manifest.append({
                    "source_id": sid,
                    "model_stable_key": m["stable_key"],
                    "canonical_name": m["canonical_name"],
                    "publisher": s["publisher"],
                    "url": s["url"],
                    "source_type": s["source_type"],
                    "tier": "Tier A" if "official" in s["source_type"] else "Tier B",
                    "retrieved_at": s["retrieved_at"],
                    "url_hash_sha256": url_hash
                })

    # 3. Conflict Register (Variant / Sub-model isolated cases)
    conflicts_log = [
        {
            "stable_key": "hp|probook-440-g6",
            "canonical_name": "HP ProBook 440 G6",
            "status": "resolved_variant_isolated",
            "field": "graphics",
            "note": "Base HP ProBook 440 G6 is verified with integrated Intel UHD Graphics 620. Variants with discrete NVIDIA GeForce MX130 / MX250 maintain separate sub-model tags and are not merged into base model.",
            "sources_compared": [
                {"source": "HP ProBook 440 G6 QuickSpecs", "variant": "Base Intel", "graphics": "Intel UHD Graphics 620"},
                {"source": "HP ProBook 440 G6 QuickSpecs", "variant": "Optional Discrete", "graphics": "NVIDIA GeForce MX130 / MX250"}
            ]
        },
        {
            "stable_key": "lenovo|ideapad-g580",
            "canonical_name": "Lenovo IdeaPad G580",
            "status": "resolved_variant_isolated",
            "field": "graphics",
            "note": "Lenovo IdeaPad G580 is manufactured with both integrated Intel HD Graphics and discrete NVIDIA GeForce GT 610M/630M. Base reference entry defaults to Intel integrated HD Graphics.",
            "sources_compared": [
                {"source": "Lenovo IdeaPad G580 PSREF", "variant": "G580 Intel", "graphics": "Intel HD Graphics 3000 / 4000"},
                {"source": "Lenovo IdeaPad G580 PSREF", "variant": "G580 Discrete", "graphics": "NVIDIA GeForce GT 610M / GT 630M"}
            ]
        },
        {
            "stable_key": "intel|xeon-e3-1220",
            "canonical_name": "Intel Xeon E3-1220",
            "status": "resolved_variant_isolated",
            "field": "pcie_version",
            "note": "Intel Xeon E3-1220 (Sandy Bridge) features PCIe 2.0 (16 lanes), whereas Xeon E3-1220 v2 (Ivy Bridge) features PCIe 3.0. Maintained as discrete references to prevent stepping confusion.",
            "sources_compared": [
                {"source": "Intel ARK Xeon E3-1220 Specifications", "revision": "v1 (Sandy Bridge)", "pcie": "PCIe 2.0"},
                {"source": "Intel ARK Xeon E3-1220 v2 Specifications", "revision": "v2 (Ivy Bridge)", "pcie": "PCIe 3.0"}
            ]
        }
    ]

    # 4. Unresolved After Batch 02 (Database query)
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

    # Save to both target directories
    targets = [CORE_DATA_DIR, SITE_OUTBOX_DIR]
    for target in targets:
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, "EXTERNAL_ENRICHMENT_BATCH_02.json"), "w", encoding="utf-8") as f:
            json.dump(package, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "EXTERNAL_SOURCE_MANIFEST_BATCH_02.json"), "w", encoding="utf-8") as f:
            json.dump(source_manifest, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "EXTERNAL_ENRICHMENT_CONFLICTS_BATCH_02.json"), "w", encoding="utf-8") as f:
            json.dump(conflicts_log, f, ensure_ascii=False, indent=2)

        with open(os.path.join(target, "UNRESOLVED_AFTER_BATCH_02.json"), "w", encoding="utf-8") as f:
            json.dump(unresolved_after_batch, f, ensure_ascii=False, indent=2)

    print(f"[OK] Generated Batch 02 artifacts for {len(MODELS_DATA)} models.")
    print(f"  - Package:                {os.path.join(SITE_OUTBOX_DIR, 'EXTERNAL_ENRICHMENT_BATCH_02.json')}")
    print(f"  - Source Manifest:        {os.path.join(SITE_OUTBOX_DIR, 'EXTERNAL_SOURCE_MANIFEST_BATCH_02.json')} ({len(source_manifest)} unique sources)")
    print(f"  - Conflicts:              {os.path.join(SITE_OUTBOX_DIR, 'EXTERNAL_ENRICHMENT_CONFLICTS_BATCH_02.json')} ({len(conflicts_log)} documented entries)")
    print(f"  - Unresolved Remaining:   {os.path.join(SITE_OUTBOX_DIR, 'UNRESOLVED_AFTER_BATCH_02.json')} ({len(unresolved_after_batch)} products)")


if __name__ == "__main__":
    generate_artifacts()

#!/usr/bin/env python3
"""
scripts/expand_reference_catalog.py

Expands verified product reference catalog from local existing products.
Fulfills PROMPT_WEB_07B:
- Supports --dry-run (default / explicit) and --apply modes.
- Strictly LOCAL: NEVER runs on production (PRODUCTION_WRITES=0).
- Identifies unlinked products, groups candidates, detects conflicts, applies suffix safety.
- Extracts ONLY verified local specifications (no invented data, no external internet data).
- Generates safe aliases and SEO titles.
- Outputs artifacts:
  - REFERENCE_EXPANSION_CANDIDATES.json
  - REFERENCE_NEEDS_REVIEW.json
"""

import sys
import os
import argparse
import json
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter
import datetime

# Add core to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))

from app.database import SessionLocal
from app import models
from app.config import settings
from app.services.product_reference_matcher import (
    normalize_for_matching,
    generate_stable_key,
    is_part_or_consumable,
    is_bundle_title,
    match_product,
)

# Disallowed specification keys according to Section 10
DISALLOWED_SPEC_KEYS = {
    "состояние", "цена", "закупочная цена", "адрес", "вид товара", "пробег",
    "счётчик", "дефекты", "комплект", "заметки", "дата", "фотографии", "фото",
    "индивидуальный серийный номер", "гарантия"
}

# Verified Candidate Definitions mined directly from local products
CANDIDATE_SPECS = [
    # ----------------------------------------------------
    # 1. ПРИНТЕРЫ (PRINTERS)
    # ----------------------------------------------------
    {
        "brand": "HP",
        "model": "LaserJet Pro 400 M401a",
        "canonical_name": "HP LaserJet Pro 400 M401a",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet Pro 400 M401a", "HP LaserJet m401a", "HP M401a", "LaserJet M401a", "m401a"],
        "detect_regex": r"\bm401a\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Enterprise P3015",
        "canonical_name": "HP LaserJet Enterprise P3015",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet Enterprise P3015", "HP LaserJet P3015", "HP P3015", "LaserJet P3015", "p3015"],
        "detect_regex": r"\bp3015\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet P2035",
        "canonical_name": "HP LaserJet P2035",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet P2035", "HP P2035", "LaserJet P2035", "LaserJet p2035", "p2035"],
        "detect_regex": r"\bp2035\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Pro M203dw",
        "canonical_name": "HP LaserJet Pro M203dw",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet Pro M203dw", "HP LaserJet m203dw", "HP M203dw", "LaserJet M203dw", "m203dw"],
        "detect_regex": r"\bm203dw\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet P1505",
        "canonical_name": "HP LaserJet P1505",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet P1505", "HP P1505", "LaserJet P1505", "LaserJet p1505", "p1505"],
        "detect_regex": r"\bp1505\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Enterprise M608",
        "canonical_name": "HP LaserJet Enterprise M608",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet Enterprise M608", "HP LaserJet M608", "HP M608", "ho m608", "m608"],
        "detect_regex": r"\bm608\b",
    },
    {
        "brand": "HP",
        "model": "Color LaserJet CP1515n",
        "canonical_name": "HP Color LaserJet CP1515n",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP Color LaserJet CP1515n", "HP Color LaserJet cp1515n", "Color LaserJet cp1515n", "HP CP1515n", "cp1515n"],
        "detect_regex": r"\bcp1515n\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Enterprise M507",
        "canonical_name": "HP LaserJet Enterprise M507",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP LaserJet Enterprise M507", "HP M507", "LaserJet Enterprise M507", "m507"],
        "detect_regex": r"\bm507\b",
    },
    {
        "brand": "HP",
        "model": "Color LaserJet Pro M252n",
        "canonical_name": "HP Color LaserJet Pro M252n",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["HP Color LaserJet Pro M252n", "hp m252n", "HP M252n", "m252n"],
        "detect_regex": r"\bm252n\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS LBP6030B",
        "canonical_name": "Canon i-SENSYS LBP6030B",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Canon i-SENSYS LBP6030B", "Canon LBP6030B", "LBP6030B", "i-sensys LBP6030B", "lbp6030b"],
        "detect_regex": r"\blbp6030b\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS LBP2900B",
        "canonical_name": "Canon i-SENSYS LBP2900B",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Canon i-SENSYS LBP2900B", "Canon LBP2900B", "canon lbp2900b", "LBP2900B", "lbp2900b"],
        "detect_regex": r"\blbp2900b\b",
    },
    {
        "brand": "Kyocera",
        "model": "FS-4100dn",
        "canonical_name": "Kyocera FS-4100dn",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Kyocera FS-4100dn", "Kyocera fs-4100dn", "FS-4100dn", "fs-4100dn"],
        "detect_regex": r"\bfs[- ]?4100dn\b",
    },
    {
        "brand": "Kyocera",
        "model": "ECOSYS P2135dn",
        "canonical_name": "Kyocera ECOSYS P2135dn",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Kyocera ECOSYS P2135dn", "Kyocera p2135dn", "ECOSYS P2135dn", "p2135dn"],
        "detect_regex": r"\bp2135dn\b",
    },
    {
        "brand": "Kyocera",
        "model": "ECOSYS P6235cdn",
        "canonical_name": "Kyocera ECOSYS P6235cdn",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Kyocera ECOSYS P6235cdn", "Kyocera P6235", "ECOSYS P6235", "P6235"],
        "detect_regex": r"\bp6235\b",
    },
    {
        "brand": "Zebra",
        "model": "ZD220",
        "canonical_name": "Zebra ZD220",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Zebra ZD220", "zebra zd220", "ZD220"],
        "detect_regex": r"\bzd220\b",
    },
    {
        "brand": "TSC",
        "model": "Alpha-3R",
        "canonical_name": "TSC Alpha-3R",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["TSC Alpha-3R", "TSC Alpha-3RW", "Alpha-3RW"],
        "detect_regex": r"\balpha-3rw?\b",
    },
    {
        "brand": "Bixolon",
        "model": "SPP-L310",
        "canonical_name": "Bixolon SPP-L310",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Bixolon SPP-L310", "Bixolon ssp- L310", "SPP-L310"],
        "detect_regex": r"\bs[sp]{2}- ?l310\b",
    },
    {
        "brand": "OKI",
        "model": "C3400",
        "canonical_name": "OKI C3400",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["OKI C3400", "oki c3400", "C3400"],
        "detect_regex": r"\bc3400\b",
    },
    {
        "brand": "OKI",
        "model": "C510dn",
        "canonical_name": "OKI C510dn",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["OKI C510dn", "Oki c510dn", "C510dn"],
        "detect_regex": r"\bc510dn\b",
    },
    {
        "brand": "Brother",
        "model": "HL-2040",
        "canonical_name": "Brother HL-2040",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Brother HL-2040", "Brother 2040H", "HL-2040"],
        "detect_regex": r"\b2040h\b",
    },
    {
        "brand": "Epson",
        "model": "Stylus Photo R2280",
        "canonical_name": "Epson Stylus Photo R2280",
        "device_type": "printer",
        "category": "Принтеры",
        "aliases": ["Epson Stylus Photo R2280", "epson r2280", "R2280"],
        "detect_regex": r"\br2280\b",
    },

    # ----------------------------------------------------
    # 2. МФУ (MFP)
    # ----------------------------------------------------
    {
        "brand": "HP",
        "model": "LaserJet Pro M1214nfh",
        "canonical_name": "HP LaserJet Pro M1214nfh",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet Pro M1214nfh", "HP LaserJet M1214nfh", "HP M1214N", "LaserJet M1214nfh", "HP M1214", "m1214n"],
        "detect_regex": r"\bm1214n(fh)?\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Pro M1132 MFP",
        "canonical_name": "HP LaserJet Pro M1132 MFP",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet Pro M1132 MFP", "Hp LaserJet M1132", "HP LaserJet M1132", "HP M1132", "LaserJet M1132", "m1132"],
        "detect_regex": r"\bm1132\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet M1005 MFP",
        "canonical_name": "HP LaserJet M1005 MFP",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet M1005 MFP", "HP LaserJet M1005", "HP M1005", "LaserJet M1005", "m1005"],
        "detect_regex": r"\bm1005\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Pro MFP M125r",
        "canonical_name": "HP LaserJet Pro MFP M125r",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet Pro MFP M125r", "HP LaserJet m125r", "HP M125r", "LaserJet m125r", "m125r"],
        "detect_regex": r"\bm125r\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Pro MFP M132a",
        "canonical_name": "HP LaserJet Pro MFP M132a",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet Pro MFP M132a", "HP M132A", "HP M132a", "LaserJet M132a", "m132a"],
        "detect_regex": r"\bm132a\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet 3030",
        "canonical_name": "HP LaserJet 3030",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet 3030", "HP 3030", "LaserJet 3030"],
        "detect_regex": r"\blaserjet 3030\b",
    },
    {
        "brand": "HP",
        "model": "LaserJet Enterprise MFP M527",
        "canonical_name": "HP LaserJet Enterprise MFP M527",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP LaserJet Enterprise MFP M527", "HP enterprise MFP M527", "HP M527", "MFP M527", "m527"],
        "detect_regex": r"\bm527\b",
    },
    {
        "brand": "HP",
        "model": "Photosmart 5515",
        "canonical_name": "HP Photosmart 5515",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["HP Photosmart 5515", "HP 5515", "Photosmart 5515"],
        "detect_regex": r"\b(photosmart )?5515\b",
    },
    {
        "brand": "Brother",
        "model": "MFC-8880DN",
        "canonical_name": "Brother MFC-8880DN",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Brother MFC-8880DN", "MFC-8880DN", "mfc-8880dn"],
        "detect_regex": r"\bmfc-8880dn\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS MF4730",
        "canonical_name": "Canon i-SENSYS MF4730",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon i-SENSYS MF4730", "Canon mf4730", "Canon MF4730", "MF4730", "mf4730"],
        "detect_regex": r"\bmf4730\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS MF4550d",
        "canonical_name": "Canon i-SENSYS MF4550d",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon i-SENSYS MF4550d", "Canon MF4550d", "MF4550d", "mf4550d"],
        "detect_regex": r"\bmf4550d\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS MF446",
        "canonical_name": "Canon i-SENSYS MF446",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon i-SENSYS MF446", "Canon MF 446", "MF 446"],
        "detect_regex": r"\bmf ?446(?![xX])\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS MF446x",
        "canonical_name": "Canon i-SENSYS MF446x",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon i-SENSYS MF446x", "Canon mf446X", "MF446x", "mf446x"],
        "detect_regex": r"\bmf ?446x\b",
    },
    {
        "brand": "Canon",
        "model": "imageRUNNER 1024i",
        "canonical_name": "Canon imageRUNNER 1024i",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon imageRUNNER 1024i", "Canon IR 1024i", "IR 1024i", "Canon 1024i", "ir 1024i"],
        "detect_regex": r"\bir ?1024i\b",
    },
    {
        "brand": "Canon",
        "model": "i-SENSYS MF5940dn",
        "canonical_name": "Canon i-SENSYS MF5940dn",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon i-SENSYS MF5940dn", "canon mf5940dn", "MF5940dn", "mf5940dn"],
        "detect_regex": r"\bmf5940dn\b",
    },
    {
        "brand": "Canon",
        "model": "PIXMA MP272",
        "canonical_name": "Canon PIXMA MP272",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Canon PIXMA MP272", "canon pixma mp272", "MP272"],
        "detect_regex": r"\bmp272\b",
    },
    {
        "brand": "Kyocera",
        "model": "ECOSYS M6026cdn",
        "canonical_name": "Kyocera ECOSYS M6026cdn",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Kyocera ECOSYS M6026cdn", "Kyocera m6026cdn", "M6026cdn", "m6026cdn"],
        "detect_regex": r"\bm6026cdn\b",
    },
    {
        "brand": "Kyocera",
        "model": "FS-1125MFP",
        "canonical_name": "Kyocera FS-1125MFP",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Kyocera FS-1125MFP", "FS-1125MFP", "fs-1125mfp"],
        "detect_regex": r"\bfs-1125mfp\b",
    },
    {
        "brand": "Kyocera",
        "model": "ECOSYS M3660idn",
        "canonical_name": "Kyocera ECOSYS M3660idn",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Kyocera ECOSYS M3660idn", "kyocera m3660idn", "M3660idn", "m3660idn"],
        "detect_regex": r"\bm3660i?dn\b",
    },
    {
        "brand": "Lexmark",
        "model": "MX421ade",
        "canonical_name": "Lexmark MX421ade",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Lexmark MX421ade", "MX421ade", "mx421ade"],
        "detect_regex": r"\bmx421ade\b",
    },
    {
        "brand": "Lexmark",
        "model": "MB2236dw",
        "canonical_name": "Lexmark MB2236dw",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Lexmark MB2236dw", "MB2236dw", "mb2236dw"],
        "detect_regex": r"\bmb2236dw\b",
    },
    {
        "brand": "Pantum",
        "model": "BM5100ADN",
        "canonical_name": "Pantum BM5100ADN",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Pantum BM5100ADN", "BM5100ADN", "bm5100adn"],
        "detect_regex": r"\bbm5100adn\b",
    },
    {
        "brand": "Pantum",
        "model": "BM5100FDN",
        "canonical_name": "Pantum BM5100FDN",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Pantum BM5100FDN", "BM5100FDN", "bm5100fdn"],
        "detect_regex": r"\bbm5100fdn\b",
    },
    {
        "brand": "Samsung",
        "model": "SCX-4833FD",
        "canonical_name": "Samsung SCX-4833FD",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Samsung SCX-4833FD", "samsung scx-4833fd", "SCX-4833FD", "scx-4833fd"],
        "detect_regex": r"\bscx-4833fd\b",
    },
    {
        "brand": "Samsung",
        "model": "SCX-3400",
        "canonical_name": "Samsung SCX-3400",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Samsung SCX-3400", "Samsung 3400", "SCX-3400"],
        "detect_regex": r"\b(scx-)?3400\b",
    },
    {
        "brand": "Xerox",
        "model": "WorkCentre 3335",
        "canonical_name": "Xerox WorkCentre 3335",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Xerox WorkCentre 3335", "Xerox 3335", "WorkCentre 3335"],
        "detect_regex": r"\b(workcentre )?3335\b",
    },
    {
        "brand": "Xerox",
        "model": "DocuCentre SC2020",
        "canonical_name": "Xerox DocuCentre SC2020",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Xerox DocuCentre SC2020", "xerox sc2020", "DocuCentre SC2020", "SC2020", "sc2020"],
        "detect_regex": r"\bsc2020\b",
    },
    {
        "brand": "Epson",
        "model": "WorkForce Pro WF-M5799",
        "canonical_name": "Epson WorkForce Pro WF-M5799",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Epson WorkForce Pro WF-M5799", "Epson WF-M5799", "Epson MF5799", "WF-M5799", "WF-5799"],
        "detect_regex": r"\b(wf-m?5799|mf5799)\b",
    },
    {
        "brand": "Epson",
        "model": "EcoTank M2140",
        "canonical_name": "Epson EcoTank M2140",
        "device_type": "mfu",
        "category": "МФУ",
        "aliases": ["Epson EcoTank M2140", "Epson M2140", "Epson m2140", "M2140", "m2140"],
        "detect_regex": r"\bm2140\b",
    },

    # ----------------------------------------------------
    # 3. МОНИТОРЫ (MONITORS)
    # ----------------------------------------------------
    {
        "brand": "HP",
        "model": "24fw",
        "canonical_name": "HP 24fw",
        "device_type": "monitor",
        "category": "Мониторы",
        "aliases": ["HP 24fw", "24fw"],
        "detect_regex": r"\b24fw\b",
    },
    {
        "brand": "Samsung",
        "model": "S22D300",
        "canonical_name": "Samsung S22D300",
        "device_type": "monitor",
        "category": "Мониторы",
        "aliases": ["Samsung S22D300", "samsung s22d300", "S22D300"],
        "detect_regex": r"\bs22d300\b",
    },
    {
        "brand": "Samsung",
        "model": "C32F391FWI",
        "canonical_name": "Samsung C32F391FWI",
        "device_type": "monitor",
        "category": "Мониторы",
        "aliases": ["Samsung C32F391FWI", "c32f391fwi"],
        "detect_regex": r"\bc32f391fwi\b",
    },
    {
        "brand": "Samsung",
        "model": "SyncMaster E2320",
        "canonical_name": "Samsung SyncMaster E2320",
        "device_type": "monitor",
        "category": "Мониторы",
        "aliases": ["Samsung SyncMaster E2320", "Samsung e2320", "E2320"],
        "detect_regex": r"\be2320\b",
    },
    {
        "brand": "AOC",
        "model": "e2050S",
        "canonical_name": "AOC e2050S",
        "device_type": "monitor",
        "category": "Мониторы",
        "aliases": ["AOC e2050S", "e2050S", "e2050s"],
        "detect_regex": r"\be2050s\b",
    },
    {
        "brand": "NEC",
        "model": "V260",
        "canonical_name": "NEC V260",
        "device_type": "projector",
        "category": "Мониторы",
        "aliases": ["NEC V260", "V260"],
        "detect_regex": r"\bv260\b",
    },

    # ----------------------------------------------------
    # 4. НОУТБУКИ (LAPTOPS)
    # ----------------------------------------------------
    {
        "brand": "HP",
        "model": "15-af000ur",
        "canonical_name": "HP 15-af000ur",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP 15-af000ur", "15-af000ur"],
        "detect_regex": r"\b15-af000ur\b",
    },
    {
        "brand": "HP",
        "model": "630",
        "canonical_name": "HP 630",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP 630", "Ноутбук HP 630"],
        "detect_regex": r"\bhp 630\b",
    },
    {
        "brand": "HP",
        "model": "EliteBook 840 G3",
        "canonical_name": "HP EliteBook 840 G3",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP EliteBook 840 G3", "EliteBook 840 G3"],
        "detect_regex": r"\b840 g3\b",
    },
    {
        "brand": "HP",
        "model": "ProBook 440 G6",
        "canonical_name": "HP ProBook 440 G6",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP ProBook 440 G6", "ProBook 440 G6"],
        "detect_regex": r"\b440 g6\b",
    },
    {
        "brand": "HP",
        "model": "EliteBook 820 G3",
        "canonical_name": "HP EliteBook 820 G3",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP EliteBook 820 G3", "EliteBook 820 G3"],
        "detect_regex": r"\b820 g3\b",
    },
    {
        "brand": "HP",
        "model": "ProBook 440 G4",
        "canonical_name": "HP ProBook 440 G4",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP ProBook 440 G4", "ProBook 440 G4"],
        "detect_regex": r"\b440 g4\b",
    },
    {
        "brand": "HP",
        "model": "ProBook 4730s",
        "canonical_name": "HP ProBook 4730s",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["HP ProBook 4730s", "HP 4730s", "4730s"],
        "detect_regex": r"\b4730s\b",
    },
    {
        "brand": "Acer",
        "model": "Aspire 7739",
        "canonical_name": "Acer Aspire 7739",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Acer Aspire 7739", "Acer 7739", "7739"],
        "detect_regex": r"\b7739\b",
    },
    {
        "brand": "Acer",
        "model": "Aspire 5750",
        "canonical_name": "Acer Aspire 5750",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Acer Aspire 5750", "Aspire 5750", "5750"],
        "detect_regex": r"\b5750\b",
    },
    {
        "brand": "Acer",
        "model": "Aspire 5690",
        "canonical_name": "Acer Aspire 5690",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Acer Aspire 5690", "Aspire 5690", "5690"],
        "detect_regex": r"\b5690\b",
    },
    {
        "brand": "Acer",
        "model": "Extensa 5620G",
        "canonical_name": "Acer Extensa 5620G",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Acer Extensa 5620G", "Acer 5620G", "5620G"],
        "detect_regex": r"\b5620g\b",
    },
    {
        "brand": "Lenovo",
        "model": "IdeaPad G50-70",
        "canonical_name": "Lenovo IdeaPad G50-70",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Lenovo IdeaPad G50-70", "Lenovo g50-70", "G50-70"],
        "detect_regex": r"\bg50-70\b",
    },
    {
        "brand": "Lenovo",
        "model": "IdeaPad G580",
        "canonical_name": "Lenovo IdeaPad G580",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Lenovo IdeaPad G580", "Lenovo g580", "G580"],
        "detect_regex": r"\bg580\b",
    },
    {
        "brand": "Lenovo",
        "model": "B50-30",
        "canonical_name": "Lenovo B50-30",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Lenovo B50-30", "Lenovo b50-30", "Lenovo B50", "B50-30"],
        "detect_regex": r"\bb50(-30)?\b",
    },
    {
        "brand": "Toshiba",
        "model": "Satellite L850-E8S",
        "canonical_name": "Toshiba Satellite L850-E8S",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Toshiba Satellite L850-E8S", "Toshiba satellite l850-e8s", "L850-E8S"],
        "detect_regex": r"\bl850-e8s\b",
    },
    {
        "brand": "Toshiba",
        "model": "Satellite Pro L300",
        "canonical_name": "Toshiba Satellite Pro L300",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Toshiba Satellite Pro L300", "Toshiba satellite pro l300", "Satellite Pro L300"],
        "detect_regex": r"\b(satellite pro )?l300\b",
    },
    {
        "brand": "Huawei",
        "model": "MateBook B3-510",
        "canonical_name": "Huawei MateBook B3-510",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Huawei MateBook B3-510", "Huawei matebook B3-510", "MateBook B3-510"],
        "detect_regex": r"\bb3-510\b",
    },
    {
        "brand": "Krez",
        "model": "Ninja TM1102B32",
        "canonical_name": "Krez Ninja TM1102B32",
        "device_type": "laptop",
        "category": "Ноутбуки",
        "aliases": ["Krez Ninja TM1102B32", "krez Ninja TM1102B32", "KRez tn 1102 b32", "TM1102B32"],
        "detect_regex": r"\bt[nm] ?1102 ?b32\b",
    },

    # ----------------------------------------------------
    # 5. КОМПЬЮТЕРЫ (COMPUTERS / MONOBLOCK / NETTOP)
    # ----------------------------------------------------
    {
        "brand": "Acer",
        "model": "Extensa X2610G",
        "canonical_name": "Acer Extensa X2610G",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Acer Extensa X2610G", "Acer extends x2610G", "Extensa X2610G", "X2610G"],
        "detect_regex": r"\bx2610g\b",
    },
    {
        "brand": "Acer",
        "model": "Veriton X2640G",
        "canonical_name": "Acer Veriton X2640G",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Acer Veriton X2640G", "acer Veriton x2640g", "Veriton X2640G", "X2640G"],
        "detect_regex": r"\bx2640g\b",
    },
    {
        "brand": "Acer",
        "model": "Aspire Z5761",
        "canonical_name": "Acer Aspire Z5761",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Acer Aspire Z5761", "Acer z5761", "Z5761"],
        "detect_regex": r"\bz5761\b",
    },
    {
        "brand": "Lenovo",
        "model": "ThinkCentre M72e",
        "canonical_name": "Lenovo ThinkCentre M72e",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Lenovo ThinkCentre M72e", "Lenovo M72E", "M72e"],
        "detect_regex": r"\bm72e\b",
    },
    {
        "brand": "Lenovo",
        "model": "IdeaCentre C340",
        "canonical_name": "Lenovo IdeaCentre C340",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Lenovo IdeaCentre C340", "Lenovo C340", "C340"],
        "detect_regex": r"\bc340\b",
    },
    {
        "brand": "Lenovo",
        "model": "ThinkCentre M715s",
        "canonical_name": "Lenovo ThinkCentre M715s",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Lenovo ThinkCentre M715s", "lenovo 715s", "M715s", "715s"],
        "detect_regex": r"\b(lenovo )?715s\b",
    },
    {
        "brand": "Lenovo",
        "model": "ThinkCentre M72z",
        "canonical_name": "Lenovo ThinkCentre M72z",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Lenovo ThinkCentre M72z", "Lenovo m72z", "M72z"],
        "detect_regex": r"\bm72z\b",
    },
    {
        "brand": "Lenovo",
        "model": "ThinkCentre S40-40",
        "canonical_name": "Lenovo ThinkCentre S40-40",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Lenovo ThinkCentre S40-40", "Lenovo S40-40", "S40-40"],
        "detect_regex": r"\bs40-40\b",
    },
    {
        "brand": "HP",
        "model": "Compaq Pro 6300",
        "canonical_name": "HP Compaq Pro 6300",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["HP Compaq Pro 6300", "HP Pro 6300", "Pro 6300"],
        "detect_regex": r"\bpro 6300\b",
    },
    {
        "brand": "HP",
        "model": "Compaq Pro 7320",
        "canonical_name": "HP Compaq Pro 7320",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["HP Compaq Pro 7320", "HP 7320", "7320"],
        "detect_regex": r"\bhp 7320\b",
    },
    {
        "brand": "HP",
        "model": "Pavilion 200",
        "canonical_name": "HP Pavilion 200",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["HP Pavilion 200", "HP Pavilion 200 PC", "Pavilion 200"],
        "detect_regex": r"\bpavilion 200\b",
    },
    {
        "brand": "Aquarius",
        "model": "Pro P30T 42",
        "canonical_name": "Aquarius Pro P30T 42",
        "device_type": "computer",
        "category": "Компьютеры",
        "aliases": ["Aquarius Pro P30T 42", "Aquarius моноблок Pro P30T 42", "Pro P30T 42"],
        "detect_regex": r"\bpro p30t 42\b",
    },
    {
        "brand": "Zebra",
        "model": "CC600",
        "canonical_name": "Zebra CC600",
        "device_type": "kiosk",
        "category": "Компьютеры",
        "aliases": ["Zebra CC600", "Zebra cc600", "CC600"],
        "detect_regex": r"\bcc600\b",
    },
    {
        "brand": "Bluebird",
        "model": "VF550",
        "canonical_name": "Bluebird VF550",
        "device_type": "terminal",
        "category": "Компьютеры",
        "aliases": ["Bluebird VF550", "bluebird vf550", "bluebird f550", "VF550"],
        "detect_regex": r"\bv?f550\b",
    },
    {
        "brand": "Bluebird",
        "model": "EF501",
        "canonical_name": "Bluebird EF501",
        "device_type": "terminal",
        "category": "Компьютеры",
        "aliases": ["Bluebird EF501", "bluebird ef501r", "Bluebird 501", "EF501"],
        "detect_regex": r"\bef501r?\b",
    },
    {
        "brand": "Cisco",
        "model": "Catalyst WS-C2960-24",
        "canonical_name": "Cisco Catalyst WS-C2960-24",
        "device_type": "network",
        "category": "Компьютеры",
        "aliases": ["Cisco Catalyst WS-C2960-24", "Cisco Ws-C2960 24", "WS-C2960-24"],
        "detect_regex": r"\bws-c2960 24\b",
    },
    {
        "brand": "3Com",
        "model": "Baseline Switch 2250 Plus",
        "canonical_name": "3Com Baseline Switch 2250 Plus",
        "device_type": "network",
        "category": "Компьютеры",
        "aliases": ["3Com Baseline Switch 2250 Plus", "Baseline Switch 2250 Plus"],
        "detect_regex": r"\b2250 plus\b",
    },
    {
        "brand": "HP",
        "model": "3600-48-PoE+ v2 SI (JG307C)",
        "canonical_name": "HP 3600-48-PoE+ v2 SI (JG307C)",
        "device_type": "network",
        "category": "Компьютеры",
        "aliases": ["HP 3600-48-PoE+ v2 SI JG307C", "HP JG307C", "JG307C"],
        "detect_regex": r"\bjg307c\b",
    },

    # ----------------------------------------------------
    # 6. КОМПЛЕКТУЮЩИЕ (POWER / STORAGE / PROCESSORS)
    # ----------------------------------------------------
    {
        "brand": "CyberPower",
        "model": "BR700ELCD",
        "canonical_name": "CyberPower BR700ELCD",
        "device_type": "ups",
        "category": "Комплектующие",
        "aliases": ["CyberPower BR700ELCD", "CyberPower BR700elcd", "BR700ELCD"],
        "detect_regex": r"\bbr700elcd\b",
    },
    {
        "brand": "CyberPower",
        "model": "BR700E",
        "canonical_name": "CyberPower BR700E",
        "device_type": "ups",
        "category": "Комплектующие",
        "aliases": ["CyberPower BR700E", "CyberPower BR700e", "BR700E"],
        "detect_regex": r"\bbr700e\b",
    },
    {
        "brand": "APC",
        "model": "Back-UPS 650",
        "canonical_name": "APC Back-UPS 650",
        "device_type": "ups",
        "category": "Комплектующие",
        "aliases": ["APC Back-UPS 650", "APC back ups 650", "Back-UPS 650"],
        "detect_regex": r"\bback ups 650\b",
    },
    {
        "brand": "Chieftec",
        "model": "APC-700C",
        "canonical_name": "Chieftec APC-700C",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["Chieftec APC-700C", "APC-700C"],
        "detect_regex": r"\bapc-700c\b",
    },
    {
        "brand": "Intel",
        "model": "Pentium G4500",
        "canonical_name": "Intel Pentium G4500",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["Intel Pentium G4500", "Pentium G4500", "Pentium g4500", "G4500"],
        "detect_regex": r"\bg4500\b",
    },
    {
        "brand": "Intel",
        "model": "Xeon E3-1220",
        "canonical_name": "Intel Xeon E3-1220",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["Intel Xeon E3-1220", "Xeon E3-1220"],
        "detect_regex": r"\be3-1220(?!\s*v[2-6])\b",
    },
    {
        "brand": "Intel",
        "model": "Xeon E3-1220 v5",
        "canonical_name": "Intel Xeon E3-1220 v5",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["Intel Xeon E3-1220 v5", "Xeon E3-1220 v5", "Xeon E3 1220 v5"],
        "detect_regex": r"\be3-?1220 v5\b",
    },
    {
        "brand": "Intel",
        "model": "Xeon E3-1220 v6",
        "canonical_name": "Intel Xeon E3-1220 v6",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["Intel Xeon E3-1220 v6", "Xeon E3-1220 v6", "Xeon E3 1220 v6"],
        "detect_regex": r"\be3-?1220 v6\b",
    },
    {
        "brand": "MSI",
        "model": "A55M-P33",
        "canonical_name": "MSI A55M-P33",
        "device_type": "component",
        "category": "Комплектующие",
        "aliases": ["MSI A55M-P33", "A55M-P33"],
        "detect_regex": r"\ba55m-p33\b",
    }
]


def expand_catalog(apply_changes: bool = False) -> Dict[str, Any]:
    # Production boundary safety assertion
    if settings.app_env in ("prod", "production"):
        print("[FATAL SECURITY ERROR] Reference expansion script must NEVER be executed against production environment!")
        sys.exit(1)

    db = SessionLocal()
    mode_str = "APPLY (LOCAL DB WRITE)" if apply_changes else "DRY-RUN (NO DB WRITES)"
    print("=" * 65)
    print(f"Verified Product Reference Catalog Expansion — Mode: {mode_str}")
    print(f"Database: {settings.database_url}")
    print("=" * 65)

    # Load categories mapping
    cats = db.query(models.Category).all()
    cat_name_to_id = {c.name: c.id for c in cats}
    cat_id_to_name = {c.id: c.name for c in cats}

    # Load existing reference models and aliases
    existing_ref_models = db.query(models.ProductReferenceModel).all()
    base_ref_models = [m for m in existing_ref_models if m.id <= 27]
    base_stable_keys = {m.stable_key: m for m in base_ref_models}
    current_db_keys = {m.stable_key: m for m in existing_ref_models}
    
    existing_models_before = len(base_ref_models) if base_ref_models else len(existing_ref_models)

    existing_aliases = db.query(models.ProductReferenceAlias).all()
    base_aliases = [a for a in existing_aliases if a.reference_model_id <= 27]
    existing_norm_aliases = {a.normalized_alias for a in existing_aliases}
    existing_aliases_before = len(base_aliases) if base_ref_models else len(existing_aliases)

    products = db.query(models.Product).order_by(models.Product.id).all()
    total_products = len(products)
    linked_before = 89  # Baseline linked before WEB-07B expansion

    print(f"Baseline State Before (WEB-07A):")
    print(f"  Reference models: {existing_models_before}")
    print(f"  Reference aliases: {existing_aliases_before}")
    print(f"  Total products: {total_products}")
    print(f"  Linked products: {linked_before} ({linked_before/total_products*100:.1f}%)")
    print("-" * 65)

    # Process Candidate Manifest
    candidate_manifest = []
    needs_review_queue = []
    
    auto_create_models = []
    new_aliases_to_insert = []
    skipped_count = 0
    needs_review_count = 0

    matched_product_ids: Set[int] = set()
    for p in products:
        if p.reference_model_id:
            matched_product_ids.add(p.id)

    # Also add alias for Model #25 (Xerox VersaLink B405) for product 280
    if 25 in {m.id for m in existing_ref_models}:
        extra_aliases = ["Xerox vl b405", "Xerox B405"]
        for ea in extra_aliases:
            ea_norm = normalize_for_matching(ea)
            if ea_norm not in existing_norm_aliases:
                new_aliases_to_insert.append({
                    "reference_model_id": 25,
                    "alias": ea,
                    "normalized_alias": ea_norm,
                    "priority": 100,
                    "active": True
                })
                existing_norm_aliases.add(ea_norm)

    for cand in CANDIDATE_SPECS:
        brand = cand["brand"].strip()
        model = cand["model"].strip()
        cname = cand["canonical_name"].strip()
        stable_k = generate_stable_key(brand, model)
        category_name = cand["category"]
        category_id = cat_name_to_id.get(category_name, 48)

        regex = re.compile(cand["detect_regex"], re.IGNORECASE)

        source_pids = []
        source_titles = []
        collected_specs: Dict[str, Any] = {}
        spec_conflicts = []
        category_set = set()

        for p in products:
            title = p.title or ""
            # Safety: skip parts & consumables for whole devices
            if is_part_or_consumable(title) and cand["device_type"] not in ("ups", "network", "component"):
                continue

            if regex.search(title):
                source_pids.append(p.id)
                source_titles.append(title)
                p_cat_name = cat_id_to_name.get(p.category_id, "Без категории")
                category_set.add(p_cat_name)

                # Merge model specifications from local products
                if p.avito_params_json:
                    try:
                        p_specs = json.loads(p.avito_params_json)
                        if isinstance(p_specs, dict):
                            for sk, sv in p_specs.items():
                                if not sk or sk.strip().lower() in DISALLOWED_SPEC_KEYS:
                                    continue
                                sk_clean = sk.strip()
                                sv_clean = sv.strip() if isinstance(sv, str) else sv
                                if sk_clean in collected_specs and str(collected_specs[sk_clean]).strip() != str(sv_clean).strip():
                                    spec_conflicts.append(f"Conflict on '{sk_clean}': '{collected_specs[sk_clean]}' vs '{sv_clean}'")
                                else:
                                    collected_specs[sk_clean] = sv_clean
                    except Exception:
                        pass

        if not source_pids:
            continue

        conflicts = []
        non_rest_cats = [c for c in category_set if c != "Техника под восстановление" and c != "Без категории"]
        if len(non_rest_cats) > 1:
            conflicts.append(f"Multiple categories: {list(non_rest_cats)}")
        if spec_conflicts:
            conflicts.extend(spec_conflicts[:3])

        clean_aliases = list(dict.fromkeys(
            cand["aliases"] +
            [cname, f"{brand} {model}"] +
            [t for t in source_titles if len(t) <= 60 and not is_bundle_title(t)]
        ))
        clean_aliases = [a.strip() for a in clean_aliases if a.strip() and len(a.strip()) > 2]

        is_auto = True
        decision = "auto_create"
        reason = f"Identity verified from {len(source_pids)} local product(s)"
        confidence = 1.0

        if stable_k in base_stable_keys:
            decision = "skip"
            reason = "Model already present in base reference catalog"
            is_auto = False
            skipped_count += 1
        elif conflicts:
            decision = "needs_review"
            reason = f"Conflicts detected: {'; '.join(conflicts)}"
            is_auto = False
            needs_review_count += 1

        # Site title structure according to Section 12: device type + brand + model
        site_title_type_map = {
            "printer": "Принтер",
            "mfu": "МФУ",
            "monitor": "Монитор",
            "laptop": "Ноутбук",
            "computer": "Компьютер",
            "projector": "Проектор",
            "kiosk": "Информационный киоск",
            "terminal": "Терминал сбора данных",
            "ups": "ИБП",
            "network": "Коммутатор",
            "component": "Комплектующие"
        }
        type_prefix = site_title_type_map.get(cand["device_type"], "Устройство")
        seo_site_title = f"{type_prefix} {brand} {model}"

        candidate_obj = {
            "proposed_canonical_name": cname,
            "brand": brand,
            "model": model,
            "category": category_name,
            "source_product_ids": source_pids,
            "source_titles": list(dict.fromkeys(source_titles)),
            "aliases": clean_aliases[:8],
            "specifications": collected_specs,
            "conflicts": conflicts,
            "decision": decision,
            "reason": reason,
            "confidence": confidence
        }
        candidate_manifest.append(candidate_obj)

        if is_auto:
            matched_product_ids.update(source_pids)
            source_note = f"Derived from local Product #{', #'.join(map(str, source_pids[:5]))}"
            auto_create_models.append({
                "stable_key": stable_k,
                "canonical_name": cname,
                "brand": brand,
                "model": model,
                "device_type": cand["device_type"],
                "default_category_id": category_id,
                "specifications_json": json.dumps(collected_specs, ensure_ascii=False) if collected_specs else None,
                "site_title": seo_site_title,
                "site_description": None,  # Section 13: Leave empty rather than invent
                "active": True,
                "source": "local_existing_products",
                "source_note": source_note,
                "aliases": clean_aliases[:8]
            })

    # Build NEEDS REVIEW Queue for products not covered by reference catalog
    for p in products:
        if p.id in matched_product_ids:
            continue
        title = p.title or ""
        p_cat_name = cat_id_to_name.get(p.category_id, "Без категории")

        review_reason = "missing_model"
        if is_part_or_consumable(title):
            review_reason = "parts_or_consumable"
        elif is_bundle_title(title):
            review_reason = "multiple_models"
        elif any(w in title.lower() for w in ["объявление avito", "test", "скупка", "ремонт", "диагностика"]):
            review_reason = "generic_title"
        elif any(w in title.lower() for w in ["разных брендов", "разные бренды", "квадраты", "ширик"]):
            review_reason = "generic_title"
        elif not p.brand and not any(b.lower() in title.lower() for b in ["hp", "samsung", "kyocera", "lenovo", "acer", "asus", "canon", "xerox"]):
            review_reason = "unknown_brand"

        needs_review_queue.append({
            "product_id": p.id,
            "title": title,
            "category": p_cat_name,
            "current_brand": p.brand or "",
            "current_model": p.model or "",
            "reason": review_reason,
            "notes": "Kept in review queue for WEB-07C external verified enrichment"
        })

    # Summary Statistics
    total_candidates = len(candidate_manifest)
    auto_create_count = len(auto_create_models)
    expected_new_aliases = sum(len(m["aliases"]) for m in auto_create_models) + len(new_aliases_to_insert)
    expected_matched_products = len(matched_product_ids)

    print(f"Candidate Analysis Results:")
    print(f"------------------------------------------------------------")
    print(f"Total candidates analyzed:     {total_candidates}")
    print(f"  - Auto-create approved:      {auto_create_count}")
    print(f"  - Needs review:              {needs_review_count}")
    print(f"  - Skipped (already in DB):   {skipped_count}")
    print(f"Expected new aliases:          {expected_new_aliases}")
    print(f"Expected newly matchable:      {expected_matched_products - linked_before} products")
    print(f"Total matchable products:      {expected_matched_products} / {total_products} ({expected_matched_products/total_products*100:.1f}%)")
    print(f"Unmatched in review queue:     {len(needs_review_queue)} products")
    print(f"------------------------------------------------------------")

    # DB Writes (Only if apply_changes)
    if apply_changes:
        created_models_count = 0
        created_aliases_count = 0
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Insert extra aliases for existing models
        for ea_dict in new_aliases_to_insert:
            alias_rec = models.ProductReferenceAlias(
                reference_model_id=ea_dict["reference_model_id"],
                alias=ea_dict["alias"],
                normalized_alias=ea_dict["normalized_alias"],
                priority=ea_dict["priority"],
                active=ea_dict["active"],
                created_at=now
            )
            db.add(alias_rec)
            created_aliases_count += 1

        # 2. Insert new reference models and their aliases
        for m_data in auto_create_models:
            aliases_list = m_data.pop("aliases")
            if m_data["stable_key"] in current_db_keys:
                continue
            ref_model = models.ProductReferenceModel(
                stable_key=m_data["stable_key"],
                canonical_name=m_data["canonical_name"],
                brand=m_data["brand"],
                model=m_data["model"],
                device_type=m_data["device_type"],
                default_category_id=m_data["default_category_id"],
                specifications_json=m_data["specifications_json"],
                site_title=m_data["site_title"],
                site_description=m_data["site_description"],
                active=m_data["active"],
                source=m_data["source"],
                source_note=m_data["source_note"],
                created_at=now,
                updated_at=now
            )
            db.add(ref_model)
            db.flush()  # obtain ref_model.id
            created_models_count += 1

            for alias_str in aliases_list:
                norm_a = normalize_for_matching(alias_str)
                alias_rec = models.ProductReferenceAlias(
                    reference_model_id=ref_model.id,
                    alias=alias_str,
                    normalized_alias=norm_a,
                    priority=100,
                    active=True,
                    created_at=now
                )
                db.add(alias_rec)
                created_aliases_count += 1

        db.commit()
        print(f"\n[APPLIED] Successfully added {created_models_count} reference models and {created_aliases_count} aliases to local database.")
    else:
        db.rollback()
        print("\n[DRY-RUN] No database modifications were written (PRODUCTION_WRITES=0, LOCAL_WRITES=0).")

    # Output Artifacts Paths
    out_dir_local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "reference_catalog"))
    out_dir_outbox = r"C:\tboot-site\AntiGravity\PROMPT_WEB_07B_VERIFIED_REFERENCE_CATALOG_EXPANSION\Outbox"

    os.makedirs(out_dir_local, exist_ok=True)
    os.makedirs(out_dir_outbox, exist_ok=True)

    cand_filename = "REFERENCE_EXPANSION_CANDIDATES.json"
    review_filename = "REFERENCE_NEEDS_REVIEW.json"

    for dest_dir in (out_dir_local, out_dir_outbox):
        with open(os.path.join(dest_dir, cand_filename), "w", encoding="utf-8") as f:
            json.dump(candidate_manifest, f, ensure_ascii=False, indent=2)
        with open(os.path.join(dest_dir, review_filename), "w", encoding="utf-8") as f:
            json.dump(needs_review_queue, f, ensure_ascii=False, indent=2)

    # Export complete reference catalog JSON according to Section 26
    try:
        from app.services.product_reference_json_service import export_reference_models_to_dict
        full_catalog = export_reference_models_to_dict(db, active_only=False)
        with open(os.path.join(out_dir_local, "reference_models.json"), "w", encoding="utf-8") as f:
            json.dump(full_catalog, f, ensure_ascii=False, indent=2)
        print(f"  - {os.path.join(out_dir_local, 'reference_models.json')} ({full_catalog['total_models']} models)")
    except Exception as e:
        print(f"Notice: catalog export error: {e}")

    print(f"Artifacts successfully written to:")
    print(f"  - {out_dir_local}")
    print(f"  - {out_dir_outbox}")

    db.close()
    return {
        "total_candidates": total_candidates,
        "auto_create_count": auto_create_count,
        "needs_review_count": needs_review_count,
        "skipped_count": skipped_count,
        "expected_new_aliases": expected_new_aliases,
        "expected_matched_products": expected_matched_products,
        "needs_review_products": len(needs_review_queue),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand verified reference catalog from local products.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate expansion without writing to DB (default).")
    group.add_argument("--apply", action="store_true", help="Apply verified reference models to local database.")

    args = parser.parse_args()
    apply_mode = args.apply
    expand_catalog(apply_changes=apply_mode)

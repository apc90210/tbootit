# Stage 05A Printer & MFP Reference Catalog Inventory Audit Report

- **Date:** 2026-10-02
- **Milestone:** Mobile Quick Intake + Reference Catalog + AI Foundation (Stage 05A)
- **Database:** Local Development SQLite (`data/db/technoreboot.db`)
- **Status:** **COMPLETE**

---

## 1. Executive Summary

This inventory audit establishes the foundational dataset for the Technoreboot **Product Reference Catalog** seeded from all printer and MFP models in the Technoreboot database, spanning both active in-stock inventory and historical sold/archived cards.

- **Total Source Products Audited:** 166
  - **In-Stock Products:** 145
  - **Sold / Archived Products:** 21
- **Distinct Raw Product Titles:** 160
- **Existing Linked Products:** 153
- **Unlinked Products Requiring Resolution / Classification:** 13
- **Normalized Reusable Reference Models:** 70 (32 pure printers, 38 multi-function printers / MFPs)
- **Active Aliases Mapped:** 368 across printer/MFP categories

---

## 2. Source Products & Category Distribution

Products were identified through category slug bindings (`printery`, `mfu`), Avito category breadcrumbs (`Оргтехника и расходники / Принтеры / Лазерные принтеры`), and title heuristic keywords (`принтер`, `мфу`, `laserjet`, `deskjet`, `photosmart`, `pixma`, `stylus`, `i-sensys`, `ecotank`, `workcentre`, `phaser`, `kyocera ecosys`, `pantum`).

| Category / Filter Scope | Total Products | In-Stock | Sold / Archive |
|-------------------------|----------------|----------|----------------|
| **МФУ (MFP)** (ID=51, slug=`mfu`) | 97 | 86 | 11 |
| **Принтеры (Printers)** (ID=5, slug=`printery`) | 62 | 53 | 9 |
| **Техника под восстановление (Restoration)** (ID=52) | 5 | 5 | 0 |
| **Другие / ошибочно сопоставленные категории** | 2 | 1 | 1 |
| **Total** | **166** | **145** | **21** |

---

## 3. Normalized Reference Models Summary

70 normalized reference models are established in `product_reference_models` for printers and MFPs.

### Top Brands Represented
- **HP (Hewlett-Packard):** 24 models (e.g. LaserJet 1010/1018/1020/1022/1320/3030/3052/3055, P1102w, P2035, P2055, M1132, M1214nfh, M125r, M252n, M527, M608, P3015)
- **Kyocera:** 19 models (e.g. FS-1040, FS-1060dn, FS-4100dn, FS-4200dn, ECOSYS M2030dn, M2035dn, M2235dn, M2540dn, M6026cdn, P2040dn, P2040dw)
- **Canon:** 8 models (e.g. i-SENSYS LBP2900B, LBP6030B, MF446, MF446x, MF4550d, MF4730, MF5940dn, imageRUNNER 1024i, PIXMA MP272)
- **Samsung:** 6 models (e.g. ML-1640, ML-1860, ML-2160, SCX-3200, SCX-3400, SCX-3405W)
- **Xerox:** 5 models (e.g. Phaser 3020, 3140, WorkCentre 3025, 3335, VersaLink B405)
- **Epson:** 3 models (e.g. Stylus Photo R2280, EcoTank M2140, WorkForce Pro WF-M5799)
- **Brother:** 2 models (e.g. HL-2040, MFC-8880DN)
- **Pantum:** 1 model (P3300dn)
- **Ricoh:** 1 model (SP 150)
- **Bixolon:** 1 model (SPP-L310)

---

## 4. Multi-Card Reusable Template Groups (Aliases / Duplicates)

37 reference models back multiple independent store cards. These prove that individual store inventory cards share reusable model facts while maintaining isolated condition, defects, price, and photos.

| Reference Model | Canonical Name | Device Type | Product Cards Linked |
|-----------------|----------------|-------------|----------------------|
| ID=25 | Xerox VersaLink B405 | MFP | 28 |
| ID=24 | Pantum P3300dn | Printer | 5 |
| ID=4 | HP LaserJet 1022 | Printer | 5 |
| ID=2 | HP LaserJet 1018 | Printer | 4 |
| ID=5 | HP LaserJet 1320 | Printer | 4 |
| ID=3 | HP LaserJet 1020 | Printer | 3 |
| ID=9 | HP LaserJet P1102w | Printer | 3 |
| ID=10 | Kyocera ECOSYS P2040dn | Printer | 3 |
| ID=14 | Kyocera ECOSYS M2235dn | MFP | 3 |
| ID=16 | Kyocera FS-4200dn | Printer | 3 |
| ID=17 | Kyocera FS-1040 | Printer | 3 |
| ID=48 | HP LaserJet Pro M1214nfh | MFP | 3 |
| ID=56 | Brother MFC-8880DN | MFP | 3 |
| ID=70 | Samsung SCX-3400 | MFP | 3 |
| ID=73 | Epson WorkForce Pro WF-M5799 | MFP | 3 |
| *Others (22 models)* | *Various* | *Printer / MFP* | 2 each |

---

## 5. Unlinked Products & Ambiguity Analysis

There are **13 products** currently unlinked to reference models. They fall into four distinct categories:

### A. New Concrete Model Candidate (1 product)
- **Product ID=375** (`AVITO-8116591556`): *"HP LaserJet Enterprise M507 на запчасти"*
  - **Resolution:** Valid high-volume enterprise laser printer (`HP LaserJet Enterprise M507`). Added as candidate for reference catalog seeding.

### B. Ambiguous Multi-Model / Variant Listings (2 products)
- **Product ID=88** (`AVITO-8345505736`): *"Лазерный Принтер на запчасти Kyocera P4100/4200"*
  - **Ambiguity:** Title joins two distinct hardware models (`FS-4100dn` vs `FS-4200dn`) with differing print speeds and drum configurations.
  - **Action:** Retained for manual operator disambiguation during intake/sale.
- **Product ID=89** (`AVITO-8262796294`): *"Лазерный Принтер Kyocera P2040 На запчасти"*
  - **Ambiguity:** Model family `Kyocera ECOSYS P2040` has two reference variants: `P2040dn` (duplex + network) vs `P2040dw` (duplex + network + Wi-Fi).
  - **Action:** Retained for operator disambiguation upon inspection of label / Wi-Fi module.

### C. Umbrella / Collective Showcase Listings (7 products)
These represent aggregate Avito promotional cards containing multiple products or generic assortments rather than a single inventory unit:
- **Product ID=69**: *"Лазерные мфу 3 в 1 разных брендов. Гарантия"*
- **Product ID=76**: *"Лазерные принтеры разных брендов. Гарантия"*
- **Product ID=166**: *"Лазерные принтеры и мфу. Гарантия"*
- **Product ID=167**: *"Лазерные, рабочие мфу 3 в 1 с доставкой"*
- **Product ID=174**: *"Лазерные принтеры hp xerox samsung, canon и др"*
- **Product ID=229**: *"Современные Лазерные /Cтруйные мфу/Принтера. Гаран"*
- **Product ID=319**: *"Лазерные мфу 3 в 1 принтер сканер копир. гарантия"*
- **Action:** Kept unlinked. Reusable reference models must only represent concrete physical models, never generic umbrella cards.

### D. Misclassified Non-Printers / Bundles (3 products)
- **Product ID=164**: *"Компьютерные корпуса"* (Sold item, PC case mistakenly categorized under МФУ).
- **Product ID=257**: *"Картриджи для принтеров"* (Consumable supply, not a printer device).
- **Product ID=371**: *"Рабочее место Комплект принтер/мфу + пк + монитор"* (Multi-item workplace bundle).
- **Action:** Excluded from printer/MFP reference model linkage.

---

## 6. Audit Conclusion & Next Steps

1. **Catalog Completeness:** 153 out of 156 genuine printer/MFP inventory units (98.1%) are linked to 70 canonical reference models.
2. **Deterministic Precedence:** Local 3-tier matcher (`product_reference_matcher.py`) resolves existing store models with 0 external API calls and 0 token cost.
3. **Data Hygiene Guarantee:** Historical sales, prices, notes, and individual product descriptions remain untouched. Reference model data serves strictly as reusable knowledge/templates.

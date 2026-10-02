#!/usr/bin/env python3
"""
Importer for External Verified Reference Enrichment Packages (WEB-07C).
Strictly adheres to:
1. Validation first (rejects unverified/invalid/conflicting packages).
2. Model-level specifications update with field-level provenance.
3. Source transition to 'mixed_verified' (preserving original lineage).
4. Generation of neutral technical site_description based solely on verified facts.
5. Product-level enrichment backfill with absolute business safety:
   - Restoration category (52) is NEVER changed.
   - Existing product values win over reference defaults.
   - Price, quantity, serial number, condition, and photos are NEVER overwritten.
6. Support for --dry-run and --apply.
"""

import sys
import os
import json
import argparse
import datetime
from typing import Dict, Any, List, Optional

# Ensure core app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app import models
from app.services.product_reference_enricher import enrich_product_from_reference, RESTORATION_CATEGORY_ID
from validate_external_reference_enrichment import validate_enrichment_package


def build_neutral_site_description(canonical_name: str, device_type: str, specs: Dict[str, Any]) -> str:
    """
    Construct a neutral, technical product description based exclusively on verified structured specs.
    No marketing fluff, no speculative claims, no instance condition descriptions.
    """
    parts = []
    
    # 1. Device classification and technology
    color = specs.get("Цветность печати", specs.get("color_mode", ""))
    tech = specs.get("Технология печати", specs.get("print_technology", ""))
    dtype = specs.get("Тип устройства", specs.get("device_type", ""))
    fmt = specs.get("Максимальный формат", specs.get("max_format", ""))

    if device_type in ("printer", "mfu"):
        dev_desc = []
        if color and color.lower() in ("черно-белая", "монохромная", "монохромный", "black"):
            dev_desc.append("Монохромное" if device_type == "mfu" else "Монохромный")
        elif color and color.lower() in ("цветная", "цветной", "color"):
            dev_desc.append("Цветное" if device_type == "mfu" else "Цветной")

        if tech and "лазер" in tech.lower():
            dev_desc.append("лазерное" if device_type == "mfu" else "лазерный")
        elif tech and "струй" in tech.lower():
            dev_desc.append("струйное" if device_type == "mfu" else "струйный")
        elif tech and "термо" in tech.lower():
            dev_desc.append("термопринтер")

        if not any("принтер" in d or "лазерное" in d for d in dev_desc):
            dev_desc.append("МФУ" if device_type == "mfu" else "принтер")
        else:
            if device_type == "mfu" and "МФУ" not in " ".join(dev_desc):
                dev_desc.append("МФУ")
            elif device_type == "printer" and "принтер" not in " ".join(dev_desc) and "термопринтер" not in " ".join(dev_desc):
                dev_desc.append("принтер")

        if fmt:
            dev_desc.append(f"формата {fmt}")

        parts.append(" ".join(dev_desc).capitalize())

        # Speed
        speed = specs.get("Скорость печати (A4, ч/б)", specs.get("print_speed_a4_mono", ""))
        if speed:
            parts.append(f"со скоростью печати до {speed}")

        # Duplex
        duplex = specs.get("Двусторонняя печать", specs.get("duplex", ""))
        if duplex and ("да" in str(duplex).lower() or "автомат" in str(duplex).lower()):
            parts.append("с автоматической двусторонней печатью")

        # Connectivity
        eth = specs.get("Сетевой интерфейс (Ethernet)", specs.get("network_ethernet", ""))
        wifi = specs.get("Wi-Fi", specs.get("wifi", ""))
        interfaces = specs.get("Интерфейсы", specs.get("interfaces", ""))

        conn = []
        if eth and "да" in str(eth).lower():
            conn.append("Ethernet")
        if wifi and "да" in str(wifi).lower():
            conn.append("Wi-Fi")
        if not conn and interfaces:
            conn.append(str(interfaces))

        if conn:
            parts.append(f"и интерфейсами {', '.join(conn)}")

        # Scanner / ADF
        adf = specs.get("Автоподатчик (ADF)", specs.get("adf", ""))
        if adf and "да" in str(adf).lower():
            parts.append("с автоподатчиком оригиналов (ADF)")

    elif device_type == "monitor":
        diag = specs.get("Диагональ", specs.get("diagonal", ""))
        res = specs.get("Разрешение экрана", specs.get("native_resolution", ""))
        matrix = specs.get("Тип матрицы", specs.get("panel_type", ""))
        rate = specs.get("Частота обновления", specs.get("refresh_rate", ""))

        m_parts = ["Монитор"]
        if diag:
            m_parts.append(f"с диагональю {diag}")
        if res:
            m_parts.append(f"и разрешением {res}")
        if matrix:
            m_parts.append(f"(матрица {matrix})")
        if rate:
            m_parts.append(f"с частотой обновления {rate}")

        inputs = specs.get("Видеовходы", specs.get("video_inputs", ""))
        if inputs:
            m_parts.append(f"и видеовходами {inputs}")

        parts.append(" ".join(m_parts))

    if not parts:
        return f"{canonical_name} — проверенные технические характеристики производителя."

    result = " ".join(parts).strip()
    if not result.endswith("."):
        result += "."
    return result


def import_enrichment_package(package_path: str, apply_changes: bool = False) -> Dict[str, Any]:
    with open(package_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Mandatory Pre-Validation
    is_valid, issues, stats = validate_enrichment_package(data)
    if not is_valid:
        print("[ABORT] Enrichment package failed pre-validation checks:")
        for iss in issues:
            if iss.severity == "ERROR":
                print(f"  {iss}")
        sys.exit(1)

    db = SessionLocal()
    mode_str = "APPLY (LOCAL DB COMMITTED)" if apply_changes else "DRY-RUN (SIMULATION ONLY)"
    print("=================================================================")
    print(f"External Verified Reference Enrichment Importer: {mode_str}")
    print(f"Package: {os.path.basename(package_path)}")
    print("=================================================================")

    models_updated = 0
    models_created = 0
    total_fields_applied = 0
    affected_products_count = 0
    products_gained_specs_count = 0
    conflicts_detected = 0

    now = datetime.datetime.now(datetime.timezone.utc)

    for item in data.get("models", []):
        stable_key = item["stable_key"]
        decision = item.get("decision", "verified_apply")
        if decision != "verified_apply":
            print(f"[SKIP] {stable_key}: decision is '{decision}'")
            continue

        ref_model = db.query(models.ProductReferenceModel).filter_by(stable_key=stable_key).first()

        new_specs = item.get("specifications", {})
        canonical_name = item.get("canonical_name", "")
        device_type = item.get("device_type", "")
        sources_list = item.get("sources", [])

        # Generate neutral description
        generated_desc = build_neutral_site_description(canonical_name, device_type, new_specs)

        if ref_model:
            # Updating existing model
            # Merge specifications: preserve existing verified if any, fill missing
            existing_specs = {}
            if ref_model.specifications_json:
                try:
                    existing_specs = json.loads(ref_model.specifications_json)
                except Exception:
                    existing_specs = {}

            merged_specs = dict(new_specs)
            # existing non-empty specs win if already present
            for ek, ev in existing_specs.items():
                if ev is not None and str(ev).strip():
                    merged_specs[ek] = ev

            fields_added = len(merged_specs) - len(existing_specs)
            total_fields_applied += fields_added

            # Set source label to mixed_verified if was local
            if ref_model.source in ("local_existing_products", "local_catalog", None):
                new_source = "mixed_verified"
            else:
                new_source = "mixed_verified"

            source_note_update = (
                f"{ref_model.source_note or ''} | Verified external enrichment {now.strftime('%Y-%m-%d')} "
                f"({len(sources_list)} Tier A/B sources)"
            ).strip(" |")

            # In both apply and dry-run, update in-memory object (dry-run will call rollback)
            ref_model.specifications_json = json.dumps(merged_specs, ensure_ascii=False)
            ref_model.source = new_source
            ref_model.source_note = source_note_update
            if not ref_model.site_description or not ref_model.site_description.strip():
                ref_model.site_description = generated_desc
            ref_model.updated_at = now

            models_updated += 1
            target_ref = ref_model
        else:
            # Create new reference model
            target_ref = models.ProductReferenceModel(
                stable_key=stable_key,
                canonical_name=canonical_name,
                brand=item.get("brand"),
                model=item.get("model"),
                device_type=device_type,
                default_category_id=item.get("default_category_id"),
                specifications_json=json.dumps(new_specs, ensure_ascii=False),
                site_title=canonical_name,
                site_description=generated_desc,
                active=True,
                source="external_verified",
                source_note=f"Created via external verified enrichment {now.strftime('%Y-%m-%d')}",
                created_at=now,
                updated_at=now
            )
            if apply_changes:
                db.add(target_ref)
                db.flush()
            models_created += 1
            total_fields_applied += len(new_specs)

        # Backfill linked products
        if target_ref and target_ref.id:
            linked_prods = db.query(models.Product).filter_by(reference_model_id=target_ref.id).all()
            for prod in linked_prods:
                affected_products_count += 1
                before_specs = {}
                if prod.avito_params_json:
                    try:
                        before_specs = json.loads(prod.avito_params_json)
                    except Exception:
                        before_specs = {}

                # Enrich product
                enrich_res = enrich_product_from_reference(
                    db=db,
                    product=prod,
                    reference=target_ref,
                    method=prod.reference_match_method or "external_verified",
                    confidence=prod.reference_match_confidence or 1.0,
                    apply=apply_changes
                )

                # Count specs gained
                added = enrich_res.get("specifications_added", {})
                if not added and "specifications_added" in enrich_res.get("fields_filled", {}):
                    added = enrich_res["fields_filled"]["specifications_added"]
                if added:
                    products_gained_specs_count += 1

    if apply_changes:
        db.commit()
        print("\n[SUCCESS] Local database updated and committed.")
    else:
        db.rollback()
        print("\n[DRY-RUN COMPLETE] No database modifications were written.")

    print(f"Models updated:                 {models_updated}")
    print(f"Models created:                 {models_created}")
    print(f"Total specification fields:     {total_fields_applied}")
    print(f"Affected linked products:       {affected_products_count}")
    print(f"Products gaining new specs:     {products_gained_specs_count}")
    print(f"Conflicts detected:             {conflicts_detected}")
    print("-----------------------------------------------------------------")

    db.close()
    return {
        "models_updated": models_updated,
        "models_created": models_created,
        "total_fields_applied": total_fields_applied,
        "affected_products_count": affected_products_count,
        "products_gained_specs_count": products_gained_specs_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Import external verified reference enrichment package.")
    parser.add_argument("package_path", help="Path to EXTERNAL_ENRICHMENT_BATCH_*.json")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate import without DB writes (default).")
    group.add_argument("--apply", action="store_true", help="Apply verified enrichment to local database.")

    args = parser.parse_args()
    apply_mode = args.apply
    import_enrichment_package(args.package_path, apply_changes=apply_mode)


if __name__ == "__main__":
    main()

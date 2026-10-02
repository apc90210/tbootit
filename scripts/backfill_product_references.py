#!/usr/bin/env python3
"""
Backfill Product References Script.
Fulfills PROMPT_WEB_07A Section 19:
- Supports --dry-run (default / explicit) and --apply modes.
- Strictly LOCAL: NEVER runs on production.
- Uses deterministic multi-tier matcher and safe enrichment policy.
- Reports:
  - total products;
  - matched exact (tier1);
  - matched brand+model (tier2/3);
  - unmatched;
  - ambiguous;
  - fields enriched / that would be enriched;
  - zero writes during dry-run.
"""

import sys
import os
import argparse
from typing import Dict, Any, List
from collections import Counter

# Add core to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))

from app.database import SessionLocal
from app import models
from app.config import settings
from app.services.product_reference_matcher import match_product
from app.services.product_reference_enricher import enrich_product_from_reference


def run_backfill(apply_changes: bool = False):
    # Production boundary safety assertion
    if settings.app_env in ("prod", "production"):
        print("[FATAL SECURITY ERROR] Backfill script must NEVER be executed against production environment!")
        sys.exit(1)

    db = SessionLocal()
    mode_str = "APPLY (LOCAL DB WRITE)" if apply_changes else "DRY-RUN (NO DB WRITES)"
    print(f"============================================================")
    print(f"Product Reference Backfill — Mode: {mode_str}")
    print(f"Database: {settings.database_url}")
    print(f"============================================================")

    from sqlalchemy.orm import joinedload
    cached_ref_models = (
        db.query(models.ProductReferenceModel)
        .options(joinedload(models.ProductReferenceModel.aliases))
        .filter(models.ProductReferenceModel.active == True)
        .all()
    )

    products = db.query(models.Product).order_by(models.Product.id).all()
    total_products = len(products)

    matched_exact = 0
    matched_brand_model = 0
    unmatched = 0
    ambiguous = 0
    already_linked = 0
    fields_enriched_counter = Counter()
    enriched_products_summary = []

    for prod in products:
        if prod.reference_model_id:
            already_linked += 1

        m_res = match_product(
            db=db,
            title=prod.title,
            brand=prod.brand,
            model=prod.model,
            description=prod.description,
            active_only=True,
            cached_models=cached_ref_models
        )

        if m_res.matched and m_res.reference_model:
            if m_res.method == "tier1_exact_alias":
                matched_exact += 1
            else:
                matched_brand_model += 1

            # Preview or apply enrichment
            enrich_res = enrich_product_from_reference(
                db=db,
                product=prod,
                reference=m_res.reference_model,
                method=m_res.method,
                confidence=m_res.confidence,
                apply=apply_changes
            )

            fields_filled = enrich_res.get("fields_filled", {})
            if fields_filled:
                for fk in fields_filled:
                    if fk == "specifications_added":
                        fields_enriched_counter["specifications (new)"] += len(fields_filled[fk])
                    else:
                        fields_enriched_counter[f"{fk} (new)"] += 1
            else:
                # Fields already enriched in prior run
                fields_enriched_counter["already_enriched_up_to_date"] += 1

            # Count reference model fields actively in use
            if prod.brand:
                fields_enriched_counter["active_brand_populated"] += 1
            if prod.model:
                fields_enriched_counter["active_model_populated"] += 1
            if prod.category_id:
                fields_enriched_counter["active_category_populated"] += 1
            if prod.site_title:
                fields_enriched_counter["active_site_title_populated"] += 1
            if prod.site_description:
                fields_enriched_counter["active_site_desc_populated"] += 1

            if len(enriched_products_summary) < 10:
                enriched_products_summary.append({
                    "id": prod.id,
                    "title": prod.title,
                    "matched_reference": m_res.canonical_name,
                    "method": m_res.method,
                    "confidence": m_res.confidence,
                    "new_fields_filled": list(fields_filled.keys()) if fields_filled else ["already_up_to_date"]
                })
        elif m_res.status == "needs_review":
            ambiguous += 1
        else:
            unmatched += 1

    if apply_changes:
        db.commit()
        print("\n[APPLIED] Changes successfully committed to local database.")
    else:
        db.rollback()
        print("\n[DRY-RUN] No database modifications were written (0 writes).")

    total_matched = matched_exact + matched_brand_model
    match_pct = (total_matched / total_products * 100) if total_products > 0 else 0

    print(f"\nBackfill Summary Statistics:")
    print(f"------------------------------------------------------------")
    print(f"Total products in DB:          {total_products}")
    print(f"Total matched:                 {total_matched} ({match_pct:.1f}%)")
    print(f"  - Tier 1 (exact alias):      {matched_exact}")
    print(f"  - Tier 2/3 (brand + model):  {matched_brand_model}")
    print(f"Ambiguous (needs_review):      {ambiguous}")
    print(f"Unmatched:                     {unmatched}")
    print(f"Already linked in DB:          {already_linked}")
    print(f"------------------------------------------------------------")
    print(f"Fields enriched / that would be filled:")
    for fk, count in fields_enriched_counter.items():
        print(f"  - {fk:24}: {count}")
    print(f"------------------------------------------------------------")

    if enriched_products_summary:
        print(f"\nSample Enriched Products (First {len(enriched_products_summary)}):")
        for s in enriched_products_summary:
            print(f"  [#{s['id']}] {s['title'][:45]} -> {s['matched_reference']} ({s['method']}, conf={s['confidence']:.2f})")
            print(f"       Filled: {s['new_fields_filled']}")

    db.close()
    return {
        "total_products": total_products,
        "total_matched": total_matched,
        "matched_exact": matched_exact,
        "matched_brand_model": matched_brand_model,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "fields_enriched": dict(fields_enriched_counter),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill reference models for local products.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate enrichment without making DB writes (default).")
    group.add_argument("--apply", action="store_true", help="Apply enrichment and write changes to local database.")

    args = parser.parse_args()
    apply_mode = args.apply
    run_backfill(apply_changes=apply_mode)

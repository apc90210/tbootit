#!/usr/bin/env python3
"""
Backfill product categories to canonical 7-category taxonomy.
Usage:
    python scripts/backfill_product_categories.py --dry-run
    python scripts/backfill_product_categories.py --apply
"""

import argparse
import json
import os
import sys
import sqlite3
from typing import Dict, Any, List, Tuple

# Add core path to sys.path so we can import services
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
core_dir = os.path.join(repo_root, "core")
if os.path.exists(core_dir) and core_dir not in sys.path:
    sys.path.insert(0, core_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.services.product_categorizer import (
    classify_product,
    CANONICAL_CATEGORIES,
    SPECIFIC_CANONICAL_NAMES,
)

DB_PATH = os.path.join(repo_root, "data", "db", "technoreboot.db")
if not os.path.exists(DB_PATH):
    alt_db = os.path.join(core_dir, "data", "db", "technoreboot.db")
    if os.path.exists(alt_db):
        DB_PATH = alt_db
    else:
        alt_db2 = os.path.join(repo_root, "technoreboot.db")
        if os.path.exists(alt_db2):
            DB_PATH = alt_db2

CANONICAL_ORDER = [
    "Компьютеры",
    "Ноутбуки",
    "Принтеры",
    "МФУ",
    "Мониторы",
    "Комплектующие",
    "Техника под восстановление",
    "Без категории",
]


def ensure_canonical_categories(conn: sqlite3.Connection, apply: bool = False) -> Dict[str, int]:
    """
    Ensure the 7 canonical categories exist with canonical slugs.
    Returns map of {category_name: category_id}.
    """
    cur = conn.cursor()
    existing = cur.execute("SELECT id, name, slug FROM categories").fetchall()
    by_name = {row[1]: (row[0], row[2]) for row in existing}

    canonical_ids = {}

    for name in CANONICAL_ORDER:
        slug = CANONICAL_CATEGORIES[name]["slug"]
        if name in by_name:
            cat_id, curr_slug = by_name[name]
            canonical_ids[name] = cat_id
            if curr_slug != slug and apply:
                cur.execute("UPDATE categories SET slug = ? WHERE id = ?", (slug, cat_id))
        else:
            if apply:
                cur.execute(
                    "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
                    (name, slug, f"Каноническая категория «{name}»")
                )
                cat_id = cur.lastrowid
                canonical_ids[name] = cat_id
            else:
                # Mock ID for dry-run
                canonical_ids[name] = -1

    if apply:
        conn.commit()

    return canonical_ids


def run_backfill(mode: str):
    is_apply = (mode == "--apply")
    print(f"=== BACKFILL PRODUCT CATEGORIES ({'APPLY' if is_apply else 'DRY RUN'}) ===")
    print(f"Database path: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Pre-flight check: ensure categories
    canonical_ids = ensure_canonical_categories(conn, apply=is_apply)
    print(f"Canonical category IDs: {canonical_ids}")

    # Fetch all categories for lookup
    all_cats = cur.execute("SELECT id, name, slug FROM categories").fetchall()
    cats_by_id = {r[0]: r[1] for r in all_cats}

    # Fetch all products
    products = cur.execute("""
        SELECT id, title, site_title, brand, model, description, category_id, status, quantity, is_published_site
        FROM products
        ORDER BY id ASC
    """).fetchall()

    target_counts: Dict[str, int] = {c: 0 for c in CANONICAL_ORDER}
    target_visible_counts: Dict[str, int] = {c: 0 for c in CANONICAL_ORDER}

    already_valid = 0
    to_change = 0
    unknown_fallback = 0
    examples: List[Dict[str, Any]] = []

    changes_to_apply: List[Tuple[int, int, str, str, str]] = []  # (prod_id, new_cat_id, old_cat_name, new_cat_name, reason)

    for p in products:
        pid, title, site_title, brand, model, desc, cat_id, status, qty, pub = p
        existing_cat_name = cats_by_id.get(cat_id)

        res = classify_product(
            title=title,
            site_title=site_title,
            brand=brand,
            model=model,
            description=desc,
            existing_category_name=existing_cat_name,
            allow_override_valid_category=False,
        )

        target_name = res.category_name
        target_counts[target_name] = target_counts.get(target_name, 0) + 1

        is_visible = (status == "in_stock" and qty > 0 and pub == 1)
        if is_visible:
            target_visible_counts[target_name] = target_visible_counts.get(target_name, 0) + 1

        if res.confidence == "fallback":
            unknown_fallback += 1

        target_cat_id = canonical_ids.get(target_name)

        if cat_id is not None and cat_id == target_cat_id:
            already_valid += 1
        else:
            to_change += 1
            changes_to_apply.append((pid, target_cat_id, existing_cat_name or "NULL", target_name, res.reason))
            if len(examples) < 50:
                examples.append({
                    "id": pid,
                    "title": (title or "")[:50],
                    "old_category": existing_cat_name or "NULL",
                    "new_category": target_name,
                    "reason": res.reason,
                    "is_visible": is_visible,
                })

    # Output summary table
    print("\n| Target category | Total Count | Visible Count |")
    print("|---|---:|---:|")
    for cat in CANONICAL_ORDER:
        print(f"| {cat} | {target_counts.get(cat, 0)} | {target_visible_counts.get(cat, 0)} |")

    print(f"\nTotal products: {len(products)}")
    print(f"Already valid / preserved: {already_valid}")
    print(f"To change: {to_change}")
    print(f"Unknown / fallback: {unknown_fallback}")

    # Restoration products breakdown
    restoration_changes = [ch for ch in changes_to_apply if ch[3] == "Техника под восстановление"]
    print(f"\n--- Restoration Products Breakdown ({len(restoration_changes)} items) ---")
    for pid, new_cat_id, old_cat_name, new_cat_name, reason in restoration_changes:
        print(f"  ID={pid:3d} | old: {old_cat_name} -> new: {new_cat_name} | reason: {reason}")

    if is_apply:
        print("\nApplying changes to local canonical DB...")
        applied_count = 0
        from app.database import SessionLocal
        from app import models
        from app.routers.customers import log_audit
        from app.routers.products import log_product_event

        db = SessionLocal()
        try:
            for pid, new_cat_id, old_cat_name, new_cat_name, reason in changes_to_apply:
                db_prod = db.query(models.Product).filter(models.Product.id == pid).first()
                if not db_prod:
                    continue
                old_val = {"category_id": db_prod.category_id}
                new_val = {"category_id": new_cat_id}
                db_prod.category_id = new_cat_id
                db.flush()

                # Audit logging
                log_audit(db, "product", pid, "update", old_value=old_val, new_value=new_val)
                log_product_event(
                    db,
                    product_id=pid,
                    event_type="update",
                    old_value=old_val,
                    new_value=new_val,
                    comment=f"Category backfill: {old_cat_name} -> {new_cat_name} ({reason})"
                )
                applied_count += 1

            db.commit()
            print(f"Successfully applied and logged {applied_count} category updates.")
        except Exception as e:
            db.rollback()
            print(f"Error during apply: {e}")
            raise
        finally:
            db.close()

        # Database health check
        print("\nVerifying DB health...")
        qc = conn.cursor().execute("PRAGMA quick_check").fetchone()[0]
        ic = conn.cursor().execute("PRAGMA integrity_check").fetchone()[0]
        fk = conn.cursor().execute("PRAGMA foreign_key_check").fetchall()
        print(f"PRAGMA quick_check: {qc}")
        print(f"PRAGMA integrity_check: {ic}")
        print(f"PRAGMA foreign_key_check: {fk}")
        assert qc == "ok"
        assert ic == "ok"
        assert len(fk) == 0
        print("DB verification: ALL CLEAN!")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill product categories")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Perform dry run without modifying database")
    group.add_argument("--apply", action="store_true", help="Apply category changes to local database")
    args = parser.parse_args()

    mode = "--apply" if args.apply else "--dry-run"
    run_backfill(mode)

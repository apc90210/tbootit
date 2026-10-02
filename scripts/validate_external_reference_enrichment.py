#!/usr/bin/env python3
"""
Validator for External Reference Enrichment Packages (WEB-07C).
Strictly validates field-level provenance, Tier A/B source legitimacy,
exclusion of forbidden instance-level attributes, and absence of silent conflict merges.
"""

import sys
import os
import json
import re
import argparse
from typing import Dict, Any, List, Tuple, Set

# Allowed device types
ALLOWED_DEVICE_TYPES = {
    "printer", "mfu", "monitor", "laptop", "computer",
    "component", "network", "kiosk", "terminal", "ups", "projector"
}

# Allowed decisions
ALLOWED_DECISIONS = {
    "verified_apply", "identity_only", "needs_review", "rejected"
}

# Allowed source types (Tier A / B manufacturer origin)
ALLOWED_SOURCE_TYPES = {
    "official_datasheet",
    "official_support_page",
    "official_manual",
    "official_product_page",
    "official_regional_page",
    "vendor_repo"
}

# Forbidden instance-level fields (NEVER allowed in reference catalog models)
FORBIDDEN_INSTANCE_FIELDS = {
    "price", "sale_price", "purchase_price", "min_price", "market_price",
    "quantity", "reserved_quantity", "stock",
    "serial", "serial_number", "barcode", "sku",
    "condition", "avito_condition", "defects",
    "photos", "photo_url", "image", "images",
    "storage_location", "status", "notes", "notes_admin",
    "buyer_phone", "seller_phone", "contact_name", "address",
    "created_at", "updated_at", "id", "product_id"
}

# Forbidden domain fragments (marketplaces, forums, aggregators, SEO scrapers)
FORBIDDEN_DOMAIN_FRAGMENTS = [
    "avito.ru", "ebay.com", "amazon.com", "aliexpress.com", "market.yandex.ru",
    "ozon.ru", "wildberries.ru", "forum", "reddit.com", "quora.com",
    "otzovik.com", "irecommend.ru", "wikipedia.org"
]

STABLE_KEY_REGEX = re.compile(r"^[a-z0-9_\-]+(\|[a-z0-9_\-]+)+$")


class ValidationIssue:
    def __init__(self, severity: str, stable_key: str, message: str):
        self.severity = severity  # "ERROR" or "WARNING"
        self.stable_key = stable_key
        self.message = message

    def __str__(self) -> str:
        return f"[{self.severity}] [{self.stable_key}] {self.message}"


def validate_enrichment_package(data: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue], Dict[str, Any]]:
    issues: List[ValidationIssue] = []
    stats: Dict[str, Any] = {
        "total_models": 0,
        "verified_apply_count": 0,
        "needs_review_count": 0,
        "rejected_count": 0,
        "identity_only_count": 0,
        "total_fields": 0,
        "total_sources": 0,
        "unique_publishers": set(),
    }

    if not isinstance(data, dict):
        issues.append(ValidationIssue("ERROR", "ROOT", "Payload must be a JSON object"))
        return False, issues, stats

    batch_id = data.get("batch_id")
    if not batch_id or not isinstance(batch_id, str):
        issues.append(ValidationIssue("ERROR", "ROOT", "Missing or invalid 'batch_id'"))

    models_list = data.get("models")
    if not isinstance(models_list, list) or len(models_list) == 0:
        issues.append(ValidationIssue("ERROR", "ROOT", "'models' must be a non-empty list"))
        return False, issues, stats

    seen_keys: Set[str] = set()

    for idx, model in enumerate(models_list):
        if not isinstance(model, dict):
            issues.append(ValidationIssue("ERROR", f"item_{idx}", "Model entry must be a dictionary"))
            continue

        stable_key = model.get("stable_key")
        if not stable_key or not isinstance(stable_key, str) or not STABLE_KEY_REGEX.match(stable_key):
            issues.append(ValidationIssue("ERROR", str(stable_key or f"item_{idx}"),
                                          f"Invalid or malformed stable_key: '{stable_key}'"))
            continue

        if stable_key in seen_keys:
            issues.append(ValidationIssue("ERROR", stable_key, "Duplicate stable_key found in batch"))
        seen_keys.add(stable_key)
        stats["total_models"] += 1

        canonical_name = model.get("canonical_name")
        if not canonical_name or not isinstance(canonical_name, str) or not canonical_name.strip():
            issues.append(ValidationIssue("ERROR", stable_key, "Missing or empty canonical_name"))

        device_type = model.get("device_type")
        if device_type not in ALLOWED_DEVICE_TYPES:
            issues.append(ValidationIssue("ERROR", stable_key,
                                          f"Invalid device_type: '{device_type}'. Allowed: {sorted(ALLOWED_DEVICE_TYPES)}"))

        decision = model.get("decision", "verified_apply")
        if decision not in ALLOWED_DECISIONS:
            issues.append(ValidationIssue("ERROR", stable_key,
                                          f"Invalid decision: '{decision}'. Allowed: {sorted(ALLOWED_DECISIONS)}"))
        if decision == "verified_apply":
            stats["verified_apply_count"] += 1
        elif decision == "needs_review":
            stats["needs_review_count"] += 1
        elif decision == "rejected":
            stats["rejected_count"] += 1
        elif decision == "identity_only":
            stats["identity_only_count"] += 1

        # Sources validation
        sources = model.get("sources", [])
        if not isinstance(sources, list) or len(sources) == 0:
            issues.append(ValidationIssue("ERROR", stable_key, "Sources list must be non-empty"))
            declared_source_ids = set()
        else:
            declared_source_ids = set()
            for s_idx, src in enumerate(sources):
                if not isinstance(src, dict):
                    issues.append(ValidationIssue("ERROR", stable_key, f"Source #{s_idx} is not a dict"))
                    continue
                sid = src.get("source_id")
                if not sid or not isinstance(sid, str):
                    issues.append(ValidationIssue("ERROR", stable_key, f"Source #{s_idx} missing 'source_id'"))
                    continue
                if sid in declared_source_ids:
                    issues.append(ValidationIssue("ERROR", stable_key, f"Duplicate source_id '{sid}' in sources"))
                declared_source_ids.add(sid)
                stats["total_sources"] += 1

                url = src.get("url", "")
                if not url or not (url.startswith("http://") or url.startswith("https://")):
                    issues.append(ValidationIssue("ERROR", stable_key, f"Source '{sid}' has invalid URL: '{url}'"))

                # Check forbidden domains
                url_lower = url.lower()
                for bad_frag in FORBIDDEN_DOMAIN_FRAGMENTS:
                    if bad_frag in url_lower:
                        issues.append(ValidationIssue("ERROR", stable_key,
                                                      f"Source '{sid}' uses forbidden domain/fragment: '{bad_frag}' in '{url}'"))

                publisher = src.get("publisher", "")
                if not publisher or not str(publisher).strip():
                    issues.append(ValidationIssue("ERROR", stable_key, f"Source '{sid}' missing 'publisher'"))
                else:
                    stats["unique_publishers"].add(str(publisher).strip())

                stype = src.get("source_type")
                if stype not in ALLOWED_SOURCE_TYPES:
                    issues.append(ValidationIssue("ERROR", stable_key,
                                                  f"Source '{sid}' has invalid source_type '{stype}'. Allowed: {sorted(ALLOWED_SOURCE_TYPES)}"))

        # Fields & Provenance validation
        fields = model.get("fields", {})
        if not isinstance(fields, dict):
            issues.append(ValidationIssue("ERROR", stable_key, "'fields' must be a dictionary"))
            fields = {}

        if decision == "verified_apply" and len(fields) == 0:
            issues.append(ValidationIssue("ERROR", stable_key,
                                          "Decision is 'verified_apply' but 'fields' map is empty"))

        for field_name, f_info in fields.items():
            stats["total_fields"] += 1
            # Check forbidden instance fields
            f_norm = field_name.lower().replace("-", "_").replace(" ", "_")
            if f_norm in FORBIDDEN_INSTANCE_FIELDS:
                issues.append(ValidationIssue("ERROR", stable_key,
                                              f"Forbidden instance-level field in reference model: '{field_name}'"))

            if not isinstance(f_info, dict):
                issues.append(ValidationIssue("ERROR", stable_key, f"Field '{field_name}' must be an object"))
                continue

            val = f_info.get("value")
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(ValidationIssue("ERROR", stable_key, f"Field '{field_name}' has null or empty value"))

            src_ids = f_info.get("source_ids", [])
            if not isinstance(src_ids, list) or len(src_ids) == 0:
                issues.append(ValidationIssue("ERROR", stable_key,
                                              f"Field '{field_name}' has no source provenance (missing source_ids)"))
            else:
                for sid in src_ids:
                    if sid not in declared_source_ids:
                        issues.append(ValidationIssue("ERROR", stable_key,
                                                      f"Field '{field_name}' references undeclared source_id '{sid}'"))

        # Check conflicts
        conflicts = model.get("conflicts", [])
        if conflicts:
            if not isinstance(conflicts, list):
                issues.append(ValidationIssue("ERROR", stable_key, "'conflicts' must be a list"))
            else:
                for c in conflicts:
                    c_field = c.get("field")
                    if decision == "verified_apply" and c_field in fields:
                        issues.append(ValidationIssue("ERROR", stable_key,
                                                      f"Field '{c_field}' is marked as unresolved conflict but included in verified_apply fields!"))

        # Specifications dictionary validation
        specs = model.get("specifications", {})
        if not isinstance(specs, dict):
            issues.append(ValidationIssue("ERROR", stable_key, "'specifications' must be a dictionary"))
        else:
            for spec_k, spec_v in specs.items():
                k_norm = spec_k.lower().replace("-", "_").replace(" ", "_")
                if k_norm in FORBIDDEN_INSTANCE_FIELDS:
                    issues.append(ValidationIssue("ERROR", stable_key,
                                                  f"Forbidden instance attribute in specifications: '{spec_k}'"))

    stats["unique_publishers"] = list(stats["unique_publishers"])
    error_count = sum(1 for i in issues if i.severity == "ERROR")
    is_valid = (error_count == 0)
    return is_valid, issues, stats


def main():
    parser = argparse.ArgumentParser(description="Validate external verified reference enrichment package.")
    parser.add_argument("package_path", help="Path to EXTERNAL_ENRICHMENT_BATCH_*.json")
    args = parser.parse_args()

    if not os.path.exists(args.package_path):
        print(f"Error: file not found: {args.package_path}")
        sys.exit(1)

    with open(args.package_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"JSON parse error: {e}")
            sys.exit(1)

    is_valid, issues, stats = validate_enrichment_package(data)

    print("=================================================================")
    print(f"ENRICHMENT PACKAGE VALIDATION REPORT: {os.path.basename(args.package_path)}")
    print("=================================================================")
    print(f"Models total:           {stats.get('total_models', 0)}")
    print(f"  - verified_apply:     {stats.get('verified_apply_count', 0)}")
    print(f"  - needs_review:       {stats.get('needs_review_count', 0)}")
    print(f"  - rejected:           {stats.get('rejected_count', 0)}")
    print(f"  - identity_only:      {stats.get('identity_only_count', 0)}")
    print(f"Total verified fields:  {stats.get('total_fields', 0)}")
    print(f"Total source entries:   {stats.get('total_sources', 0)}")
    print(f"Publishers verified:    {', '.join(stats.get('unique_publishers', []))}")
    print("-----------------------------------------------------------------")

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]

    print(f"Validation status:      {'PASS (ALL CHECKS GREEN)' if is_valid else 'FAIL'}")
    print(f"Errors:                 {len(errors)}")
    print(f"Warnings:               {len(warnings)}")
    print("-----------------------------------------------------------------")

    if issues:
        for iss in issues:
            print(str(iss))

    if not is_valid:
        sys.exit(1)
    else:
        print("[OK] Package is fully compliant with WEB-07C specification requirements.")
        sys.exit(0)


if __name__ == "__main__":
    main()

import subprocess
import sys

tests_to_run = [
    ("core", ["python", "-m", "pytest", "tests/test_product_safety_and_draft.py", "tests/test_products.py", "tests/test_products_search_filters.py", "-p", "no:warnings"]),
    ("admin-shell", ["python", "-m", "pytest", "tests/test_seller_rbac_and_data_safety.py", "tests/test_certificate_auth.py", "tests/test_unified_top_navigation_bar.py", "tests/test_extension_download_manifest_valid.py", "tests/test_extension_download_is_current_version.py", "tests/test_owner_operations_rbac.py", "-p", "no:warnings"]),
    (".", ["python", "-m", "pytest", "tests/test_production_data_guard.py", "tests/test_stage08b_r1_production_baseline.py", "tests/test_hard_delete_audit.py", "tests/test_stage08d_r1r3_pairing_lifecycle.py", "tests/test_owner_operations_rbac.py", "tests/test_owner_operations_environment_guard.py", "tests/test_owner_operations_schema_guard.py", "tests/test_owner_operations_direction_guard.py", "tests/test_owner_operations_preflight.py", "tests/test_owner_operations_checkpoint.py", "tests/test_owner_operations_rollback.py", "tests/test_owner_operations_rollback_schema_guard.py", "-p", "no:warnings"])
]

all_ok = True
for cwd, cmd in tests_to_run:
    cmd_str = " ".join(cmd)
    print(f"=== Running in {cwd}: {cmd_str} ===")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    summary_lines = [l for l in res.stdout.splitlines() if "passed" in l or "failed" in l or "error" in l]
    for l in summary_lines:
        print(f"   {l}")
    if res.returncode != 0:
        print(f"FAILED in {cwd}! Tail:\n{res.stdout[-600:]}\nSTDERR:\n{res.stderr}")
        all_ok = False

if not all_ok:
    print("\nSOME TESTS FAILED!")
    sys.exit(1)

print("\nALL TARGETED SUITES PASSED! FAILED = 0")

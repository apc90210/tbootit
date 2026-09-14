import sys
import os
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from local_ops_runner import (
    check_vds_health_preflight,
    create_vds_release_checkpoint,
    DEFAULT_SSH_KEY,
    DEFAULT_VDS_HOST,
)

def main():
    print("=== Step 1: Preflight VDS Health ===")
    status, probe_data, err = check_vds_health_preflight(DEFAULT_SSH_KEY, DEFAULT_VDS_HOST)
    print(f"Preflight status: {status}")
    if status != "HEALTHY":
        print(f"ERROR: {err}")
        sys.exit(1)

    previous_head = probe_data.get("git_head", "e21dba6404f14314863213cb40ba945ea427a467")
    target_head = "46fbed130ca838c2e1aeaa4897f6cc68c86337b8"

    print(f"Previous VDS HEAD: {previous_head}")
    print(f"Target candidate HEAD: {target_head}")

    print("=== Step 2: Create Release Checkpoint on VDS & Local ===")
    manifest = create_vds_release_checkpoint(
        job_id="stage10b_prod_deploy",
        ssh_key=DEFAULT_SSH_KEY,
        vds_host=DEFAULT_VDS_HOST,
        previous_head=previous_head,
        target_head=target_head,
        preflight_data=probe_data,
    )

    print("=== Checkpoint Created Successfully! ===")
    print(json.dumps(manifest, indent=2))

    # Save to json file
    out_file = Path(__file__).resolve().parent / "vds_checkpoint_10b.json"
    out_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved manifest to {out_file}")

if __name__ == "__main__":
    main()

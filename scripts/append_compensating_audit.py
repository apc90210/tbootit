import sqlite3
import json
from datetime import datetime

CURRENT_DB_PATH = '/srv/technoreboot/data/db/technoreboot.db'

conn = sqlite3.connect(CURRENT_DB_PATH)
conn.row_factory = sqlite3.Row

# Check if compensating event already exists
existing = conn.execute("SELECT * FROM audit_log WHERE entity_type='repair_order' AND entity_id=1 AND action='production_test_restore'").fetchone()
if existing:
    print("Compensating audit event already exists:", dict(existing))
else:
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    old_val = json.dumps({
        "deleted_by_test": True,
        "delete_audit_id": 1745,
        "delete_timestamp": "2026-09-17 08:22:24"
    })
    new_val = json.dumps({
        "restored_from_backup": "TECHNOREBOOT_BACKUP_2026-09-17_110805.zip",
        "repair_id": 1,
        "number": "R-20260914-0001",
        "status": "ready",
        "sale_id": None
    })
    comment = "Real repair deletion was performed during Stage11D-R1 verification and restored from pre-test backup TECHNOREBOOT_BACKUP_2026-09-17_110805.zip; sale_id set to NULL as linked sale #3 was permanently deleted by owner."
    
    conn.execute(
        "INSERT INTO audit_log (entity_type, entity_id, action, old_value, new_value, comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("repair_order", 1, "production_test_restore", old_val, new_val, comment, now_str)
    )
    conn.commit()
    print(f"Appended compensating audit event at {now_str}")

# Verify
last_entry = conn.execute("SELECT * FROM audit_log WHERE entity_type='repair_order' AND entity_id=1 ORDER BY id DESC LIMIT 1").fetchone()
print("Latest audit log entry for repair_order #1:", dict(last_entry))

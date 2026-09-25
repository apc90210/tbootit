#!/usr/bin/env python3
"""
Stage01A R3 Migration Script — Add/Update Mobile Access Tables (Additive & Non-destructive)

R3 AUDIT & MIGRATION RULES:
  - Additive only: CREATE TABLE IF NOT EXISTS.
  - No destructive schema operations: no DROP TABLE, no SQLite table rebuild.
  - Legacy column `credential_token_hash` in `mobile_credentials` is retained as a
    nullable column so that existing code/models remain forward and backward compatible.
    If missing, it is added via non-destructive `ALTER TABLE ... ADD COLUMN`.
  - Adds `mobile_challenges` table with indexes for one-time nonce storage.
  - Non-destructive to all business and audit data.
  - Verifies PRAGMA foreign_key_check and PRAGMA quick_check.
"""

import sqlite3
import sys
from pathlib import Path

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS mobile_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_identifier TEXT UNIQUE NOT NULL,
    display_name TEXT,
    parent_certificate_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mobile_devices_parent_cert ON mobile_devices(parent_certificate_id);
CREATE INDEX IF NOT EXISTS idx_mobile_devices_identifier ON mobile_devices(device_identifier);
CREATE INDEX IF NOT EXISTS idx_mobile_devices_status ON mobile_devices(status);

CREATE TABLE IF NOT EXISTS mobile_pairing_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    parent_certificate_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    used_at TIMESTAMP,
    device_name TEXT
);

CREATE INDEX IF NOT EXISTS idx_mobile_pairing_codes_code ON mobile_pairing_codes(code);
CREATE INDEX IF NOT EXISTS idx_mobile_pairing_codes_parent ON mobile_pairing_codes(parent_certificate_id);

CREATE TABLE IF NOT EXISTS mobile_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nonce_hex TEXT UNIQUE NOT NULL,
    credential_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mobile_challenges_nonce ON mobile_challenges(nonce_hex);
CREATE INDEX IF NOT EXISTS idx_mobile_challenges_cred ON mobile_challenges(credential_id);

CREATE TABLE IF NOT EXISTS mobile_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mobile_device_id INTEGER NOT NULL,
    credential_id TEXT UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    credential_token_hash TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (mobile_device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mobile_credentials_device ON mobile_credentials(mobile_device_id);
CREATE INDEX IF NOT EXISTS idx_mobile_credentials_cred_id ON mobile_credentials(credential_id);
CREATE INDEX IF NOT EXISTS idx_mobile_credentials_status ON mobile_credentials(status);
"""


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def _ensure_additive_columns(conn: sqlite3.Connection):
    """
    R3 Additive check: ensures mobile_credentials has legacy nullable credential_token_hash
    without rebuilding the table or dropping data.
    """
    if not _has_column(conn, "mobile_credentials", "credential_token_hash"):
        conn.execute("ALTER TABLE mobile_credentials ADD COLUMN credential_token_hash TEXT;")
        conn.commit()


def apply_migration(db_path: Path) -> bool:
    if not db_path.exists():
        print(f"Skipping non-existent db: {db_path}")
        return True

    print(f"Applying Stage01A R3 additive migration to: {db_path}...")
    conn = sqlite3.connect(str(db_path))
    try:
        # 1. Create tables & indexes if not present
        conn.executescript(SCHEMA_SQL)

        # 2. Non-destructive column check
        _ensure_additive_columns(conn)
        conn.commit()

        # 3. Integrity checks
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_key_check;")
        fk_violations = cur.fetchall()
        if fk_violations:
            print(f"ERROR: foreign_key_check failed on {db_path}: {fk_violations}")
            return False

        cur.execute("PRAGMA quick_check;")
        qc = cur.fetchall()
        if qc != [("ok",)]:
            print(f"ERROR: quick_check failed on {db_path}: {qc}")
            return False

        print(f"PASS: Migration applied cleanly to {db_path}. FK check: clean, Quick check: ok.")
        return True
    finally:
        conn.close()


def main():
    root = Path(__file__).resolve().parent.parent
    targets = [
        root / "technoreboot.db",
        root / "data" / "db" / "technoreboot.db",
        root / "core" / "technoreboot.db",
    ]

    all_ok = True
    for db in targets:
        if db.exists():
            ok = apply_migration(db)
            if not ok:
                all_ok = False

    if not all_ok:
        sys.exit(1)
    print("All Stage01A R3 migrations completed successfully.")


if __name__ == "__main__":
    main()

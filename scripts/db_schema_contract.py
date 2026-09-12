#!/usr/bin/env python3
"""
Technoreboot — DB Schema Contract and Compatibility Guard
Stage 08D-R1R5: OWNER Operations & Schema Guard

Responsibilities:
1. Extract canonical schema contract from SQLAlchemy source models.
2. Extract runtime schema contract from any SQLite database (Local or VDS).
3. Compute deterministic schema contract SHA256.
4. Compare expected contract against live VDS/Local database with detailed structural diffs.
5. Provide strict binary safety decision: SAFE or BLOCKED.
"""

import os
import sys
import json
import hashlib
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "core"
DEFAULT_CONTRACT_PATH = REPO_ROOT / "deploy" / "production" / "schema_contract.json"
DEFAULT_COMPATIBILITY_PATH = REPO_ROOT / "deploy" / "production" / "deployment_compatibility.json"


def normalize_type_name(col_type: str) -> str:
    """Normalize SQLite column type to standard uppercase category."""
    if not col_type:
        return "TEXT"
    t = col_type.strip().upper()
    if any(k in t for k in ["INT", "SERIAL", "ROWID"]):
        return "INTEGER"
    if any(k in t for k in ["CHAR", "CLOB", "TEXT", "STRING"]):
        return "TEXT"
    if any(k in t for k in ["BLOB", "BINARY"]):
        return "BLOB"
    if any(k in t for k in ["REAL", "FLOA", "DOUB", "NUMERIC", "DECIMAL"]):
        return "FLOAT"
    if any(k in t for k in ["BOOL"]):
        return "BOOLEAN"
    if any(k in t for k in ["TIME", "DATE"]):
        return "DATETIME"
    return t


def extract_contract_from_sqlite_conn(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Inspect an open SQLite connection and extract normalized schema dictionary."""
    cur = conn.cursor()
    
    # Retrieve all tables
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    table_names = [r[0] for r in cur.fetchall()]
    
    tables_contract = {}
    
    for tbl in sorted(table_names):
        # 1. Columns
        cur.execute(f"PRAGMA table_info('{tbl}');")
        col_rows = cur.fetchall()
        # col_rows: (cid, name, type, notnull, dflt_value, pk)
        columns = []
        for r in col_rows:
            cid, name, col_type, notnull, dflt_val, pk = r
            columns.append({
                "name": name,
                "type": normalize_type_name(col_type),
                "nullable": bool(notnull == 0),
                "primary_key": int(pk),
                "default": str(dflt_val) if dflt_val is not None else None,
            })
        columns.sort(key=lambda c: c["name"])
        
        # 2. Foreign keys
        cur.execute(f"PRAGMA foreign_key_list('{tbl}');")
        fk_rows = cur.fetchall()
        # fk_rows: (id, seq, table, from, to, on_update, on_delete, match)
        fks = []
        for r in fk_rows:
            fks.append({
                "from_column": r[3],
                "to_table": r[2],
                "to_column": r[4],
            })
        fks.sort(key=lambda k: (k["from_column"], k["to_table"], k["to_column"] or ""))
        
        # 3. Indexes
        cur.execute(f"PRAGMA index_list('{tbl}');")
        idx_rows = cur.fetchall()
        # idx_rows: (seq, name, unique, origin, partial)
        indexes = []
        for ir in idx_rows:
            idx_name = ir[1]
            is_unique = bool(ir[2])
            cur.execute(f"PRAGMA index_info('{idx_name}');")
            info_rows = cur.fetchall()
            idx_cols = [c[2] for c in info_rows]
            indexes.append({
                "name": idx_name,
                "unique": is_unique,
                "columns": idx_cols,
            })
        indexes.sort(key=lambda idx: idx["name"])
        
        tables_contract[tbl] = {
            "columns": columns,
            "foreign_keys": fks,
            "indexes": indexes,
        }
        
    return {
        "format_version": 1,
        "tables": tables_contract,
    }


def extract_contract_from_db_path(db_path: Path) -> Dict[str, Any]:
    """Extract schema contract from physical SQLite database file."""
    if not db_path.is_file():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return extract_contract_from_sqlite_conn(conn)
    finally:
        conn.close()


def extract_contract_from_source_models() -> Dict[str, Any]:
    """Generate schema contract from SQLAlchemy models in core/app/models.py."""
    saved_modules = {}
    for key in list(sys.modules.keys()):
        if key == "app" or key.startswith("app."):
            saved_modules[key] = sys.modules.pop(key)

    saved_sys_path = list(sys.path)
    if str(CORE_DIR) in sys.path:
        sys.path.remove(str(CORE_DIR))
    sys.path.insert(0, str(CORE_DIR))

    try:
        import app.database
        import app.models
        Base = app.database.Base
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        raw_conn = engine.raw_connection()
        try:
            sqlite_conn = getattr(raw_conn, "dbapi_connection", getattr(raw_conn, "driver_connection", raw_conn))
            contract = extract_contract_from_sqlite_conn(sqlite_conn)
        finally:
            raw_conn.close()
            engine.dispose()
    finally:
        sys.path = saved_sys_path
        for key in list(sys.modules.keys()):
            if key == "app" or key.startswith("app."):
                sys.modules.pop(key, None)
        sys.modules.update(saved_modules)

    return contract


def compute_contract_sha256(contract: Dict[str, Any]) -> str:
    """Compute deterministic SHA256 of schema contract."""
    serialized = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compare_schema_contracts(
    expected_contract: Dict[str, Any],
    live_contract: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Compare expected contract against live contract.
    Returns: (is_safe, diff_messages)
    Conservative rule: ANY structural difference blocks normal UPDATE.
    """
    diffs = []
    
    exp_tables = expected_contract.get("tables", {})
    live_tables = live_contract.get("tables", {})
    
    # 1. Missing or extra tables
    missing_tables = sorted(set(exp_tables.keys()) - set(live_tables.keys()))
    extra_tables = sorted(set(live_tables.keys()) - set(exp_tables.keys()))
    
    for t in missing_tables:
        diffs.append(f"NEW TABLE IN CODE (missing in live DB): {t}")
    for t in extra_tables:
        diffs.append(f"EXTRA TABLE IN LIVE DB (not in code): {t}")
        
    # 2. Table-level structural comparisons
    common_tables = sorted(set(exp_tables.keys()) & set(live_tables.keys()))
    for t in common_tables:
        exp_cols = {c["name"]: c for c in exp_tables[t]["columns"]}
        live_cols = {c["name"]: c for c in live_tables[t]["columns"]}
        
        missing_cols = sorted(set(exp_cols.keys()) - set(live_cols.keys()))
        extra_cols = sorted(set(live_cols.keys()) - set(exp_cols.keys()))
        
        for c in missing_cols:
            diffs.append(f"TABLE '{t}': NEW COLUMN IN CODE '{c}' ({exp_cols[c]['type']})")
        for c in extra_cols:
            diffs.append(f"TABLE '{t}': EXTRA COLUMN IN LIVE DB '{c}' ({live_cols[c]['type']})")
            
        common_cols = sorted(set(exp_cols.keys()) & set(live_cols.keys()))
        for c in common_cols:
            ec = exp_cols[c]
            lc = live_cols[c]
            
            # Type mismatch
            if ec["type"] != lc["type"]:
                diffs.append(
                    f"TABLE '{t}', COLUMN '{c}': Type mismatch (Code: {ec['type']}, Live: {lc['type']})"
                )
            # Nullable mismatch
            if ec["nullable"] != lc["nullable"]:
                diffs.append(
                    f"TABLE '{t}', COLUMN '{c}': Nullable mismatch (Code: {ec['nullable']}, Live: {lc['nullable']})"
                )
            # Primary key mismatch
            if ec["primary_key"] != lc["primary_key"]:
                diffs.append(
                    f"TABLE '{t}', COLUMN '{c}': PK mismatch (Code: {ec['primary_key']}, Live: {lc['primary_key']})"
                )
                
    is_safe = (len(diffs) == 0)
    return is_safe, diffs


def check_deployment_compatibility_flag(
    compat_path: Path = DEFAULT_COMPATIBILITY_PATH
) -> Tuple[bool, str]:
    """Check tracked deployment_compatibility.json flag."""
    if not compat_path.is_file():
        return False, "Missing deployment_compatibility.json file"
    try:
        data = json.loads(compat_path.read_text(encoding="utf-8"))
        if data.get("requires_manual_migration") is True:
            return False, f"Manual migration required: {data.get('reason', 'Unspecified reason')}"
        if data.get("database_change") is True:
            return False, f"Database schema change flagged: {data.get('reason', 'Unspecified reason')}"
        return True, "Compatibility flag is SAFE (no manual migration required)"
    except Exception as e:
        return False, f"Failed to parse deployment_compatibility.json: {e}"


def check_live_vds_schema(ssh_key: str, vds_host: str) -> Dict[str, Any]:
    """Query live schema contract directly from production VDS via SSH (pure standard library)."""
    import subprocess
    remote_script = """
import sqlite3, json

conn = sqlite3.connect('file:/srv/technoreboot/data/db/technoreboot.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
table_names = [r[0] for r in cur.fetchall()]
tables = {}
for tbl in table_names:
    cur.execute(f"PRAGMA table_info('{tbl}');")
    cols = []
    for r in cur.fetchall():
        cid, name, col_type, notnull, dflt_val, pk = r
        t = col_type.upper().strip() if col_type else "TEXT"
        if t.startswith("VARCHAR") or t.startswith("NVARCHAR") or t.startswith("CHAR"):
            t = "TEXT"
        elif t.startswith("TIMESTAMP"):
            t = "DATETIME"
        elif t.startswith("NUMERIC") or t.startswith("DECIMAL") or t.startswith("REAL") or t.startswith("DOUBLE"):
            t = "FLOAT"
        elif t.startswith("INT") or t.startswith("TINYINT") or t.startswith("SMALLINT") or t.startswith("BIGINT"):
            t = "INTEGER"
        elif t.startswith("BOOL"):
            t = "BOOLEAN"
        cols.append({
            "name": name,
            "type": t,
            "nullable": bool(notnull == 0),
            "primary_key": int(pk),
            "default": str(dflt_val) if dflt_val is not None else None,
        })
    cols.sort(key=lambda c: c["name"])
    
    cur.execute(f"PRAGMA foreign_key_list('{tbl}');")
    fks = []
    for r in cur.fetchall():
        id_, seq, target_table, from_col, to_col, on_update, on_delete, match = r
        fks.append({
            "from_column": from_col,
            "target_table": target_table,
            "target_column": to_col,
            "on_delete": (on_delete or "NO ACTION").upper(),
            "on_update": (on_update or "NO ACTION").upper(),
        })
    fks.sort(key=lambda x: (x["from_column"], x["target_table"]))
    
    cur.execute(f"PRAGMA index_list('{tbl}');")
    indexes = []
    for r in cur.fetchall():
        seq, name, unique, origin, partial = r
        if origin == "pk": continue
        cur.execute(f"PRAGMA index_info('{name}');")
        idx_cols = [c[2] for c in sorted(cur.fetchall(), key=lambda x: x[0])]
        indexes.append({
            "name": name,
            "unique": bool(unique),
            "columns": idx_cols,
        })
    indexes.sort(key=lambda x: x["name"])
    
    tables[tbl] = {
        "columns": cols,
        "foreign_keys": fks,
        "indexes": indexes,
    }
conn.close()
print(json.dumps({"format_version": 1, "tables": tables}))
"""
    cmd = ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 -"]
    res = subprocess.run(cmd, input=remote_script, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to query VDS schema: {res.stderr.strip() or res.stdout.strip()}")
    return json.loads(res.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Technoreboot DB Schema Contract Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    gen_p = subparsers.add_parser("generate", help="Generate schema contract from source models")
    gen_p.add_argument("--output", default=str(DEFAULT_CONTRACT_PATH), help="Output contract path")
    
    verify_p = subparsers.add_parser("verify", help="Verify source models match tracked contract")
    verify_p.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH), help="Tracked contract path")
    
    comp_p = subparsers.add_parser("compare", help="Compare database file against contract")
    comp_p.add_argument("--db", required=True, help="Path to SQLite DB")
    comp_p.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH), help="Contract path")
    
    vds_p = subparsers.add_parser("check-vds", help="Check live VDS database schema against contract")
    vds_p.add_argument("--key", default="C:/Users/Apc/.ssh/id_ed25519", help="SSH private key path")
    vds_p.add_argument("--vds", default="root@144.31.50.134", help="VDS host")
    vds_p.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH), help="Contract path")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        contract = extract_contract_from_source_models()
        h = compute_contract_sha256(contract)
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        print(f"Generated contract at {out_p}")
        print(f"SHA256: {h}")
        print(f"Tables: {len(contract.get('tables', {}))}")
        
    elif args.command == "verify":
        code_contract = extract_contract_from_source_models()
        c_path = Path(args.contract)
        if not c_path.is_file():
            print(f"ERROR: Contract file not found: {c_path}", file=sys.stderr)
            sys.exit(1)
        tracked_contract = json.loads(c_path.read_text(encoding="utf-8"))
        is_safe, diffs = compare_schema_contracts(code_contract, tracked_contract)
        if not is_safe:
            print("ERROR: Code models differ from tracked contract!", file=sys.stderr)
            for d in diffs:
                print(f"  - {d}", file=sys.stderr)
            sys.exit(1)
        print("Contract verification PASSED: Code models match tracked contract exactly.")
        
    elif args.command == "compare":
        db_p = Path(args.db)
        db_contract = extract_contract_from_db_path(db_p)
        c_path = Path(args.contract)
        tracked_contract = json.loads(c_path.read_text(encoding="utf-8"))
        is_safe, diffs = compare_schema_contracts(tracked_contract, db_contract)
        if not is_safe:
            print(f"SCHEMA MISMATCH in {db_p}:", file=sys.stderr)
            for d in diffs:
                print(f"  - {d}", file=sys.stderr)
            sys.exit(1)
        print(f"Database {db_p} matches contract: SAFE")
        
    elif args.command == "check-vds":
        vds_contract = check_live_vds_schema(args.key, args.vds)
        c_path = Path(args.contract)
        tracked_contract = json.loads(c_path.read_text(encoding="utf-8"))
        is_safe, diffs = compare_schema_contracts(tracked_contract, vds_contract)
        if not is_safe:
            print(f"SCHEMA MISMATCH between VDS and tracked contract:", file=sys.stderr)
            for d in diffs:
                print(f"  - {d}", file=sys.stderr)
            sys.exit(1)
        print("VDS live database matches tracked contract: SAFE")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

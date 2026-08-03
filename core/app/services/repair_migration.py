import sqlite3
import datetime
import os

def run_repair_additive_migration(db_path: str):
    """
    Idempotent, additive migration for RepairOrder and RepairStatusHistory.
    Applies schema additions (ALTER TABLE ADD COLUMN) without dropping any existing tables or data.
    """
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. Ensure repair_orders table exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS repair_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE,
            status TEXT DEFAULT 'received',
            customer_id INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            customer_email TEXT,
            device_type TEXT,
            brand TEXT,
            model TEXT,
            serial_number TEXT,
            reported_issue TEXT,
            completeness TEXT,
            appearance TEXT,
            customer_comment TEXT,
            internal_note TEXT,
            access_code_provided INTEGER DEFAULT 0,
            assigned_to TEXT,
            priority TEXT DEFAULT 'normal',
            accepted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            closed_at DATETIME,
            issued_at DATETIME,
            canceled_at DATETIME
        )
        """)

        # 2. Check existing columns in repair_orders and add missing ones
        cur.execute("PRAGMA table_info(repair_orders)")
        existing_cols = {row[1] for row in cur.fetchall()}

        new_columns = [
            ("number", "TEXT"),
            ("status", "TEXT DEFAULT 'received'"),
            ("customer_id", "INTEGER"),
            ("customer_name", "TEXT"),
            ("customer_phone", "TEXT"),
            ("customer_email", "TEXT"),
            ("device_type", "TEXT"),
            ("brand", "TEXT"),
            ("model", "TEXT"),
            ("serial_number", "TEXT"),
            ("reported_issue", "TEXT"),
            ("completeness", "TEXT"),
            ("appearance", "TEXT"),
            ("customer_comment", "TEXT"),
            ("internal_note", "TEXT"),
            ("access_code_provided", "INTEGER DEFAULT 0"),
            ("assigned_to", "TEXT"),
            ("priority", "TEXT DEFAULT 'normal'"),
            ("diagnostic_fee", "FLOAT DEFAULT 500.0"),
            ("accepted_at", "DATETIME"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
            ("closed_at", "DATETIME"),
            ("issued_at", "DATETIME"),
            ("canceled_at", "DATETIME")
        ]

        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE repair_orders ADD COLUMN {col_name} {col_type}")

        # 3. Create repair_status_history table if not exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS repair_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            comment TEXT,
            changed_by TEXT,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (repair_id) REFERENCES repair_orders (id)
        )
        """)

        # 4. Create Indexes
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_repair_orders_number ON repair_orders (number)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_orders_status ON repair_orders (status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_orders_phone ON repair_orders (customer_phone)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_orders_serial ON repair_orders (serial_number)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_history_repair_id ON repair_status_history (repair_id)")

        # Backfill diagnostic_fee for any existing rows where it is NULL
        cur.execute("UPDATE repair_orders SET diagnostic_fee = 500.0 WHERE diagnostic_fee IS NULL")

        # 5. Populate default values for legacy prototype records
        cur.execute("SELECT id, number, status, device_title, problem_description, customer_id FROM repair_orders")
        rows = cur.fetchall()
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.datetime.utcnow().strftime("%Y%m%d")

        cur.execute("SELECT number FROM repair_orders WHERE number IS NOT NULL")
        existing_numbers = {r[0] for r in cur.fetchall() if r[0]}

        counter = 1
        for row_id, num, status, dev_title, prob_desc, cust_id in rows:
            updates = {}
            if not num:
                candidate = f"R-{date_str}-{counter:04d}"
                while candidate in existing_numbers:
                    counter += 1
                    candidate = f"R-{date_str}-{counter:04d}"
                updates["number"] = candidate
                existing_numbers.add(candidate)
                counter += 1
            if not status or status == "new":
                updates["status"] = "received"
            
            # Populate customer info if missing
            cur.execute("SELECT name, phone, email FROM customers WHERE id = ?", (cust_id,)) if cust_id else None
            cust_row = cur.fetchone() if cust_id else None
            
            updates.setdefault("customer_name", cust_row[0] if cust_row else f"Клиент #{row_id}")
            updates.setdefault("customer_phone", cust_row[1] if cust_row else "+7 000 000-00-00")
            if cust_row and cust_row[2]:
                updates.setdefault("customer_email", cust_row[2])

            updates.setdefault("device_type", "Устройство")
            updates.setdefault("brand", dev_title or "—")
            updates.setdefault("reported_issue", prob_desc or "Заявка на ремонт")
            updates.setdefault("accepted_at", now_str)
            updates.setdefault("access_code_provided", 0)
            updates.setdefault("priority", "normal")
            updates.setdefault("diagnostic_fee", 500.0)

            # Check existing values in table before overriding
            cur.execute("SELECT customer_name, customer_phone, device_type, reported_issue FROM repair_orders WHERE id = ?", (row_id,))
            cur_vals = cur.fetchone()
            if cur_vals[0]: updates.pop("customer_name", None)
            if cur_vals[1]: updates.pop("customer_phone", None)
            if cur_vals[2]: updates.pop("device_type", None)
            if cur_vals[3]: updates.pop("reported_issue", None)

            if updates:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                params = list(updates.values()) + [row_id]
                cur.execute(f"UPDATE repair_orders SET {set_clause} WHERE id = ?", params)

            # Ensure an initial history entry exists
            cur.execute("SELECT id FROM repair_status_history WHERE repair_id = ?", (row_id,))
            if not cur.fetchone():
                final_status = updates.get("status", status or "received")
                cur.execute("""
                INSERT INTO repair_status_history (repair_id, old_status, new_status, comment, changed_at)
                VALUES (?, NULL, ?, 'Инициализация сервисной записи', ?)
                """, (row_id, final_status, now_str))

        conn.commit()
    finally:
        conn.close()

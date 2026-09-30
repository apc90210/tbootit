import os
import tempfile
import sqlite3
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import migrate_db
from app import models
from app.services import sale_service


def test_fresh_database_creates_correct_schema():
    """Verify that a brand new empty database creates checkout_idempotency with id primary key."""
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "fresh_test.db")
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        try:
            # 1. Run Base.metadata.create_all
            models.Base.metadata.create_all(bind=engine)
            # 2. Run migrate_db
            migrate_db(target_engine=engine)

            # 3. Verify schema
            with engine.connect() as conn:
                cols = conn.execute(text("PRAGMA table_info(checkout_idempotency);")).fetchall()
                col_names = [r[1] for r in cols]
                assert "id" in col_names, f"Expected 'id' in checkout_idempotency columns: {col_names}"
                assert "client_checkout_id" in col_names
                assert "sale_id" in col_names
                assert "request_hash" in col_names

                id_col = next(r for r in cols if r[1] == "id")
                assert id_col[5] == 1, "id column must be PRIMARY KEY"

                qc = conn.execute(text("PRAGMA quick_check;")).fetchall()
                assert qc == [("ok",)]
                fk = conn.execute(text("PRAGMA foreign_key_check;")).fetchall()
                assert fk == []
        finally:
            engine.dispose()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_pre_stage04b_database_upgrades_cleanly():
    """Verify an existing database from before Stage 04B upgrades cleanly without data loss."""
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "pre_stage04b.db")
        conn_raw = sqlite3.connect(db_path)
        try:
            conn_raw.execute("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR,
                    sale_price FLOAT,
                    quantity INTEGER DEFAULT 1,
                    status VARCHAR DEFAULT 'in_stock',
                    storage_location VARCHAR DEFAULT 'store'
                );
            """)
            conn_raw.execute("""
                CREATE TABLE sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_amount FLOAT,
                    payment_method VARCHAR,
                    status VARCHAR DEFAULT 'completed'
                );
            """)
            conn_raw.execute("INSERT INTO products (title, sale_price, quantity) VALUES ('Test Item', 1000.0, 5);")
            conn_raw.execute("INSERT INTO sales (total_amount, payment_method) VALUES (1000.0, 'cash');")
            conn_raw.commit()
        finally:
            conn_raw.close()

        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        try:
            # Run migration on legacy DB
            migrate_db(target_engine=engine)

            with engine.connect() as conn:
                # Check sales has client_checkout_id
                sales_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(sales);")).fetchall()]
                assert "client_checkout_id" in sales_cols

                # Check checkout_idempotency exists with id primary key
                idem_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(checkout_idempotency);")).fetchall()]
                assert "id" in idem_cols
                assert "client_checkout_id" in idem_cols

                # Verify business data preserved
                prod_count = conn.execute(text("SELECT COUNT(*) FROM products;")).scalar()
                assert prod_count == 1
                sale_count = conn.execute(text("SELECT COUNT(*) FROM sales;")).scalar()
                assert sale_count == 1

                qc = conn.execute(text("PRAGMA quick_check;")).fetchall()
                assert qc == [("ok",)]
                fk = conn.execute(text("PRAGMA foreign_key_check;")).fetchall()
                assert fk == []
        finally:
            engine.dispose()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_reproduce_and_repair_broken_table_without_id():
    """
    Reproduces the previous failure:
    checkout_idempotency was created with client_checkout_id as PK, missing the 'id' column.
    migrate_db must safely upgrade it to have 'id' column while preserving existing rows.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "broken_repro.db")
        conn_raw = sqlite3.connect(db_path)
        try:
            conn_raw.execute("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR,
                    sale_price FLOAT,
                    quantity INTEGER DEFAULT 1,
                    status VARCHAR DEFAULT 'in_stock',
                    storage_location VARCHAR DEFAULT 'store'
                );
            """)
            conn_raw.execute("""
                CREATE TABLE sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_amount FLOAT,
                    payment_method VARCHAR,
                    status VARCHAR DEFAULT 'completed',
                    client_checkout_id VARCHAR(64)
                );
            """)
            # BROKEN TABLE: primary key is client_checkout_id, NO 'id' column
            conn_raw.execute("""
                CREATE TABLE checkout_idempotency (
                    client_checkout_id VARCHAR(64) PRIMARY KEY,
                    sale_id INTEGER NOT NULL,
                    request_hash VARCHAR(64) NOT NULL,
                    cashier_name VARCHAR(128),
                    created_at DATETIME
                );
            """)
            conn_raw.execute("INSERT INTO products (title, sale_price, quantity) VALUES ('Product A', 500.0, 2);")
            conn_raw.execute("INSERT INTO sales (id, total_amount, payment_method, client_checkout_id) VALUES (1, 500.0, 'cash', 'prior-uuid-1');")
            conn_raw.execute("""
                INSERT INTO checkout_idempotency (client_checkout_id, sale_id, request_hash, cashier_name, created_at)
                VALUES ('prior-uuid-1', 1, 'hash-abc', 'Cashier Old', '2026-09-30 08:00:00');
            """)
            conn_raw.commit()
        finally:
            conn_raw.close()

        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        try:
            # 1. Run migration: should detect missing 'id' and upgrade table preserving prior-uuid-1
            migrate_db(target_engine=engine)

            with engine.connect() as conn:
                cols = conn.execute(text("PRAGMA table_info(checkout_idempotency);")).fetchall()
                col_names = [r[1] for r in cols]
                assert "id" in col_names, "id column must be present after upgrade"

                id_col = next(r for r in cols if r[1] == "id")
                assert id_col[5] == 1, "id column must be PRIMARY KEY"

                # Check preserved row
                row = conn.execute(text("SELECT id, client_checkout_id, sale_id, request_hash, cashier_name FROM checkout_idempotency;")).fetchone()
                assert row is not None
                assert row[0] is not None and row[0] > 0
                assert row[1] == "prior-uuid-1"
                assert row[2] == 1
                assert row[3] == "hash-abc"
                assert row[4] == "Cashier Old"

                qc = conn.execute(text("PRAGMA quick_check;")).fetchall()
                assert qc == [("ok",)]

            # 2. Verify SQLAlchemy CheckoutIdempotency ORM query succeeds without OperationalError
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                item = session.query(models.CheckoutIdempotency).filter(
                    models.CheckoutIdempotency.client_checkout_id == "prior-uuid-1"
                ).first()
                assert item is not None
                assert item.id is not None
                assert item.sale_id == 1
            finally:
                session.close()

            # 3. Verify running migrate_db again on the repaired DB is completely idempotent
            migrate_db(target_engine=engine)
            with engine.connect() as conn:
                qc = conn.execute(text("PRAGMA quick_check;")).fetchall()
                assert qc == [("ok",)]
                count = conn.execute(text("SELECT COUNT(*) FROM checkout_idempotency;")).scalar()
                assert count == 1
        finally:
            engine.dispose()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

# Development Databases

> **One-liner rule:** Tests MUST NEVER touch the canonical DB. All test runs use
> a throwaway SQLite file in a `tempfile.mkdtemp()` directory that is destroyed
> after the session.

---

## Canonical (Production) Databases

| Path | Size (approx.) | Purpose |
|------|----------------|---------|
| `data/db/technoreboot.db` | ~5 MB | **Primary production DB** — the live store of all real business data |
| `core/technoreboot.db` | ~1.5 MB | Operational copy — used by the running `core/` FastAPI service |

Both are tracked by `.gitignore` and are **never committed to version control**.

---

## Forbidden Paths During Tests

The isolation layer rejects any attempt to write to:

| Pattern | Guard |
|---------|-------|
| `data/db/technoreboot.db` | `database.py` runtime fail-safe |
| `core/technoreboot.db` | `database.py` runtime fail-safe |
| `technoreboot.db` (repository root) | `conftest.py` env-var override + `.gitignore` |

If a test accidentally targets any of the above paths, a `RuntimeError` is
raised before any `SessionLocal()` is created.

---

## How Isolation Is Enforced

`
pytest
 |-- C:\tbootit\conftest.py           <- root session fixture
 |    |-- os.environ["IS_TESTING"] = "1"
 |    |-- os.environ["DATABASE_URL"] = "sqlite:////<tmpdir>/isolated_test.db"
 |    +-- yields -> test runs in complete isolation
 +-- C:\tbootit\core\tests\conftest.py <- core-specific fixtures
      +-- re-applies same override for the core test suite
`

`core/app/database.py` checks `IS_TESTING` at engine-bind time. If the flag is
set and the resolved URL path contains `technoreboot.db`, it raises
`RuntimeError` immediately.

---

## Temp DB Lifecycle

`
session start -> tempfile.mkdtemp() -> isolated_test.db created
test runs                           -> all writes go to temp file only
session end   -> tempfile cleanup   -> temp dir removed
`

> **Windows note:** SQLite may hold a file lock until the Python process fully
> exits. If `tempfile` cleanup raises `PermissionError: [WinError 32]` during
> teardown, this is a harmless Windows SQLite lock artefact and does NOT
> indicate data leakage.

---

## Root `technoreboot.db` - Forensic History

Prior to WEB-03A-R2, running `tests/` from the repository root created
`C:\tbootit\technoreboot.db` because the relative URL `sqlite:///technoreboot.db`
resolved against the CWD.

- Forensic SHA256: `e8229b6680a532ca9cad67b203a6754ede9a730ac5b2583e7851179c34aa6563`
- Contents: seed API responses + test strings (Test Laptop for Delete,
  Audit Test Product, repair numbers R-11B-REQ*)
- Deleted 2026-09-29 as part of WEB-03A-R2 cleanup
- `.gitignore` now explicitly excludes this path and all SQLite journal variants

---

## Quick Reference

`
# Run ALL tests safely (both test suites)
python -m pytest tests/ core/tests/ -q

# Run only the core API unit tests
python -m pytest core/tests/ -q

# Verify isolation: root DB must NOT exist after test run
Test-Path C:\tbootit\technoreboot.db   # expected: False
`

---

## Adding New Tests

1. Never call `SessionLocal()` or `create_engine()` with a hard-coded path.
2. Use the `db` fixture provided by `conftest.py` -- it hands you the isolated session.
3. If you need to inspect the test DB during a run, check `DATABASE_URL` in your test environment.
4. All test files must be runnable from the repository root via
   `python -m pytest` -- do not require `cd core/` before running.

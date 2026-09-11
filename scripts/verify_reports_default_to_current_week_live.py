#!/usr/bin/env python3
"""
Live verification script confirming Reports default to current week:
1. Accesses /inventory/reports/sales over Gateway 8443 (mTLS) without parameters.
2. Verifies the week button has class 'active'.
3. Verifies date pickers are populated with the current week (Monday to today).
4. Verifies quick filters for today, month, year, and custom continue to function.
"""

import sys
from datetime import date, timedelta
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GATEWAY_URL = "https://127.0.0.1:8443"

OWNER_CERT = PROJECT_ROOT / "data" / "auth" / "certificates" / "owner.crt"
OWNER_KEY = PROJECT_ROOT / "data" / "auth" / "certificates" / "owner.key"
CA_CERT = PROJECT_ROOT / "data" / "auth" / "ca" / "ca.crt"


def main():
    print("=== STARTING LIVE VERIFICATION: REPORTS DEFAULT TO CURRENT WEEK ===")

    assert OWNER_CERT.exists(), f"Owner cert missing: {OWNER_CERT}"
    assert OWNER_KEY.exists(), f"Owner key missing: {OWNER_KEY}"
    assert CA_CERT.exists(), f"CA cert missing: {CA_CERT}"

    gw_client = httpx.Client(
        base_url=GATEWAY_URL,
        cert=(str(OWNER_CERT), str(OWNER_KEY)),
        verify=str(CA_CERT),
        timeout=15.0,
        trust_env=False
    )

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.isoformat()
    today_str = today.isoformat()

    # Step 1: Default /inventory/reports/sales without parameters
    print("\n--- Step 1: Default Request /inventory/reports/sales (No Parameters) ---")
    res_default = gw_client.get("/inventory/reports/sales")
    assert res_default.status_code == 200, f"Expected 200, got {res_default.status_code}"
    html_default = res_default.text
    assert "Отчёт по продажам" in html_default
    assert "Сводка денег за период" in html_default

    # Verify Week button has class 'active'
    assert 'period=week" class="btn btn-outline-primary active"' in html_default, \
        "Week button is not active by default in /inventory/reports/sales"
    print("[OK] Week button is active by default.")

    # Verify Date inputs are synchronized to current week
    assert f'id="date_from" name="date_from" value="{monday_str}"' in html_default, \
        f"date_from input does not match current week Monday ({monday_str})"
    assert f'id="date_to" name="date_to" value="{today_str}"' in html_default, \
        f"date_to input does not match today ({today_str})"
    print(f"[OK] Date inputs synchronized to current week: {monday_str} to {today_str}.")

    # Step 2: Test quick filter "Сегодня"
    print("\n--- Step 2: Quick Filter 'Сегодня' ---")
    res_today = gw_client.get("/inventory/reports/sales?period=today")
    assert res_today.status_code == 200
    html_today = res_today.text
    assert 'period=today" class="btn btn-outline-primary active"' in html_today
    assert f'id="date_from" name="date_from" value="{today_str}"' in html_today
    assert f'id="date_to" name="date_to" value="{today_str}"' in html_today
    print("[OK] 'Сегодня' filter works cleanly and sets date pickers to today.")

    # Step 3: Test quick filter "Месяц"
    print("\n--- Step 3: Quick Filter 'Месяц' ---")
    res_month = gw_client.get("/inventory/reports/sales?period=month")
    assert res_month.status_code == 200
    html_month = res_month.text
    assert 'period=month" class="btn btn-outline-primary active"' in html_month
    first_of_month = today.replace(day=1).isoformat()
    assert f'id="date_from" name="date_from" value="{first_of_month}"' in html_month
    print(f"[OK] 'Месяц' filter works cleanly ({first_of_month} to {today_str}).")

    # Step 4: Test quick filter "Год"
    print("\n--- Step 4: Quick Filter 'Год' ---")
    res_year = gw_client.get("/inventory/reports/sales?period=year")
    assert res_year.status_code == 200
    html_year = res_year.text
    assert 'period=year" class="btn btn-outline-primary active"' in html_year
    jan_first = today.replace(month=1, day=1).isoformat()
    assert f'id="date_from" name="date_from" value="{jan_first}"' in html_year
    print(f"[OK] 'Год' filter works cleanly ({jan_first} to {today_str}).")

    # Step 5: Test custom dates submission
    print("\n--- Step 5: Custom Dates Submission ---")
    res_custom = gw_client.get(f"/inventory/reports/sales?period=custom&date_from={monday_str}&date_to={today_str}")
    assert res_custom.status_code == 200
    html_custom = res_custom.text
    assert f'id="date_from" name="date_from" value="{monday_str}"' in html_custom
    assert f'id="date_to" name="date_to" value="{today_str}"' in html_custom
    print("[OK] Custom date range submission works cleanly.")

    print("\n=== ALL REPORTS DEFAULT CHECKS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()

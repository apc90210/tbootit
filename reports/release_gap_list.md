# Technoreboot — Release Gap List
**Audit Date:** 2026-09-11  
**Stage:** 08A-R1 — Full Owner Workflow Audit and Release Gap List  
**Workspace:** `C:\tbootit`  
**Target Environment:** Local Stack / Pre-Production VDS Baseline  
**Production Deployment Blockers (P0):** **0 (NONE)**

---

## Executive Summary

A comprehensive, end-to-end audit was conducted across all real Owner workflows through the secure Gateway (`https://127.0.0.1:8443`) and internal microservices (`core-api`, `admin-shell`, `inventory-sales-module`, `repairs-module`, `avito-module`).

All core business capabilities required for live operations (Authentication/mTLS, Product Catalog, JSON import/export/AI generator, Avito extension synchronization, Batch price tags and operations, POS Sales and stock deduction, Financial Reporting, Repairs lifecycle and print acts, Web Backup/Restore, and Client Certificate issuance/revocation) have been verified and **PASSED 100%**.

Data consistency checks verified 0 duplicate Avito IDs, 0 duplicate SKUs, 0 missing photos on disk, 0 broken foreign key references, and 0 inventory state anomalies. The strict data safety invariant was preserved throughout the audit: **all live business IDs remain intact and 0 business records were deleted**.

---

## Deployment Readiness Status

| Metric | Status | Details |
|---|---|---|
| **P0 Blockers** | **0** | **No blockers remain for deployment readiness** |
| **P1 Gaps** | 3 | Early production operational improvements |
| **P2 Optimizations**| 3 | Convenience & performance enhancements |
| **P3 Enhancements** | 3 | Roadmap features |
| **Gateway Security**| **PASS** | mTLS enforced, role separation active, 403 on missing cert |
| **Data Safety** | **PASS** | `REAL_PRODUCT_ID_SET_UNCHANGED`: True |

---

## Categorized Release Gap List

### Priority 0: Deployment Blockers (Must-Have Before VDS Deployment)
*None. All essential workflows, security gates, backup recovery, and UI pathways are verified and functional.*

---

### Priority 1: High Priority for Early Production Use

#### GAP-1: Automated Periodic Backup Scheduling (Cron / Background Worker)
- **Description:** Currently, full system backups (format version 1.0 containing SQLite DB, photos, auth certificates, and manifest) can be generated manually via the Web Admin UI (`/backups`) or through CLI scripts. For resilient 24/7 production operation, an automated recurring background job (e.g. nightly cron) should be established to create and retain rotating timestamped archives.
- **Affected Workflow:** Backup / Disaster Recovery
- **Severity:** P1
- **Workaround:** The Owner can create manual backups on demand directly in the Web UI `/backups` before or after significant operations.
- **Estimated Effort:** 2–3 hours.

#### GAP-2: Real-time Avito Background Sync (Webhooks / Scheduled Worker)
- **Description:** Avito integration operates via the local bridge and Chrome extension (v0.2.53), providing idempotent imports, archive reactivations, and anti-inflation guards. However, inventory changes on Avito require the browser extension to actively synchronize. Native webhooks or scheduled background polling would allow passive synchronization.
- **Affected Workflow:** Avito Integration
- **Severity:** P1
- **Workaround:** Staff or Owner uses the Avito Chrome extension bridge button to trigger catalog synchronization when active on Avito.
- **Estimated Effort:** 1–2 days.

#### GAP-3: Direct Hardware ESC/POS Receipt Printer Integration
- **Description:** POS sales receipts and Repair Service Acts currently format cleanly in standard browser print dialogs using 58mm/80mm and A4 responsive print CSS. Adding direct USB/Ethernet ESC/POS socket printing would enable 1-click silent receipt printing without opening the browser print preview dialog.
- **Affected Workflow:** POS Sales / Repairs Receipt Printing
- **Severity:** P1
- **Workaround:** Browser print dialog automatically formats to receipt dimensions and remembers printer defaults.
- **Estimated Effort:** 4–6 hours.

---

### Priority 2: Nice to Have / Optimizations

#### GAP-4: Client-Side Image Compression Prior to Upload
- **Description:** When staff upload high-resolution product photos directly from smartphone cameras (5–12 MB per JPEG), the full file is uploaded before the server generates thumbnails and web-optimized images. Pre-compressing images in JavaScript canvas to ~1–2 MB before POSTing would improve upload speed on slower Wi-Fi connections.
- **Affected Workflow:** Product Catalog Photo Upload
- **Severity:** P2
- **Workaround:** Server accepts full resolution files and securely writes them to persistent storage.
- **Estimated Effort:** 3–4 hours.

#### GAP-5: Bulk Status Transition in Repairs Registry
- **Description:** The Product Catalog supports batch actions (price tags, status changes). In the Repairs registry, technicians transition orders individually. A bulk checkbox selection to mark multiple diagnostic orders simultaneously would streamline high-volume workshop operations.
- **Affected Workflow:** Repairs Management
- **Severity:** P2
- **Workaround:** Repairs can be transitioned rapidly in individual order detail screens.
- **Estimated Effort:** 3–4 hours.

#### GAP-6: Specialized "Technician" Role in RBAC
- **Description:** The mTLS certificate authority currently issues `OWNER` certificates (full access to inventory, sales, reports, repairs, certificates, backups) and `USER` certificates (inventory, repairs, sales; restricted from certificates and backups). Introducing a dedicated `TECHNICIAN` role that can manage repair orders without viewing financial sales reports would further isolate sensitive financial data.
- **Affected Workflow:** Security / Certificate Access Control
- **Severity:** P2
- **Workaround:** Use `USER` role certificates for shop floor staff.
- **Estimated Effort:** 2–3 hours.

---

### Priority 3: Future Enhancements

#### GAP-7: Automated Customer SMS / Telegram Notification on Repair Completion
- **Description:** When a repair order transitions to `ready` or `issued`, send an automated SMS or Telegram message to `customer_phone` informing the customer that their device is ready for pickup with diagnostic fees and repair totals.
- **Affected Workflow:** Repairs / Customer Communications
- **Severity:** P3
- **Workaround:** Workshop staff notify customer via phone call or manual messaging.
- **Estimated Effort:** 1 day.

#### GAP-8: Hardware Barcode Scanner Autofocus Listener
- **Description:** Add a global hotkey or JavaScript listener on the POS Sales page to detect rapid keystroke sequences from standard USB/Bluetooth barcode scanners and automatically focus the product barcode search field.
- **Affected Workflow:** POS Sales Checkout
- **Severity:** P3
- **Workaround:** User clicks the search input or uses keyboard shortcut before scanning barcode.
- **Estimated Effort:** 2 hours.

#### GAP-9: Dark Mode Theme Support in Admin Shell
- **Description:** Provide a theme toggle (Light / Dark) for Admin Shell and module templates to reduce eye strain during evening workshop operations.
- **Affected Workflow:** UI / UX
- **Severity:** P3
- **Workaround:** System utilizes clean, high-contrast light theme.
- **Estimated Effort:** 4 hours.

---

## Conclusion

The Technoreboot system has reached full operational maturity for local and staging deployment. There are **0 P0 blocking issues**. The remaining items in this list represent non-blocking enhancements that can be prioritized in subsequent operational phases without hindering initial production rollout.

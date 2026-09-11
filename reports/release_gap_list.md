# Technoreboot — Release Gap List
**Audit Date:** 2026-09-11  
**Revision:** Stage 08A-R1-R1 — Gap Severity Normalization & Avito Regression Closure  
**Workspace:** `C:\tbootit`  
**Target Environment:** Local Stack / Pre-Production VDS Baseline  
**Production Deployment Blockers (P0):** **0 (NONE)**  
**Broken Core Daily Workflows (P1):** **0 (NONE)**  

---

## Severity Classification Definitions

Per the Technoreboot release audit standards:
- **P0**: Blocks production / data loss / serious security vulnerability (MUST fix before deployment).
- **P1**: Existing core daily workflow is broken or unreliable (MUST fix before deployment).
- **P2**: Important operational or usability improvement; viable workaround exists (post-release).
- **P3**: Polish / future enhancement / optional automation (roadmap backlog).

---

## Executive Summary of Normalization

In the initial Stage 08A-R1 review, three items (GAP-1 Automated backup cron, GAP-2 Avito background webhooks, GAP-3 Direct ESC/POS socket printing) were colloquially designated as P1 based on operational desire. However, upon auditing against the formal release criteria:
1. **Backups** are 100% operational via the Web Admin UI (`/backups`) and CLI;
2. **Avito synchronization** is 100% operational via the Chrome extension bridge (v0.2.53);
3. **Receipt & Act printing** is 100% operational via the browser print dialog with dedicated 58mm/80mm and A4 CSS.

Because none of these represent a broken core daily workflow and reliable workarounds are fully operational, they have been properly normalized to **P2 (Important Operational Improvements)**.

---

## Gap Normalization Table

| Gap ID | Description | Old Severity | New Severity | Rationale | Blocks VDS Deployment |
|---|---|:---:|:---:|---|:---:|
| **GAP-1** | Automated Periodic Backup Scheduling (Cron) | P1 | **P2** | Web UI `/backups` manual backup creation and upload restore works 100% reliably. Missing cron automation does not break daily workflow. | **No** |
| **GAP-2** | Real-time Avito Background Sync (Webhooks) | P1 | **P2** | Chrome extension bridge (v0.2.53) performs verified idempotent import, anti-inflation, and archive reactivation. Webhook is an optional convenience. | **No** |
| **GAP-3** | Direct Hardware ESC/POS Socket Printing | P1 | **P2** | Standard browser print dialog formats receipts and service acts cleanly using 58mm/80mm responsive CSS. Direct socket printing saves 1 click. | **No** |
| **GAP-4** | Client-Side Image Pre-Compression | P2 | **P2** | Server accepts full-resolution uploads and generates web thumbnails safely. Pre-compression is a network optimization. | **No** |
| **GAP-5** | Bulk Status Transition in Repairs Registry | P2 | **P2** | Individual repair orders transition smoothly in order detail view. Bulk table transitions are a usability optimization. | **No** |
| **GAP-6** | Dedicated "Technician" Role in RBAC | P2 | **P2** | Current mTLS RBAC (OWNER and USER) is enforced and secure. Granular technician role is an operational security optimization. | **No** |
| **GAP-7** | Automated Customer SMS / Telegram Notification | P3 | **P3** | Workshop staff notify customers via phone call or manual chat. Automated notifications are a roadmap feature. | **No** |
| **GAP-8** | Hardware Barcode Scanner Autofocus Listener | P3 | **P3** | User focuses search field before scanning barcode. Global keystroke listener is a convenience feature. | **No** |
| **GAP-9** | Dark Mode Theme Support in Admin Shell | P3 | **P3** | Cosmetic UI theme feature. | **No** |

---

## Release Gap Counts

- **P0 Count:** **0**
- **P1 Count:** **0**
- **P2 Count:** **6**
- **P3 Count:** **3**
- **VDS Deployment Blockers:** **0**

---

## Detailed Gap Profiles

### Priority 0: Deployment Blockers
*None.*

### Priority 1: Core Broken Daily Workflows
*None.*

### Priority 2: Important Operational Improvements (Post-Deployment Backlog)

#### GAP-1: Automated Periodic Backup Scheduling (Cron / Background Worker)
- **OLD_SEVERITY:** P1
- **NEW_SEVERITY:** P2
- **RATIONALE:** Web UI `/backups` manual backup creation and upload restore is 100% operational. A background cron job is an automation improvement that does not block live operation.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Owner or administrator creates on-demand backups via the `/backups` page or runs periodic CLI scripts.
- **Estimated Effort:** 2–3 hours.

#### GAP-2: Real-time Avito Background Sync (Webhooks / Scheduled Worker)
- **OLD_SEVERITY:** P1
- **NEW_SEVERITY:** P2
- **RATIONALE:** The primary supported workflow uses the Chrome Extension (v0.2.53), which reliably performs catalog synchronization, anti-inflation guards, and archive reactivations. A server-side webhook listener is an optional background sync enhancement.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Staff or Owner clicks the extension bridge icon in Chrome when active on Avito.
- **Estimated Effort:** 1–2 days.

#### GAP-3: Direct Hardware ESC/POS Receipt Printer Integration
- **OLD_SEVERITY:** P1
- **NEW_SEVERITY:** P2
- **RATIONALE:** POS sales receipts and Repair Service Acts format cleanly in standard browser print dialogs using 58mm/80mm responsive CSS. Direct socket printing avoids opening the browser print preview, but is not required for daily sales.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Standard browser print dialog remembers thermal printer defaults and prints accurately.
- **Estimated Effort:** 4–6 hours.

#### GAP-4: Client-Side Image Compression Prior to Upload
- **OLD_SEVERITY:** P2
- **NEW_SEVERITY:** P2
- **RATIONALE:** Server accepts full resolution files and creates thumbnails safely in `/data/storage`. Client-side compression is a speed optimization for slow connections.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Photos are uploaded directly from disk or camera.
- **Estimated Effort:** 3–4 hours.

#### GAP-5: Bulk Status Transition in Repairs Registry
- **OLD_SEVERITY:** P2
- **NEW_SEVERITY:** P2
- **RATIONALE:** Technicians can transition repair tickets individually in each order's detail screen. Bulk status selection is a high-volume convenience.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Update orders individually via status dropdown.
- **Estimated Effort:** 3–4 hours.

#### GAP-6: Specialized "Technician" Role in RBAC
- **OLD_SEVERITY:** P2
- **NEW_SEVERITY:** P2
- **RATIONALE:** Existing OWNER and USER roles properly restrict `/backups` and `/certificates` access. A dedicated technician role isolating repair tickets from sales reports is an operational enhancement.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Issue USER certificates for workshop staff.
- **Estimated Effort:** 2–3 hours.

### Priority 3: Future Polish & Enhancements

#### GAP-7: Automated Customer SMS / Telegram Notification on Repair Completion
- **OLD_SEVERITY:** P3
- **NEW_SEVERITY:** P3
- **RATIONALE:** Customer notification automation.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Staff call or message customer directly.
- **Estimated Effort:** 1 day.

#### GAP-8: Hardware Barcode Scanner Autofocus Listener
- **OLD_SEVERITY:** P3
- **NEW_SEVERITY:** P3
- **RATIONALE:** Auto-focus convenience for USB barcode guns in POS checkout.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** Click search bar before scanning.
- **Estimated Effort:** 2 hours.

#### GAP-9: Dark Mode Theme Support in Admin Shell
- **OLD_SEVERITY:** P3
- **NEW_SEVERITY:** P3
- **RATIONALE:** Cosmetic theme preference.
- **BLOCKS_VDS_DEPLOYMENT:** false
- **Workaround:** High-contrast light mode UI.
- **Estimated Effort:** 4 hours.

---

## Conclusion

Following formal severity audit, there are **0 P0 blockers** and **0 P1 broken workflows**. The platform satisfies all release criteria for production deployment readiness.

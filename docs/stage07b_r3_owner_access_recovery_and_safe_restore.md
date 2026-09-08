# Stage 07B-R3: OWNER Access Recovery and Safe Web Restore Policy

## 1. Incident Overview & Root Cause Analysis

### Incident Description
During manual verification in Stage 07B-R2, the Owner presented their existing browser-installed certificate (`Technoreboot OWNER`) to access `https://127.0.0.1:8443`, but received an HTTP `403 Forbidden` response from the Nginx gateway.

### Root Cause Analysis
1. **Unconstrained Auth Restore in Web Flow:** In Stage 07B-R2, `backup_service.restore_backup()` extracted all components present in the backup ZIP, including `auth/`, into the runtime directory `data/auth/`.
2. **Identity Desynchronization:** An archive created during development or testing containing an alternate/test CA (`5D24...`) was restored. As a result:
   - The runtime `data/auth/ca.crt` was replaced by the test CA.
   - The Nginx Gateway (which loads `data/auth/ca.crt` as `ssl_client_certificate`) was configured to trust the test CA instead of the accepted Stage 07A CA (`32CE...`).
3. **Gateway Rejection:** When the Owner presented their Stage 07A client certificate (Serial `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`, signed by CA `32CE...`), Nginx client certificate verification failed because the client certificate was not signed by the newly restored CA in `data/auth/ca.crt`.

---

## 2. Recovery of Accepted Stage 07A OWNER Identity

To resolve the incident without requiring the Owner to re-import certificates:
1. The authoritative Stage 07A accepted authentication state was extracted from `TECHNOREBOOT_BACKUP_2026-09-08_142812.zip` into `data/auth/`.
2. Cleaned any temporary non-registry certificate files.
3. Reloaded both `technoreboot-gateway` and `technoreboot-admin-shell`.
4. Verified that the live identity matches the accepted Stage 07A specifications:
   - **CA Subject:** `CN=Technoreboot Root CA, O=Technoreboot, C=RU`
   - **CA Fingerprint (SHA-256):** `32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA`
   - **OWNER Subject:** `CN=Technoreboot OWNER, O=Technoreboot, C=RU`
   - **OWNER Serial:** `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`
   - **OWNER Fingerprint (SHA-256):** `022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D`
5. **No new CA or OWNER certificates were generated.** The Owner's existing certificate installed in their browser works immediately without re-import.

---

## 3. Safe Web Restore Policy vs Disaster Recovery

### Safe Online Web Restore Policy (`/backups`)
When an Owner triggers a restore via `/admin-api/backups/restore` or the Web UI:
- **Restored Components:**
  - Database: `technoreboot.db` (products, categories, sales, customers, repair tickets).
  - Storage/Media: `storage/` directory (product and repair photos).
  - Avito State: `avito-module` mutable cache/storage.
- **Strictly Preserved Components (Untouched):**
  - Live Authentication: `data/auth/`
  - Current Root CA (`ca.crt`, `ca.key`)
  - Current OWNER credentials (`owner.crt`, `owner.key`, `owner.p12`)
  - Current USER certificate registry (`registry.json`)
  - Revocation states (any certificates revoked post-backup remain revoked)
  - Newly issued certificates (any user certificates created post-backup remain active and valid)

### Emergency Disaster Recovery Packaging
- System backup archives created via `/admin-api/backups/download` **continue to include** the `auth/` directory.
- This ensures that if the physical host or disk is destroyed, a full disaster recovery can rebuild the identical cryptographic root on a new host.
- However, the online web restore routine explicitly ignores `auth/` during normal operation.

---

## 4. User Interface

On the `/backups` page, the restore warning text has been updated:
> «Восстановление заменит базу данных и изменяемые данные системы состоянием из резервной копии. Текущие сертификаты доступа при обычном онлайн-восстановлении сохраняются.»

This provides clear assurance to the Owner that restoring older data will never lock them out or invalidate active employee certificates.

---

## 5. Automated Verification Matrix

The end-to-end verification script `scripts/verify_stage07b_r3_safe_restore.py` validates the entire access and restore lifecycle through the real Nginx Gateway (`https://127.0.0.1:8443`):

| Test | Objective | Result |
|---|---|---|
| **TEST A** | Live OWNER identity matches accepted Stage 07A serial and fingerprint | PASS |
| **TEST B** | Live OWNER access through real gateway (`/`, `/certificates`, `/backups`) returns 200 OK | PASS |
| **TEST C** | CA and OWNER identity consistency (no new identities generated) | PASS |
| **TEST D** | Web backup generation downloads valid archive | PASS |
| **TEST E** | Web backup archive contains emergency `auth/` component | PASS |
| **TEST F** | Normal web restore preserves live auth state (post-backup cert intact) | PASS |
| **TEST G** | Database rolled back to exact pre-backup baseline | PASS |
| **TEST H** | Storage/media files rolled back to pre-backup baseline | PASS |
| **TEST I** | OWNER mTLS access works immediately after restore without re-import | PASS |
| **TEST J** | Existing USER revoked certificate status preserved | PASS |
| **TEST K** | Normal USER denied access to Owner endpoints (HTTP 403 Forbidden) | PASS |
| **TEST L** | Corrupted/invalid archive rejected before touching live data (HTTP 400) | PASS |
| **TEST M** | All unit tests in `admin-shell/tests` pass | PASS |

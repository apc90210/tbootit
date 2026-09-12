# Stage 08D-R1R1: Test-Production Activation with Clean Server Data and Code-Only Deployment Model

**Document Date:** 2026-09-12  
**Status:** BLOCKED on Public DNS Delegation (`atanov821.serv.host` -> `144.31.50.134`)  
**Safety Status:** ZERO DATA DESTRUCTION (VDS and Local Business Data 100% Intact)

---

## 1. Executive Summary

Stage 08D-R1R1 initiates the transition of the real Debian VDS (`144.31.50.134`) into canonical test-production under a new operating architecture approved by the Project Owner:
1. **Local Workstation:** Permanently designated as DEV / TEST sandbox with dirty demo data. Stays running independently. Never pushes business data to VDS.
2. **Debian VDS:** Canonical real-user environment. Business data starts clean and accumulates real user transactions.
3. **Public Trusted TLS:** Requires valid public DNS resolution and ACME/Let's Encrypt certificate for `atanov821.serv.host`.
4. **Code-Only Deployment Model:** Container updates pull source and rebuild without ever wiping or restoring live VDS data.

### Immediate Blocker (Public DNS NXDOMAIN)
During DNS pre-flight verification (Section 4), authoritative Cloudflare nameservers (`peyton.ns.cloudflare.com` and `wally.ns.cloudflare.com`) for the zone `serv.host` returned `NXDOMAIN` for `atanov821.serv.host`. Public DNS queries across global resolvers (`1.1.1.1`, `8.8.8.8`, `77.88.8.8`, `9.9.9.9`) all confirmed that no `A` record exists for `atanov821.serv.host`.

An automated Certbot dry-run test executed on the VDS confirmed the failure:
```text
Detail: DNS problem: NXDOMAIN looking up A for atanov821.serv.host - check that a DNS record exists for this domain
```

Pursuant to Section 4 and Section 25 of the Stage 08D Prompt:
> **"If trusted TLS cannot be obtained, return BLOCKED and DO NOT perform the destructive clean-data step."**

The destructive wipe of live business data on the VDS was **intentionally halted** before execution. Zero business records, media files, or database rows were deleted.

---

## 2. Work Completed in Stage 08D-R1R1

Even though the destructive data reset was halted for safety, the foundational infrastructure and safeguards for the new operating model were successfully established:

### A. Pre-Reset Safety Backup (Section 5)
A full, validated server backup of the current VDS mutable state was created using the official `admin-shell/app/backup_service.py` service:
- **Backup Archive:** `/srv/technoreboot/deploy/pre_clean_reset/TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip`
- **Persistent Copy:** `/srv/technoreboot/data/backups/TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip`
- **Archive SHA256:** `4362991cc8216b66d36451b1ea36be9ede3ff77173a9bb4a871be280c122b9cc`
- **VDS DB SHA256:** `fa835b6c2e737f5fa74a8808f2f04b452ee7d0960a9359dee0ae29f328ead6ae`
- **Storage Tree SHA256:** `ccc610dbc28c612c6fd51e08bfb630d7feab83f8008129df58082fdde43470ed` (1,529 files)
- **Auth Tree SHA256:** `c38aa50861553fad53c0aac7efc1c2023661715f484b5b2f97cc72efa01288c7`
- **Avito Tree SHA256:** `bf51373a7e7592d05e118c0dadd198ae939f9de6314f648b90bd62dcb203e027`
- **Safety Manifest:** `/srv/technoreboot/deploy/pre_clean_reset/safety_manifest.json`

### B. Production Data Guard Sentinel (Section 16)
Installed `/srv/technoreboot/data/.technoreboot_production_data` on VDS to strictly prohibit destructive operations and local-to-remote data overwrites:
```ini
environment=production
data_owner=vds
do_not_overwrite_from_local=true
installed_at=2026-09-12T11:16:44Z
```

### C. Code-Only Production Deployment Engine (Section 15)
Authored `deploy/production/update_code_only.sh`:
- Enforces presence of `/srv/technoreboot/data/.technoreboot_production_data`.
- Rejects any arguments containing restore keywords (`restore`, `bootstrap`, `wipe`, `reset`, `sync-from-local`).
- Creates pre-update backup of live VDS data before modifying code.
- Fetches target Git commit, validates compose config, builds images from source, and recreates containers.
- Waits for healthchecks across all 6 services with automated rollback on failure.
- Verifies post-deploy business counts match pre-deploy counts.

### D. Automated Test Coverage (Section 23)
Created `tests/test_production_data_guard.py` verifying script syntax, guard logic, forbidden restore rejection, and data root persistence invariants (3/3 tests PASSED).

---

## 3. Current Environment State

| Attribute | Local Workstation | Debian VDS (`144.31.50.134`) |
| :--- | :--- | :--- |
| **Role** | Permanent DEV / TEST Sandbox | Canonical Real-User Production |
| **Stack Status** | Running (all 6 services Up) | Stopped (ready for activation upon DNS) |
| **Database SHA256** | `98a58f06...` (50 products, 52 sales) | `fa835b6c...` (Intact, pre-reset backup saved) |
| **Client CA SHA256** | `a9b4d288...` | `a9b4d288...` (Preserved) |
| **Data Guard** | N/A (DEV) | Active (`.technoreboot_production_data`) |
| **Domain Resolution** | `localhost:8443` | `atanov821.serv.host` (NXDOMAIN in DNS) |

---

## 4. Required Action to Unblock Activation

To complete the clean test-production activation:
1. The Owner / hosting provider must add an `A` record in the Cloudflare DNS management panel for `serv.host`:
   ```text
   atanov821.serv.host.  IN  A  144.31.50.134
   ```
2. Verify DNS resolution:
   ```bash
   dig +short atanov821.serv.host @1.1.1.1
   # Must return: 144.31.50.134
   ```
3. Once DNS propagates, obtain Let's Encrypt certificate via Certbot standalone:
   ```bash
   certbot certonly --standalone -d atanov821.serv.host --non-interactive --agree-tos -m admin@atanov821.serv.host
   ```
4. Proceed with clean database initialization, empty-state verification, and production baseline backup.

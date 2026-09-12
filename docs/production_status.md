# Technoreboot Production Status

**Status Date:** 2026-09-12  
**Operating Architecture:** Local (Permanent DEV Sandbox) + VDS (Canonical Production)  
**Production Activation State:** Pre-Activated, BLOCKED on Public DNS Delegation

---

## 1. Network & Host Identity

| Parameter | Current Value | Required / Target Value | Status |
| :--- | :--- | :--- | :--- |
| **VDS Public IPv4** | `144.31.50.134` | `144.31.50.134` | MATCH |
| **VDS Hostname** | `atanov821.serv.host` | `atanov821.serv.host` | MATCH |
| **Public DNS A Record** | NXDOMAIN (No record in Cloudflare) | `144.31.50.134` | **BLOCKED** |
| **Public DNS AAAA Record** | None (Correct, no IPv6) | None | PASS |
| **Public Server TLS** | Self-signed pre-cutover certificate | Let's Encrypt Publicly Trusted | **Awaiting DNS** |
| **ACME Renewal Service** | Systemd `certbot.timer` installed | Active & enabled | READY |
| **mTLS Client CA** | `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` | Persistent | PRESERVED |

---

## 2. Environments Status

### Local Workstation (`C:\tbootit`)
- **Role:** Permanent DEV / TEST Sandbox.
- **Stack Status:** RUNNING (all 6 services Up and healthy).
- **Restart Count:** 0 across all containers.
- **Database Status:** 50 products, 52 sales, 66 repairs (SHA256: `98a58f06...`).
- **Data Sync:** Strictly isolated; local data will never sync to VDS.

### Debian VDS (`144.31.50.134`)
- **Role:** Canonical Real-User Test-Production.
- **Stack Status:** Standby (stopped pending DNS and clean start).
- **Production Data Guard:** Installed at `/srv/technoreboot/data/.technoreboot_production_data`.
- **Pre-Reset Safety Backup:** Stored at `/srv/technoreboot/deploy/pre_clean_reset/TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip` (`4362991c...`).
- **Live Database:** Intact, zero data destroyed (`fa835b6c...`, 50 products, 52 sales, 66 repairs).
- **Code-Only Update Script:** Installed at `deploy/production/update_code_only.sh`.

---

## 3. Deployment & Update Model

```text
LOCAL = DEV / TEST SANDBOX
VDS = CANONICAL REAL-USER DATA
CODE SYNCS LOCAL/GIT -> VDS
BUSINESS DATA NEVER SYNCS LOCAL -> VDS
VDS DATA SURVIVES CODE DEPLOYMENTS
```

- Deployment updates are triggered via `deploy/production/update_code_only.sh`.
- Ordinary deployments will never invoke `bootstrap_restore.py`, local data sync, or auth wipe.
- In-place SQLite backups occur automatically before every code change.
- Invariant verification checks ensure pre-update and post-update business record counts match identically.

---

## 4. Unblock Checklist

1. [ ] Owner/provider creates DNS A record: `atanov821.serv.host` -> `144.31.50.134` in Cloudflare for `serv.host`.
2. [ ] Run `certbot certonly --standalone -d atanov821.serv.host` on VDS to acquire Let's Encrypt certificate.
3. [ ] Copy certificate into `/srv/technoreboot/secrets/server.crt` and `server.key`.
4. [ ] Initialize clean empty database and storage on VDS.
5. [ ] Launch production stack and verify empty-state UI routes (`0 products, 0 sales, 0 repairs`).
6. [ ] Create baseline clean production backup.

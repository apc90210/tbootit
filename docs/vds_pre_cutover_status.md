# ТехноРебут — Real VDS Pre-Cutover Deployment Status

**Date:** 2026-09-12  
**Target Server:** 144.31.50.134 (`atanov821.serv.host`)  
**Stage:** Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification  

---

## 1. Server Specification & Environment
- **Host / Public IP:** `144.31.50.134`
- **Domain Name:** `atanov821.serv.host`
- **OS:** Debian GNU/Linux 13 (trixie) x86_64
- **Kernel:** `6.12.85+deb13-amd64`
- **CPU:** 1 vCPU (`AMD EPYC 7C13 64-Core Processor`)
- **RAM:** 2.0 GB Physical + 2.0 GB Swapfile
- **Storage:** 20 GB SSD (13 GB available after build and restore)
- **Docker Engine:** `29.8.0` (overlayfs, cgroup v2)
- **Docker Compose:** `v5.5.1`

---

## 2. Deployed Source & Restored Data
- **Remote Repository:** `/srv/technoreboot/app`
- **Git Commit:** `7e19c953936db92ee448616a70001c6bc8871b28` (matches GitHub `origin/main` exactly, rebuilt from source with `--no-cache`)
- **Images Built:** `890e8b0edb70`, `f08174cdf93d`, `eec54bf6f523`, `44d608f40048`, `9ec065122baa`, `72ba65eb42c1`
- **Restored Backup Archive:** `TECHNOREBOOT_BACKUP_2026-09-12_102533.zip`
- **Restored Data Root:** `/srv/technoreboot/data`
- **Restored Business State:**
  - Products: 50 (`[1..50]`)
  - Sales: 52 (`[1..52]`)
  - Repairs: 66 (`[1..66]`)
  - Product Photos: 50 (`[1..48, 50, 51]`)
  - External Listings: 50 (`[1..50]`)
  - Media Files: 315 files verified in `/srv/technoreboot/data/storage`
  - Client CA Fingerprint: `32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA` (identical to local master CA)
  - OWNER Certificate: Verified and accepted
  - Revocation Registry: 14 revoked certificates preserved
  - Avito Session State: Fully restored

---

## 3. Network & Security Hardening
- **Firewall:** `nftables` active
  - Allowed inbound ports: `22/tcp` (SSH), `80/tcp` (HTTP redirect), `443/tcp` (HTTPS mTLS)
  - Internal Docker virtual interfaces (`docker0`, `br-*`, `veth*`) accepted
  - All unsolicited inbound traffic dropped
- **Internal Services Port Exposure:** 0 host ports (all microservices communicate strictly over Docker bridge network `technoreboot-network`)
- **Production Secrets:** Strong random 64-character hex tokens generated on VDS in `/srv/technoreboot/secrets/production.env` (file permissions `0600`)
- **Server TLS:** Temporary self-signed pre-cutover server certificate generated for IP `144.31.50.134` (separate from client CA)

---

## 4. Pre-Cutover Verification Results
- **HTTP to HTTPS Redirection:** PASS (`301 Moved Permanently`)
- **HTTPS Gateway Access:** PASS
- **Unauthenticated Access (No Cert):** PASS (HTTP 403 Forbidden)
- **OWNER Certificate Access:** PASS (HTTP 200 on `/`, `/inventory/products`, `/inventory/sales`, `/repairs/repairs`, `/avito/extension`, `/backups`, `/certificates`)
- **USER Certificate RBAC:** PASS (HTTP 200 on operational routes; HTTP 403 Forbidden on `/backups` and `/certificates`)
- **Media Serving:** PASS (HTTP 200 on `/media/product_photos/1_51527540.jpg`, `/media/product_photos/2_bc9bdcec.jpg`, `/media/product_photos/3_f3b61975.jpg`)
- **Remote Backup Smoke Test:** PASS (`TECHNOREBOOT_BACKUP_2026-09-12_073237.zip` created on VDS under `/srv/technoreboot/data/backups/`)

---

## 5. Operational State & Split-Brain Prevention
- **Local Workstation:** Running and operational (sole active writer, zero data changes).
- **VDS Application Stack:** Deliberately stopped (`docker compose stop`) after proof completion.
- **DNS:** Unchanged.
- **Public Cutover:** Not performed.

```text
VDS APPLICATION STACK IS STOPPED PENDING FINAL CUTOVER
```

# ТехноРебут — Stage 08C-R1 / 08C-R1-R2 / 08C-R1-R3: Real VDS Pre-Cutover Deployment Runbook

## 1. Overview
This document records the exact procedure, configuration standards, and verification steps performed during the deployment and final runtime-head rebuild of **ТехноРебут** on the real Debian Virtual Dedicated Server (VDS), operating in pre-cutover mode.

---

## 2. Server Architecture & Host Layout
- **Target Profile:** Debian GNU/Linux 13 (trixie) x86_64, 1 vCPU AMD Epyc, 2 GB RAM, 20 GB SSD.
- **Directory Layout:**
  ```text
  /srv/technoreboot/
    ├── app/       # Clean Git clone of origin/main
    ├── data/      # Persistent mutable business data
    │   ├── db/            # SQLite database (technoreboot.db)
    │   ├── storage/       # Product media files
    │   ├── auth/          # Restored CA, server certs, and client registry
    │   ├── avito-module/  # Avito session storage and cookies
    │   └── backups/       # Local and remote backup archives
    ├── secrets/   # Production configuration and server TLS keys (mode 0600)
    │   ├── production.env
    │   ├── server.crt
    │   └── server.key
    └── deploy/    # Transferred backup packages and staging tools
  ```

---

## 3. Deployment Procedure
1. **Initial SSH Key Bootstrap:**
   - Public key from operator workstation (`~/.ssh/id_ed25519.pub`) appended to `/root/.ssh/authorized_keys`.
   - Key authentication verified; passwords discarded and never persisted to logs, history, or git.
2. **Environment & Dependency Installation:**
   - Debian packages: `curl`, `ca-certificates`, `git`, `python3-cryptography`, `nftables`.
   - Swap space: 2 GB swapfile `/swapfile` enabled to prevent OOM during multi-service container builds.
   - Official Docker CE: Docker Engine `29.8.0` and Docker Compose plugin `v5.5.1` installed from Docker apt repository.
3. **Repository Deployment:**
   - Repository cloned directly via Git from `https://github.com/apc90210/tbootit.git` into `/srv/technoreboot/app`.
   - Verified exact commit match with local `origin/main`.
4. **State Restoration:**
   - Fresh backup archive transferred via SCP to `/srv/technoreboot/deploy/`.
   - SHA256 checksum verified matching.
   - State restored via `scripts/bootstrap_restore.py --skip-containers`.
   - Verified that client CA and OWNER credentials are preserved without regeneration.
5. **Firewall & Security Hardening:**
   - `nftables` configured to allow only ports 22, 80, 443, and Docker bridge traffic.
   - Host port exposure on internal microservices strictly prohibited.
6. **Container Build & Verification:**
   - Images built deterministically from source on the VDS.
   - Stack booted and verified healthy via Docker healthchecks.
   - HTTPS mTLS authentication and route permissions verified from external workstation.
   - Remote backup creation tested.
7. **Split-Brain Safety Stop:**
   - Application stack stopped via `docker compose stop` to prevent concurrent write split-brain until final cutover.

# ТехноРебут — Production Debian Deployment Runbook

## 1. Scope & Warning

This runbook describes the deterministic deployment and rollback procedures for ТехноРебут on a Debian 12 (Bookworm) Virtual Dedicated Server (VDS).

> [!IMPORTANT]
> **Pre-deployment Rule:** Do NOT deploy to the real VDS until the Owner explicitly accepts Stage 08B-R1. This document serves as the operational baseline and audit reference.

---

## 2. Server Prerequisites & Debian 12 Baseline

- **Hardware Profile:** 1 vCPU, 2 GB RAM, 20 GB SSD storage.
- **Operating System:** Debian 12 (Bookworm) minimal installation with SSH access.
- **System Packages:**
  ```bash
  sudo apt-get update && sudo apt-get install -y \
      ca-certificates \
      curl \
      gnupg \
      lsb-release \
      git \
      ufw \
      fail2ban
  ```

---

## 3. Firewall Configuration (UFW)

Configure minimal public exposure:
```bash
# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH, HTTP redirect, and HTTPS Gateway
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP redirect to HTTPS'
sudo ufw allow 443/tcp comment 'HTTPS Gateway mTLS'

# Enable firewall
sudo ufw --force enable
sudo ufw status verbose
```
All internal application ports (`8000`, `8010`, `8020`, `8030`, `8040`, `6080`) are blocked from external networks.

---

## 4. Docker Engine & Docker Compose Installation

Install official Docker Engine on Debian 12:
```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
sudo systemctl enable --now docker
```

---

## 5. Clone Git Repository

```bash
sudo mkdir -p /srv/technoreboot
sudo chown -R $USER:$USER /srv/technoreboot
cd /srv/technoreboot

git clone https://github.com/apc90210/tbootit.git app
cd /srv/technoreboot/app
```

---

## 6. Directory Layout & Permissions

Create the persistent data directory hierarchy:
```bash
sudo mkdir -p /srv/technoreboot/data/db \
              /srv/technoreboot/data/storage/product_photos \
              /srv/technoreboot/data/auth/ca \
              /srv/technoreboot/data/auth/server \
              /srv/technoreboot/data/auth/certificates \
              /srv/technoreboot/data/avito-module \
              /srv/technoreboot/data/backups \
              /srv/technoreboot/certs

# Set permissions: directories 0750, files 0640, private keys 0600
sudo chown -R $USER:docker /srv/technoreboot/data
sudo chmod -R 0750 /srv/technoreboot/data
```

---

## 7. Configure Production Environment

1. Copy the production template:
   ```bash
   cp deploy/production/env.production.example deploy/production/.env
   chmod 0600 deploy/production/.env
   ```
2. Populate the required variables in `deploy/production/.env`:
   ```ini
   # 1. Hostname
   TECHNOREBOOT_HOSTNAME=crm.technoreboot.ru
   HTTP_PORT=80
   HTTPS_PORT=443

   # 2. Data Root
   TECHNOREBOOT_DATA_ROOT=/srv/technoreboot/data

   # 3. Certificates
   SERVER_TLS_CERT_PATH=/srv/technoreboot/certs/server.crt
   SERVER_TLS_KEY_PATH=/srv/technoreboot/certs/server.key
   CLIENT_CA_CERT_PATH=/srv/technoreboot/data/auth/ca/ca.crt

   # 4. Secrets (Generate with: openssl rand -hex 32)
   APP_ENV=production
   CORE_API_TOKEN=<generated_64_hex_token>
   CART_SESSION_SECRET=<generated_64_hex_secret>
   ```

---

## 8. Data Placement & Disaster Recovery Restore

If migrating from an existing installation or restoring from backup:
```bash
# Using the bootstrap restore script
python3 scripts/bootstrap_restore.py \
    --backup-zip /path/to/TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip \
    --target-data-dir /srv/technoreboot/data \
    --skip-containers
```
Ensure that `technoreboot.db` resides in `/srv/technoreboot/data/db/technoreboot.db` and existing client certificates reside in `/srv/technoreboot/data/auth/`.

---

## 9. Server TLS Certificate Setup

Place public server HTTPS certificate (e.g. from Let's Encrypt / Certbot or custom authority):
```bash
sudo cp /etc/letsencrypt/live/crm.technoreboot.ru/fullchain.pem /srv/technoreboot/certs/server.crt
sudo cp /etc/letsencrypt/live/crm.technoreboot.ru/privkey.pem /srv/technoreboot/certs/server.key

sudo chmod 0644 /srv/technoreboot/certs/server.crt
sudo chmod 0600 /srv/technoreboot/certs/server.key
```

---

## 10. Build and Start Production Stack

```bash
cd /srv/technoreboot/app/deploy/production

# 1. Validate configuration interpolation
docker compose -f docker-compose.prod.yml config

# 2. Build images from source
docker compose -f docker-compose.prod.yml build

# 3. Launch stack in background
docker compose -f docker-compose.prod.yml up -d

# 4. Check status and health
docker compose -f docker-compose.prod.yml ps
```

---

## 11. Verification Checklist

1. **Verify Published Ports**:
   ```bash
   sudo ss -tulpn | grep -E ':(80|443|8000|8010|8020|8030|8040)'
   ```
   *Expect:* Only ports 80 and 443 are listening on public interfaces. Ports 8000–8040 must NOT appear.
2. **Verify HTTP Redirect**:
   ```bash
   curl -I http://crm.technoreboot.ru/
   ```
   *Expect:* `HTTP/1.1 301 Moved Permanently` with `Location: https://crm.technoreboot.ru/`.
3. **Verify mTLS Rejection without Certificate**:
   ```bash
   curl -k https://crm.technoreboot.ru/
   ```
   *Expect:* `403 Forbidden` (`No valid Technoreboot client certificate presented`).
4. **Verify OWNER Access**:
   Import `owner.p12` into client browser and visit `https://crm.technoreboot.ru/`.
   *Expect:* Dashboard, Inventory, Repairs, Avito, Backups, and Certificates all load normally with 200 OK.
5. **Verify USER Access**:
   Import user certificate into another browser profile.
   *Expect:* Inventory loads normally; `/backups` and `/certificates` return 403 Forbidden.

---

## 12. Rollback Procedure

In case a release fails healthchecks or runtime verification:

```bash
cd /srv/technoreboot/app/deploy/production

# 1. Stop current failing stack
docker compose -f docker-compose.prod.yml down

# 2. Switch to previous known good Git commit
cd /srv/technoreboot/app
git checkout <PREVIOUS_STABLE_COMMIT_HASH>

# 3. Rebuild and launch previous stack
cd deploy/production
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 4. Verify health
docker compose -f docker-compose.prod.yml ps
```

*Note on Database:* Since release commits in Stage 08B do not alter the database schema, normal rollbacks do NOT require a database restore. If data corruption occurred, restore `/srv/technoreboot/data` from the pre-release backup ZIP using `scripts/bootstrap_restore.py`.

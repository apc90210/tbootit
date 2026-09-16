# Stage 10D — Parallel Full Clone to New VDS

## Executive Summary
A complete, bit-for-bit verified parallel clone of the TechnoReboot production system has been deployed to the new VDS `144.31.15.88` running Debian 13.
The original production server `144.31.50.134` remains 100% untouched, intact, authoritative, and operational with zero downtime.
Public Let's Encrypt TLS certificate with IP SAN `144.31.15.88` has been issued and configured.
Mutual TLS (mTLS) with the existing TechnoReboot Client CA is enforced.
Packet capture (`target-capture.service`) is armed on the new VDS awaiting the Owner's real non-VPN browser test.

---

## Source
- **SOURCE_IP:** 144.31.50.134
- **SOURCE_HOSTNAME:** atanov821.serv.host
- **SOURCE_OS:** Debian GNU/Linux 13 (trixie)
- **SOURCE_VDS_HEAD:** `37768cb20dc7eca4a9539ce83ab9ba5b379c1232`
- **SOURCE_6_SERVICES_HEALTHY_BEFORE:** true
- **SOURCE_PRODUCTS:** 220
- **SOURCE_SALES:** 6
- **SOURCE_REPAIRS:** 1
- **SOURCE_PHOTOS:** 216
- **SOURCE_EXTERNAL_LISTINGS:** 216
- **SOURCE_AVITO_POST_SALE_TASKS:** 4
- **SOURCE_STORAGE_FILE_COUNT:** 216
- **SOURCE_DB_SCHEMA_SHA:** `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467bbf7e5e21dfd989d21605973a`
- **SOURCE_AUTH_CA_SHA256:** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`

---

## Backup
- **SOURCE_BACKUP_CREATED:** true
- **SOURCE_BACKUP_PATH:** `/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-16_172658.zip`
- **SOURCE_BACKUP_SHA256:** `2e5a95d2309b5ba3ca12eb2b06b9d62eb8a7d61bb6db2f44c2511a203af83eee`
- **SOURCE_BACKUP_QUICK_CHECK:** ok
- **SOURCE_BACKUP_MANIFEST_OK:** true

---

## Target Baseline & Bootstrap
- **TARGET_IP:** 144.31.15.88
- **TARGET_OS:** Debian GNU/Linux 13 (trixie) (Kernel: 6.12.85+deb13-amd64)
- **TARGET_HOSTNAME:** atanov822.serv.host
- **TARGET_CPU:** Intel(R) Xeon(R) CPU E5-2667 v2 @ 3.30GHz (1 vCPU)
- **TARGET_RAM:** 1.9 GiB total (1.7 GiB free)
- **TARGET_DISK_FREE:** 18 GiB free (6% used of 20 GiB)
- **TARGET_DEFAULT_ROUTE:** default via 144.31.15.1 dev ens3 onlink
- **TARGET_MTU:** 1500
- **TARGET_DOCKER_VERSION:** 29.8.1
- **TARGET_COMPOSE_VERSION:** v5.5.1
- **TARGET_CODE_HEAD:** `37768cb20dc7eca4a9539ce83ab9ba5b379c1232`
- **CODE_HEAD_MATCH:** true

---

## Restored Data
- **TARGET_PRODUCTS:** 220
- **TARGET_SALES:** 6
- **TARGET_REPAIRS:** 1
- **TARGET_PHOTOS:** 216
- **TARGET_EXTERNAL_LISTINGS:** 216
- **TARGET_AVITO_POST_SALE_TASKS:** 4
- **TARGET_STORAGE_FILE_COUNT:** 216
- **TARGET_DB_SCHEMA_SHA:** `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467bbf7e5e21dfd989d21605973a`
- **TARGET_DB_QUICK_CHECK:** ok
- **TARGET_AUTH_CA_SHA256:** `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`
- **SOURCE_TARGET_DATA_INVARIANTS_MATCH:** true

---

## TLS / Security
- **NEW_SERVER_CERT_VALID_FOR_144_31_15_88:** true
  - Issuer: Let's Encrypt (`C=US, O=Let's Encrypt, CN=YE2`)
  - SAN: `IP Address:144.31.15.88`
  - Profile: shortlived (valid until 2026-09-23)
  - Auto-renewal: `certbot.timer` active + `/etc/letsencrypt/renewal-hooks/deploy/technoreboot_reload.sh`
- **CLIENT_CA_SAME_AS_SOURCE:** true (`a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`)
- **MTLS_REQUIRED:** true (Requests without client certificate rejected with HTTP 403 Forbidden)
- **HTTP_80_REDIRECT:** true (Redirects with 301 to `https://144.31.15.88/`)
- **INTERNAL_PORTS_PRIVATE:** true (No internal ports exposed on host; only gateway 80 and 443 published)
- **SSH_KEY_LOGIN_OK:** true (Owner key configured, password login disabled for automated tasks)

---

## Runtime Health & Smoke Verification
- **TARGET_6_SERVICES_HEALTHY:** true
  - `technoreboot-prod-core`: Healthy
  - `technoreboot-prod-inventory-sales`: Healthy
  - `technoreboot-prod-repairs`: Healthy
  - `technoreboot-prod-avito`: Healthy
  - `technoreboot-prod-admin-shell`: Healthy
  - `technoreboot-prod-gateway`: Healthy
- **ROOT_OK:** true (HTTP 200)
- **PRODUCTS_OK:** true (HTTP 200)
- **SALES_OK:** true (HTTP 200)
- **REPAIRS_OK:** true (HTTP 200)
- **AVITO_EXTENSION_OK:** true (HTTP 200, version 0.2.62 verified)
- **AVITO_POST_SALE_OK:** true (HTTP 200)
- **HELP_OK:** true (HTTP 200)
- **USER_MANUAL_OK:** true (HTTP 200)
- **EXTENSION_HASH_MATCH:** true (`1cf0c2d733b801e00d81e4563a0f24c2c3a9b46f99053c33b106045b95cc2ae9`)
- **MANUAL_PDF_HASH_MATCH:** true (`50ddeedeb4f93d2ea164ce57218a49cf6318ad2557a90c9266995dc8d0589b9e`)
- **AUTO_AVITO_DEACTIVATION_DISABLED:** true (manual-only deactivation preserved)
- **NO_DUPLICATE_EXTERNAL_MUTATION_WORKER:** true

---

## Side-by-Side Invariant Verification

| Metric | Source (`144.31.50.134`) | Target (`144.31.15.88`) | Parity Match |
| :--- | :--- | :--- | :--- |
| **Git HEAD** | `37768cb20dc7eca4a9539ce83ab9ba5b379c1232` | `37768cb20dc7eca4a9539ce83ab9ba5b379c1232` | **YES** |
| **DB Schema SHA** | `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467b...` | `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467b...` | **YES** |
| **DB Quick Check** | `ok` | `ok` | **YES** |
| **Products Count** | 220 | 220 | **YES** |
| **Sales Count** | 6 | 6 | **YES** |
| **Repair Orders** | 1 | 1 | **YES** |
| **Product Photos** | 216 | 216 | **YES** |
| **External Listings** | 216 | 216 | **YES** |
| **Avito Tasks** | 4 | 4 | **YES** |
| **Storage Files** | 216 | 216 | **YES** |
| **Client CA SHA** | `a9b4d288cddf74f6337848a833240efdfba412e...` | `a9b4d288cddf74f6337848a833240efdfba412e...` | **YES** |
| **Extension ZIP SHA** | `1cf0c2d733b801e00d81e4563a0f24c2c3a9b46...` | `1cf0c2d733b801e00d81e4563a0f24c2c3a9b46...` | **YES** |
| **User Manual PDF SHA**| `50ddeedeb4f93d2ea164ce57218a49cf6318ad2...` | `50ddeedeb4f93d2ea164ce57218a49cf6318ad2...` | **YES** |

---

## Source Production Safety Verification (After Clone)
- **SOURCE_6_SERVICES_HEALTHY_AFTER:** true (all 6 Up 34+ hours, healthy)
- **SOURCE_BUSINESS_DATA_UNCHANGED:** true (220 products, 6 sales, 1 repair, 216 photos, 216 listings, 4 tasks, 216 storage files)
- **SOURCE_DB_QUICK_CHECK_AFTER:** ok
- **SOURCE_STILL_AUTHORITATIVE:** true (No cutover performed)

---

## New IP Owner Test Status
- **OWNER_REAL_NONVPN_TEST_PERFORMED:** PENDING_OWNER_TEST
- **PACKET_CAPTURE_ARMED:** `target-capture.service` active on `144.31.15.88` capturing `tcp port 80 or tcp port 443` into `/tmp/stage10d_target_test.pcap`
- **ACTION FOR OWNER:**
  1. Turn OFF VPN (Amnezia).
  2. Open in browser: `https://144.31.15.88/` (using existing Owner client certificate).
  3. Inform the agent when the attempt is made.

---

## Conclusion
- **NEW_IP_SOLVES_NONVPN_ACCESS:** PENDING_OWNER_NONVPN_BROWSER_TEST
- **READY_FOR_SEPARATE_CUTOVER_STAGE:** false (Awaiting owner test results)

FINAL_STATUS: TECHNOREBOOT_STAGE10D_NEW_VDS_CLONE_READY_ARMED_FOR_OWNER_TEST

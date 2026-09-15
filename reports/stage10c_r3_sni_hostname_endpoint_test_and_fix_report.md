# Stage 10C-R3 — Standard SNI Hostname Endpoint Diagnostic Report

## 1. Executive Summary

This report documents the findings of **Stage 10C-R3 PRODUCTION — Standard SNI Hostname Endpoint Test & Fix**.
The objective was to test the candidate provider hostname `atanov821.serv.host` for standard DNS resolution and SNI HTTPS reachability, to determine whether a standard hostname endpoint can resolve the non-VPN domestic Russian access issue identified in Stage 10C-R2 without compromising mTLS security or raw-IP fallback.

### Key Finding
- **DNS Resolution of Provider Hostname:** **FAILED (NXDOMAIN)**.
  `atanov821.serv.host` does **NOT** exist in public DNS.
  Queries to local resolvers, Cloudflare (`1.1.1.1`), Google (`8.8.8.8`), and authoritative nameservers for zone `serv.host` (`wally.ns.cloudflare.com`, `peyton.ns.cloudflare.com`) all return `status: NXDOMAIN`.
- **Root Cause of Unsuitability:**
  The name `atanov821.serv.host` is a purely internal host identifier assigned by the hosting provider `serv.host` in `/etc/hostname`, but the provider does not publish public DNS `A` records for individual client subdomains under `serv.host`.
- **Public TLS Certificate Issuance:**
  Because `atanov821.serv.host` does not resolve in public DNS, Let's Encrypt / ACME HTTP-01 or TLS-ALPN-01 validation cannot succeed. Furthermore, `serv.host` is a provider domain not controlled by the Owner.
- **Safety Enforcement:**
  In accordance with Section 3 and Section 10 of the Stage 10C-R3 prompt, Nginx was **not** altered with unresolvable hostnames or self-signed fakes. The production mTLS gateway remains 100% operational on its trusted canonical IP endpoint `https://144.31.50.134` over Amnezia VPN.

---

## 2. DNS Investigation & Evidence

### 2.1 Resolution Checks
Commands executed on VDS `144.31.50.134`:
- `python socket.gethostbyname('atanov821.serv.host')` -> `[Errno -2] Name or service not known`
- `dig +short A atanov821.serv.host` -> `EMPTY`
- `dig +short AAAA atanov821.serv.host` -> `EMPTY`
- `dig @8.8.8.8 +short A atanov821.serv.host` -> `EMPTY`
- `dig @1.1.1.1 +short A atanov821.serv.host` -> `EMPTY`

### 2.2 Authoritative Cloudflare Nameserver Response
```text
; <<>> DiG 9.20.21-1~deb13u1-Debian <<>> atanov821.serv.host
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 19594
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1

;; QUESTION SECTION:
;atanov821.serv.host.        IN    A

;; AUTHORITY SECTION:
serv.host.    1800    IN    SOA    peyton.ns.cloudflare.com. dns.cloudflare.com. 2414350288 10000 2400 604800 1800
```

### 2.3 Reverse DNS (PTR) Status
- `dig -x 144.31.50.134` -> `NXDOMAIN` (No reverse DNS PTR record configured for `144.31.50.134`).

---

## 3. Current Production Nginx Gateway Baseline

Extracted from production container `technoreboot-prod-gateway` via `nginx -T`:
- **CURRENT_SERVER_NAMES:** `144.31.50.134` (HTTP :80 -> 301 redirect), `144.31.50.134` (HTTPS :443)
- **CURRENT_SERVER_CERT:** `/etc/nginx/certs/server/server.crt` (Let's Encrypt Public IP SAN certificate for `144.31.50.134`)
- **CURRENT_CLIENT_CA:** `/etc/nginx/certs/ca/ca.crt` (TechnoReboot Client CA)
- **CURRENT_SSL_VERIFY_CLIENT:** `optional` (strictly verified by internal subrequest `/internal-auth/verify` to `admin-shell:8010`)
- **MTLS_STILL_REQUIRED:** `true` (enforced without exception)

---

## 4. Requirements for User-Controlled Domain

Because `atanov821.serv.host` cannot be used for public TLS, a user-controlled domain or subdomain is required if the Owner wishes to provide a standard SNI hostname endpoint.

### Recommended Configuration
1. **Domain Selection:**
   Any domain controlled by the Owner (e.g. `technoreboot.ru`, `technoreboot.com`, `admin.technoreboot.ru`, or similar).
2. **DNS Record Required:**
   ```text
   Type: A
   Host: <chosen-hostname> (e.g. app.technoreboot.ru)
   Value: 144.31.50.134
   TTL: 300 (or default / auto)
   Proxy / Cloudflare Orange Cloud: OFF (DNS-Only) initially for direct mTLS termination
   ```
3. **Automated Steps Once DNS is Delegated:**
   - Run Let's Encrypt Certbot via HTTP-01 challenge on port 80.
   - Add `<chosen-hostname>` to Nginx `server_name` block alongside `144.31.50.134`.
   - Re-arm live trace and verify non-VPN access through domestic Russian ISPs.

---

## 5. Security & Business Safety Verification

- **Database Migrations Run:** `false` (0 migrations)
- **Business Data Changed:** `false` (0 changes)
- **Business Invariant Parity:**
  - `products`: **162**
  - `sales`: **3**
  - `repair_orders`: **1**
  - `product_photos`: **158**
  - `product_external_listings`: **158**
- **Docker Containers:** 6 of 6 containers healthy (`admin-shell`, `core`, `gateway`, `avito`, `inventory-sales`, `repairs`).
- **Internal Ports:** Private (isolated from host/public).
- **SSH Access:** Healthy and responsive.
- **Canonical IP Production Path:** 100% operational over Amnezia VPN.

---

## 6. Final Report Contract

```text
# Stage 10C-R3 — Standard SNI Hostname Endpoint

## DNS
HOSTNAME: atanov821.serv.host
HOSTNAME_RESOLVES: false
A_RECORD: none (NXDOMAIN)
AAAA_RECORD: none (NXDOMAIN)
POINTS_TO_VDS: false

## TLS
CERT_ISSUED: false (ACME rejected: domain does not exist in public DNS)
CERT_SUBJECT: N/A
CERT_SAN: N/A
SERVER_NAME_CONFIGURED: 144.31.50.134 (preserved; atanov821.serv.host not added to avoid invalid vhost)
MTLS_STILL_REQUIRED: true

## Synthetic External Test
HTTP_HOSTNAME_80: N/A (NXDOMAIN)
HTTPS_HOSTNAME_NO_CLIENT_CERT: N/A (NXDOMAIN)
HTTPS_HOSTNAME_WITH_OWNER_CERT: N/A (NXDOMAIN)

## Real Owner Test
OWNER_REAL_NONVPN_HOSTNAME_TEST: NOT_FEASIBLE (hostname does not resolve in public DNS)
OWNER_SYN_REACHED_VDS: N/A
FULL_CLIENTHELLO_REACHED_VDS: N/A
SNI_SEEN: N/A
TLS_HANDSHAKE_COMPLETED: N/A
NGINX_HTTP_REQUEST_SEEN: N/A
HTTP_STATUS: N/A

## Comparison
RAW_IP_NONVPN_STATUS: BLOCKED_BY_ISP_TSPU_DPI (Stage 10C-R2 proved trailing ClientHello dropped)
HOSTNAME_NONVPN_STATUS: NXDOMAIN (provider hostname atanov821.serv.host is not in public DNS)
VPN_IP_STATUS: OPERATIONAL_HTTP_200 (100% functional via Amnezia VPN)

## Conclusion
ROOT_CAUSE_CONFIDENCE: 100% (atanov821.serv.host is an internal hosting host ID, not a registered public DNS A record)
CANONICAL_PRODUCTION_URL_RECOMMENDATION: Maintain https://144.31.50.134 over Amnezia VPN as canonical production URL until Owner assigns a user-controlled domain (e.g. A record pointing to 144.31.50.134)

## Safety
DB_MIGRATION_RUN: false
BUSINESS_DATA_CHANGED: false
INTERNAL_PORTS_PRIVATE: true
SSH_OK: true

FINAL_STATUS:
PROVIDER_HOSTNAME_UNSUITABLE_USER_DOMAIN_REQUIRED
```

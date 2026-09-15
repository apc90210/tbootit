# TECHNOREBOOT — Stage 10C-R3 PRODUCTION
## Standard hostname/SNI endpoint test and fix for non-VPN access

Project: ТехноРебут
LOCAL workspace: C:\tbootit
Production VDS: 144.31.50.134
Candidate provider hostname: atanov821.serv.host
Stage: Stage 10C-R3 — Standard SNI Hostname Endpoint

# 0. OWNER CONTEXT

Stage10C-R2 real packet capture proved:

- Owner non-VPN TCP reaches VDS.
- SYN/SYN-ACK/ACK succeeds.
- TLS ClientHello begins arriving.
- Full TLS ClientHello does not complete.
- nginx never reaches HTTP layer.
- VPN path works.

Important correction:
The packet capture proves a path-specific TLS failure, but it does NOT by itself prove that the exact blocker is TSPU/RKN/ECH/PQ.
Do not overclaim the filtering mechanism unless independently demonstrated.

The most practical next test is to stop using raw-IP HTTPS as the only production entry point and provide a normal hostname with standard SNI.

Goal:

https://<hostname>
-> normal DNS resolution
-> normal SNI
-> valid public server certificate
-> existing TechnoReboot mTLS client certificate requirement
-> TechnoReboot UI

The existing IP endpoint must remain available as fallback.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10C_R3_SNI_HOSTNAME_ENDPOINT_TEST_AND_FIX_PROMPT.md

to:

C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10C_R3_SNI_HOSTNAME_ENDPOINT_TEST_AND_FIX_PROMPT.md

# 2. SAFETY

Allowed:
- DNS inspection;
- nginx gateway config changes;
- server TLS certificate issuance/install;
- HTTP-01 ACME challenge on port 80;
- adding hostname to server_name;
- preserving existing mTLS.

Forbidden:
- disabling client certificate requirement;
- changing business DB;
- copying LOCAL DB/media/auth to VDS;
- removing IP endpoint;
- changing unrelated firewall rules;
- broad DNS changes without proof.

Before config changes:
- backup nginx config;
- record rollback;
- run nginx -t.

# 3. VERIFY PROVIDER HOSTNAME FIRST

Check atanov821.serv.host using:

dig +short A atanov821.serv.host
dig +short AAAA atanov821.serv.host
dig +trace atanov821.serv.host

Also use an independent public resolver if practical.

Record:

HOSTNAME_RESOLVES:
A_RECORD:
AAAA_RECORD:
POINTS_TO_144_31_50_134:
DNS_TTL:

If it does NOT resolve to 144.31.50.134, do not force nginx changes.

Return:
PROVIDER_HOSTNAME_UNSUITABLE

and specify that Owner needs a real domain/subdomain pointing to 144.31.50.134.

# 4. VERIFY HTTP REQUEST BY HOSTNAME

Before TLS changes, test:

curl -v http://atanov821.serv.host/

and inspect VDS nginx logs.

Expected:
- request reaches VDS;
- nginx can see Host header atanov821.serv.host.

If DNS resolves but HTTP does not reach VDS, diagnose separately before ACME.

# 5. INSPECT CURRENT NGINX TLS CONFIG

Inside production gateway inspect effective config with nginx -T.

Record:

CURRENT_SERVER_NAMES:
CURRENT_SERVER_CERT:
CURRENT_CLIENT_CA:
CURRENT_SSL_VERIFY_CLIENT:

Required security invariant:
ssl_verify_client remains required
or the existing equivalent mTLS policy.

# 6. OBTAIN A VALID SERVER CERTIFICATE FOR HOSTNAME

If atanov821.serv.host resolves correctly and public ACME issuance is allowed:

Prefer:
- Let's Encrypt HTTP-01 on port 80;
- or existing ACME tooling already used in project.

Do not expose the app anonymously.

HTTP challenge may be served on port 80 while normal HTTP traffic continues to redirect to HTTPS.

Record:

CERT_ISSUED:
CERT_SUBJECT:
CERT_SAN:
CERT_NOT_AFTER:

If ACME issuance for provider-owned hostname is rejected:
- do not work around CA policy;
- stop and report that a user-controlled domain is required.

# 7. CONFIGURE NORMAL SNI ENDPOINT

Configure nginx so both remain valid:

https://144.31.50.134
https://atanov821.serv.host

For hostname:
- server_name atanov821.serv.host;
- use valid public server certificate for hostname;
- preserve required TechnoReboot client certificate verification;
- proxy to same internal app.

Do not create a second anonymous/unprotected vhost.

# 8. VERIFY TLS WITH AND WITHOUT CLIENT CERT

From external test nodes:

Without client certificate:
https://atanov821.serv.host

Expected:
- DNS resolves;
- TLS completes normally;
- server presents hostname-valid certificate;
- request is rejected by mTLS (e.g. 400/403 depending current nginx policy);
- no timeout/reset.

With valid Owner client certificate:
Expected HTTP 200.

# 9. REAL OWNER NON-VPN TEST — MANDATORY

Before final acceptance:

1. Arm tcpdump + nginx access/error log watch.
2. Ask Owner only:
   Отключи Amnezia и открой:
   https://atanov821.serv.host
3. Capture:
   - source SYN;
   - complete ClientHello;
   - SNI value;
   - server TLS response;
   - client certificate exchange;
   - nginx HTTP request.

Required:
OWNER_REAL_NONVPN_HOSTNAME_TEST: PASS

If this works while raw IP still fails:
conclude:
STANDARD_SNI_HOSTNAME_PATH_SOLVES_NONVPN_ACCESS

and recommend hostname as canonical production URL.

# 10. IF PROVIDER HOSTNAME IS UNSUITABLE

If atanov821.serv.host cannot be used for proper public TLS:
- do not fake it;
- report exact reason.

Then prepare exact requirements for a user-controlled domain:

A record: <chosen-hostname> -> 144.31.50.134
No proxy/CDN required initially
TTL: normal/default

Example only:
app.technoreboot.ru -> 144.31.50.134

Do not buy/register anything.

# 11. SECURITY REGRESSION

Verify:
- mTLS still required;
- 80 only redirects / serves ACME challenge;
- 443 app is not anonymous;
- SSH unchanged;
- DB/internal ports private;
- IP endpoint still works over VPN.

# 12. BUSINESS SAFETY

No DB migration.

Verify counts unchanged:
- products
- sales
- repair_orders
- product_photos
- product_external_listings

# 13. DOCUMENTATION

Create:
reports/stage10c_r3_sni_hostname_endpoint_test_and_fix_report.md

Update:
docs/production_status.md
logs/<current-date>.md

# 14. FINAL REPORT CONTRACT

Return:

# Stage 10C-R3 — Standard SNI Hostname Endpoint

## DNS
HOSTNAME:
HOSTNAME_RESOLVES:
A_RECORD:
AAAA_RECORD:
POINTS_TO_VDS:

## TLS
CERT_ISSUED:
CERT_SUBJECT:
CERT_SAN:
SERVER_NAME_CONFIGURED:
MTLS_STILL_REQUIRED:

## Synthetic External Test
HTTP_HOSTNAME_80:
HTTPS_HOSTNAME_NO_CLIENT_CERT:
HTTPS_HOSTNAME_WITH_OWNER_CERT:

## Real Owner Test
OWNER_REAL_NONVPN_HOSTNAME_TEST:
OWNER_SYN_REACHED_VDS:
FULL_CLIENTHELLO_REACHED_VDS:
SNI_SEEN:
TLS_HANDSHAKE_COMPLETED:
NGINX_HTTP_REQUEST_SEEN:
HTTP_STATUS:

## Comparison
RAW_IP_NONVPN_STATUS:
HOSTNAME_NONVPN_STATUS:
VPN_IP_STATUS:

## Conclusion
ROOT_CAUSE_CONFIDENCE:
CANONICAL_PRODUCTION_URL_RECOMMENDATION:

## Safety
DB_MIGRATION_RUN: false
BUSINESS_DATA_CHANGED: false
INTERNAL_PORTS_PRIVATE:
SSH_OK:

FINAL_STATUS:
<one of>
TECHNOREBOOT_STAGE10C_R3_HOSTNAME_NONVPN_FIXED
PROVIDER_HOSTNAME_UNSUITABLE_USER_DOMAIN_REQUIRED
BLOCKED_TLS_HOSTNAME_PATH

Do not claim fixed unless the Owner's real non-VPN browser test succeeds.

# 15. STOP

STOP after real Owner non-VPN hostname test and evidence-based conclusion.

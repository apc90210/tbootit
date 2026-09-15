# TECHNOREBOOT — Stage 10C PRODUCTION
## Urgent diagnosis and fix: production site works via Amnezia VPN but not from ordinary Russian providers

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Production URL:** `https://144.31.50.134`  
**Stage:** `Stage 10C — Russia Reachability Diagnostic & Safe Fix`

# 0. OWNER PROBLEM

Critical production networking issue:

```text
When client traffic goes through Amnezia VPN:
https://144.31.50.134 works

When client uses ordinary Russian ISP/mobile provider:
connection fails / site is inaccessible
```

Earlier observed behavior:

```text
WITHOUT VPN:
TCP to 144.31.50.134:80 connects,
but HTTP GET is reset / connection reset

WITH Amnezia:
TCP works,
HTTP GET / on port 80 returns nginx 301 -> https://144.31.50.134/
```

Important implication:

- mTLS/client certificate cannot explain the HTTP port 80 reset, because TLS has not started yet;
- the issue is likely at or before nginx:
  - host firewall;
  - nftables/iptables/UFW/firewalld;
  - Docker FORWARD/DOCKER-USER chain;
  - fail2ban/ipset/nft set;
  - source-IP allowlist;
  - GeoIP/ASN block;
  - hosting-provider firewall/security group;
  - anti-DDoS/filtering;
  - asymmetric routing / policy routing;
  - nginx `allow/deny`/geo/map rules;
  - another packet filter before nginx.

Goal:

```text
Production must remain protected by mTLS
BUT
ports 80/443 must be reachable from normal Russian providers too,
not only from Amnezia/VPN source IPs.
```

This is a REAL production networking task.

Do NOT touch business DB/data.

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10C_PRODUCTION_RUSSIA_ACCESS_DIAGNOSTIC_AND_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10C_PRODUCTION_RUSSIA_ACCESS_DIAGNOSTIC_AND_FIX_PROMPT.md`

# 2. SAFETY RULES

Allowed:
- inspect networking/firewall/nginx/docker;
- change network/firewall/nginx rules only when root cause is demonstrated;
- reload nginx/firewall safely;
- verify mTLS remains enforced.

Forbidden:
- modify production DB;
- modify products/sales/repairs;
- copy LOCAL DB/media/auth to VDS;
- disable mTLS;
- expose admin endpoints without certificate;
- broadly open unrelated ports;
- reboot VDS unless absolutely necessary and explicitly justified.

Before any firewall/network write:
- save current configuration;
- record rollback command/file;
- keep SSH access safe;
- never flush all firewall rules blindly.

# 3. BASELINE — PRODUCTION HEALTH

Record:

```text
VDS_HEAD:
LIVE_6_SERVICES_HEALTHY:
PUBLIC_HTTP_80_LISTENING:
PUBLIC_HTTPS_443_LISTENING:
NGINX_GATEWAY_HEALTHY:
```

On VDS inspect:

```bash
ss -lntup
docker ps
docker logs --tail 100 technoreboot-prod-gateway
```

Confirm which process/container owns ports 80 and 443.

# 4. CAPTURE CURRENT SERVER NETWORK CONFIG

Collect and save:

```text
ip addr
ip route
ip rule
sysctl net.ipv4.ip_forward
```

Inspect all relevant packet filtering systems:

```text
nft list ruleset
iptables-save
ip6tables-save
ufw status verbose
firewall-cmd --list-all
```

Run only commands that exist.

Inspect Docker-specific chains:

```text
DOCKER
DOCKER-USER
FORWARD
INPUT
```

Look specifically for:
- source-IP allowlists;
- DROP/REJECT/RESET actions;
- `ct state`;
- rate limits;
- geo/ASN sets;
- VPN-specific source networks;
- rules matching 80/443;
- rules matching Russian address ranges or non-VPN traffic;
- stale temporary rules from previous setup.

Record exact suspicious rules with counters.

# 5. INSPECT FAIL2BAN / IP SETS / BLOCKLISTS

Check:

```text
fail2ban-client status
fail2ban-client status <jail>
ipset list
nft sets
```

Look for:
- current owner/client public IPs;
- broad CIDR blocks;
- Russian ISP ranges;
- accidental permanent bans;
- nginx badbot/recidive/sshd rules touching 80/443.

Do not unban broadly until root cause is known.

# 6. INSPECT NGINX / GATEWAY CONFIG

Inspect the live effective nginx config:

```bash
nginx -T
```

or inside gateway container if nginx is containerized.

Search for:

```text
allow
deny
geo
map
limit_req
limit_conn
return 444
proxy_protocol
real_ip
set_real_ip_from
if ($remote_addr ...)
```

Confirm intended behavior:

```text
HTTP :80 -> 301 HTTPS
HTTPS :443 -> TLS + required client certificate (mTLS)
```

There must NOT be an allowlist that permits only Amnezia/VPN source addresses.

Also inspect whether nginx itself is logging the failed non-VPN requests.

# 7. DETERMINE WHERE THE RESET OCCURS

This is the most important diagnostic step.

Run packet capture on VDS while performing external requests:

```bash
tcpdump -ni any 'tcp port 80 or tcp port 443'
```

Use a bounded capture, e.g. timeout 30-60 seconds.

From LOCAL workstation, test current path:

```text
curl -v http://144.31.50.134/
curl -vk https://144.31.50.134/
Test-NetConnection 144.31.50.134 -Port 80
Test-NetConnection 144.31.50.134 -Port 443
```

Record local public source IP if safely obtainable.

If current workstation happens to be behind Amnezia, record that honestly.

Correlate:

### Case A
Packets from failing source NEVER reach VDS:
```text
root cause is upstream of host firewall
```
Likely:
- provider firewall/security group;
- hoster anti-DDoS/filtering;
- routing issue.

### Case B
SYN reaches VDS but host sends RST/REJECT before nginx:
```text
root cause is host firewall / Docker chain / kernel rule
```

### Case C
Request reaches nginx and nginx closes/resets:
```text
root cause is nginx configuration/rate-limit/allow-deny
```

### Case D
443 reaches nginx but TLS fails:
```text
separate TLS/mTLS issue
```

Do not guess. Determine which layer actually drops/resets.

# 8. CHECK HOSTING-PROVIDER FIREWALL / CONTROL-PLANE CONFIG

Inspect all server-side files/scripts/docs in repo that may configure host firewall.

Search repository for:

```text
nft
iptables
ufw
firewall
allow
deny
144.31.50.134
Amnezia
VPN
80
443
```

Inspect production setup scripts and historical logs.

If hoster provides a firewall/security-group API or CLI already configured on the VDS, inspect it.

If provider-level filtering cannot be read from SSH:
- prove that packets from failing ISP do not reach VDS with tcpdump;
- report `UPSTREAM_FILTERING_PROVEN`;
- identify the hosting provider/control-panel setting that must be checked;
- do not falsely modify local firewall.

# 9. SAFE FIX — ONLY AFTER ROOT CAUSE IS PROVEN

Apply the smallest possible fix.

Examples:

## If nftables/iptables source allowlist is wrong
Change only 80/443 reachability rule so:

```text
TCP 80: allowed from Internet
TCP 443: allowed from Internet
```

Keep:
- SSH restrictions as-is;
- mTLS at nginx;
- unrelated ports closed.

## If fail2ban accidentally blocks broad ranges
Remove/fix the offending jail/filter only.

## If nginx has source allow/deny
Remove source-network restriction from 80/443,
but keep:

```text
ssl_verify_client on;
```

or current equivalent mTLS enforcement.

## If Docker DOCKER-USER chain blocks
Correct only the relevant 80/443 path.

## If provider firewall/security group blocks
Change provider rule only if agent has a supported, auditable method.
Otherwise return the exact required control-panel action.

# 10. FIREWALL CONFIG PERSISTENCE

If any rule is changed, ensure it survives reboot.

Record:

```text
FIREWALL_BACKUP_PATH:
FIREWALL_CHANGE:
PERSISTENCE_METHOD:
ROLLBACK_METHOD:
```

Do not leave a one-off temporary iptables rule as the final fix.

# 11. VERIFY FROM MULTIPLE NETWORK PATHS

After fix, test:

## A. Server-side
```text
curl localhost / container health
```

## B. Current workstation path
```text
HTTP 80
HTTPS 443
```

## C. Amnezia/VPN path if available
Confirm it still works.

## D. Non-VPN Russian ISP path
This is mandatory for final acceptance.

If agent cannot switch the Owner's network itself:
- prepare a 30-second tcpdump/log watch;
- ask Owner for only one action:
  `Открой https://144.31.50.134 без VPN`
- capture evidence;
- continue immediately after.

Do not make Owner run terminal commands unless there is no alternative.

# 12. EXPECTED FINAL NETWORK BEHAVIOR

Without client certificate:

```text
http://144.31.50.134/
-> reachable
-> 301 redirect to HTTPS

https://144.31.50.134/
-> reachable
-> denied because client certificate is missing/invalid
```

With valid TechnoReboot client certificate:

```text
https://144.31.50.134/
-> 200
```

This must work:
- through Amnezia;
- without Amnezia from ordinary Russian ISP/mobile provider.

# 13. SECURITY REGRESSION

After fix verify:

```text
SSH exposure unchanged
DB port not publicly exposed
internal module ports not publicly exposed
mTLS still required
80 only redirects
443 does not become anonymous/public app access
```

Run:

```text
ss -lntup
nft/iptables final dump
nginx effective config
```

# 14. BUSINESS DATA SAFETY

Verify no application data changed due to this task:

```text
PRODUCT_COUNT_BEFORE == PRODUCT_COUNT_AFTER
SALES_COUNT_BEFORE == SALES_COUNT_AFTER
REPAIRS_COUNT_BEFORE == REPAIRS_COUNT_AFTER
```

No DB migration.

# 15. DOCUMENTATION

Create:

```text
reports/stage10c_production_russia_access_diagnostic_and_fix_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Document:
- exact root cause;
- exact layer where reset occurred;
- exact rule/config changed;
- before/after tests;
- rollback path.

# 16. FINAL REPORT CONTRACT

Return:

```text
# Stage 10C — Production Russia Reachability Diagnostic & Fix

## Symptom
VPN_PATH_WORKED_BEFORE:
NON_VPN_RUSSIAN_PATH_FAILED_BEFORE:
HTTP_80_RESET_CONFIRMED:
HTTPS_443_FAILURE_CONFIRMED:

## Root Cause
FAILURE_LAYER:
ROOT_CAUSE:
EVIDENCE:
PACKETS_FROM_FAILING_SOURCE_REACHED_VDS:
NGINX_SAW_FAILING_REQUEST:
OFFENDING_RULE_OR_CONFIG:

## Fix
CHANGE_APPLIED:
FILES_OR_RULES_CHANGED:
FIREWALL_BACKUP_PATH:
PERSISTENCE_METHOD:
ROLLBACK_METHOD:

## Verification
HTTP_80_NON_VPN:
HTTPS_443_NON_VPN_WITHOUT_CERT:
HTTPS_443_NON_VPN_WITH_VALID_CERT:
HTTP_80_VPN:
HTTPS_443_VPN_WITH_VALID_CERT:
NGINX_301_ON_HTTP:
MTLS_STILL_REQUIRED:

## Security
SSH_POLICY_UNCHANGED:
INTERNAL_PORTS_STILL_PRIVATE:
DB_NOT_PUBLIC:
UNRELATED_FIREWALL_RULES_UNCHANGED:

## Business Safety
DB_MIGRATION_RUN: false
PRODUCT_COUNT_UNCHANGED:
SALES_COUNT_UNCHANGED:
REPAIRS_COUNT_UNCHANGED:

FINAL_STATUS:
TECHNOREBOOT_STAGE10C_RUSSIA_ACCESS_FIXED
```

If packets from the failing Russian provider never reach the VDS and no host-side rule explains it, return:

```text
FINAL_STATUS:
BLOCKED_UPSTREAM_PROVIDER_FILTERING

NEXT_REQUIRED_ACTION:
<exact provider firewall / anti-DDoS / hosting support action>
```

Do not claim fixed unless a real non-VPN test succeeds.

# 17. STOP

After real verification from non-VPN Russian connectivity:

STOP.

Do not start another feature.

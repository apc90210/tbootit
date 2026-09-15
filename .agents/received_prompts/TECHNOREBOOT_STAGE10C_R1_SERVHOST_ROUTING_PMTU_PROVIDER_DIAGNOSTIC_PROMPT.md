# TECHNOREBOOT — Stage 10C-R1 PRODUCTION
## Deep provider-routing / PMTU / serv.host diagnostic after Russia-access fix

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Hostname:** `atanov821.serv.host`  
**Provider:** `serv.host`  
**Stage:** `Stage 10C-R1 — serv.host Routing / PMTU / Provider Diagnostic`

# 0. OWNER CONTEXT

Stage10C already applied a host-side networking fix:
- allow ICMP / IPv6-ICMP in nftables;
- enable `net.ipv4.tcp_mtu_probing=1`;
- add MSS clamping in forward chain;
- preserve mTLS;
- preserve production data.

New provider/network information from the VDS panel:

```text
Public IPv4: 144.31.50.134
Network: Основная сеть
Netmask: 255.255.255.255 (/32)
Gateway: 100.65.65.65
Hostname: atanov821.serv.host
```

Important:
- `100.65.65.65` is inside `100.64.0.0/10` shared-address space.
- A public `/32` routed through a shared/private transit gateway can be legitimate provider architecture.
- Do NOT assume this means CGNAT.
- Do NOT assume the previous PMTU explanation is definitely complete.

Goal:
**independently verify the real network topology and determine whether there is any remaining provider-side routing, MTU, anti-DDoS, asymmetric-routing, or source-filtering issue that could explain why Russian non-VPN access historically failed while Amnezia worked.**

If no remaining problem exists, prove it and make no unnecessary changes.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10C_R1_SERVHOST_ROUTING_PMTU_PROVIDER_DIAGNOSTIC_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10C_R1_SERVHOST_ROUTING_PMTU_PROVIDER_DIAGNOSTIC_PROMPT.md`

# 2. SAFETY

This is a production network diagnostic.

Allowed:
- inspect routes, neighbors, MTU, nftables, sysctl, nginx, Docker network;
- packet capture;
- external reachability tests;
- provider/public routing research;
- small reversible network fixes only if root cause is demonstrated.

Forbidden:
- DB migration;
- business-data changes;
- replacing DB/media/auth;
- disabling mTLS;
- changing SSH policy unless absolutely required;
- opening unrelated ports;
- rebooting the VDS without explicit need.

Before changing any live network rule:
1. save current configuration;
2. record rollback command;
3. verify SSH recovery path;
4. make the smallest change possible.

# 3. VERIFY CURRENT NETWORK TOPOLOGY

On VDS collect:

```bash
ip -br addr
ip addr show
ip route show table all
ip rule show
ip neigh show
ip link show
ip -d link show
```

Record:

```text
PUBLIC_IP:
PUBLIC_PREFIX:
DEFAULT_ROUTE:
DEFAULT_GATEWAY:
EGRESS_INTERFACE:
INTERFACE_MTU:
GATEWAY_NEIGHBOR_STATE:
```

Explicitly determine how a `/32` address reaches gateway `100.65.65.65`.

Look for:
- on-link route;
- host route to gateway;
- point-to-point semantics;
- provider-specific routing;
- policy-routing tables;
- source routing.

Do not call it broken merely because the gateway is outside the public IP subnet.

# 4. VERIFY CURRENT FIREWALL / PMTU FIX

Collect current:

```bash
nft list ruleset
sysctl net.ipv4.tcp_mtu_probing
sysctl net.ipv4.ip_no_pmtu_disc
sysctl net.ipv4.tcp_ecn
sysctl net.ipv4.tcp_sack
sysctl net.ipv4.tcp_window_scaling
```

Confirm persistence files:

```text
/etc/nftables.conf
/etc/sysctl.d/99-technoreboot-pmtu.conf
```

Verify:
- ICMP is still permitted;
- 80/443 are allowed;
- unrelated ports remain closed;
- MSS clamp is actually attached to the packet path used by Docker/nginx;
- `tcp_mtu_probing=1` survived.

Important:
**Do not simply trust Stage10C report. Re-read live config.**

# 5. VERIFY REAL PATH MTU

Determine effective MTU to several destinations.

Use available tools such as:

```bash
tracepath
ping -M do -s <size>
ping -M want -s <size>
```

If missing, install only a lightweight standard networking package if safe.

Test representative targets:
- at least one Russian endpoint;
- at least one non-Russian endpoint.

Determine:

```text
VDS_INTERFACE_MTU:
PATH_MTU_RUSSIA:
PATH_MTU_OTHER:
```

Try to establish whether the route genuinely requires an MTU below 1500.

Do not invent a 1420/1460 value unless measured.

# 6. VERIFY TCP MSS BEHAVIOR

Capture SYN/SYN-ACK traffic on 80/443:

```bash
tcpdump -ni <iface> -vv 'tcp port 80 or tcp port 443'
```

Inspect negotiated MSS from:
- Russian test node;
- current Owner connection;
- Amnezia/VPN path if available.

Record:

```text
CLIENT_MSS_RU:
SERVER_MSS_RU:
CLIENT_MSS_VPN:
SERVER_MSS_VPN:
```

Determine whether MSS clamping is actually changing packets and whether it is necessary.

# 7. PROVIDER / ASN / ROUTING ANALYSIS

Identify:
- ASN announcing `144.31.50.134`;
- upstream ASNs;
- anti-DDoS/transit providers;
- prefix announcement status;
- RPKI validity if available.

Use authoritative/public routing sources where possible:
- RIPEstat;
- BGP looking glasses;
- route collectors;
- provider docs.

Record:

```text
ORIGIN_AS:
PREFIX:
RPKI_STATUS:
UPSTREAM_ASNS:
ANTI_DDOS_OR_TRANSIT:
```

Check whether the prefix is selectively reachable or filtered from Russia.

# 8. SERV.HOST-SIDE FEATURES / FIREWALL / ANTI-DDOS

Inspect the provider side as far as possible.

Search existing:
- provider panel configuration;
- server provisioning metadata;
- cloud-init/netplan/network config;
- provider firewall/security-group settings;
- anti-DDoS settings;
- ACL/allowlist options.

If the agent has no authenticated provider API/panel access:
- do not pretend;
- inspect server-visible evidence;
- search public serv.host documentation;
- report any provider-side setting that Owner may need to inspect manually.

Specifically look for:
- source-country filters;
- anti-DDoS profiles;
- protected-IP routing;
- blackhole/scrubbing mode;
- firewall rules applied outside the VM;
- GRE/tunnel/scrubbing networks.

# 9. CHECK ASYMMETRIC ROUTING

Run:

```bash
ip route get <RU_TEST_IP>
ip route get <VPN_TEST_IP>
```

and packet capture.

Verify inbound and outbound traffic uses expected interface/path.

Look for:
- asymmetric path causing stateful firewall drops;
- source address selection issues;
- policy routing mistakes;
- rp_filter behavior.

Collect:

```bash
sysctl net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.default.rp_filter
sysctl net.ipv4.conf.<iface>.rp_filter
```

Do not change rp_filter unless evidence demonstrates a problem.

# 10. CHECK NGINX / TLS PACKET BEHAVIOR

Inspect live nginx effective config.

Confirm:
- HTTP 80 -> 301;
- HTTPS 443 -> mTLS;
- no source-IP allowlist;
- no GeoIP filter;
- no `return 444` based on origin;
- no proxy-protocol mismatch.

Capture a real TLS handshake and confirm whether:
- ServerHello / Certificate / CertificateRequest are delivered;
- retransmissions occur;
- MTU-related loss remains;
- connection closes normally when no client cert.

# 11. TEST FROM RUSSIAN NETWORKS

Use at least two independent Russian test points if available.

Tests:

```text
TCP/80
HTTP/80
TCP/443
HTTPS/443 without client certificate
```

Expected:
- TCP/80 connect;
- HTTP/80 -> 301;
- TCP/443 connect;
- HTTPS/443 -> 403 or mTLS rejection, NOT timeout/reset.

# 12. OWNER REAL NON-VPN TEST — REQUIRED

The final truth test is the Owner's real Russian ISP/mobile path.

If you need the Owner:
- prepare packet capture / nginx access-log watch first;
- then ask only:

```text
Отключи Amnezia и открой:
https://144.31.50.134
```

Do not ask the Owner to run PowerShell/CMD unless absolutely necessary.

While Owner tests, capture:
- source IP;
- SYN/SYN-ACK;
- TLS handshake;
- nginx access/error logs.

If Owner reports success:
- mark real non-VPN validation PASS.

If Owner reports failure:
- correlate the exact packet trace and continue diagnosing.
- Do NOT stop at synthetic check-host success.

# 13. ONLY FIX WHAT IS PROVEN

Possible valid outcomes:

## A. No remaining problem
If routing, PMTU, provider path and real Owner non-VPN test all work:
- make no new networking changes;
- state that Stage10C fix is sufficient.

## B. Host route / MTU issue remains
Apply minimal persistent host fix.

## C. Provider-side filtering proven
Do not alter unrelated VDS firewall.
Report exact provider-side action.

## D. Anti-DDoS / scrubbing issue
Document exact evidence and provider action.

# 14. SECURITY REGRESSION

After any change, verify:

```text
mTLS still required
HTTP 80 only redirects
HTTPS anonymous access denied
SSH policy unchanged
DB/internal module ports private
no broad INPUT ACCEPT rule
no firewall flush left in place
```

# 15. BUSINESS SAFETY

No business DB changes.

Verify counts before/after:

```text
products
sales
repair_orders
product_photos
product_external_listings
```

No migration.

# 16. DOCUMENTATION

Create:

```text
reports/stage10c_r1_servhost_routing_pmtu_provider_diagnostic_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Document:
- actual `/32` routing topology;
- role of gateway `100.65.65.65`;
- measured path MTU;
- whether MSS clamping is active/useful;
- provider ASN/upstream;
- whether provider filtering exists;
- real Owner non-VPN result.

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 10C-R1 — serv.host Routing / PMTU / Provider Diagnostic

## Provider Network
PUBLIC_IP:
PUBLIC_PREFIX:
DEFAULT_GATEWAY:
EGRESS_INTERFACE:
INTERFACE_MTU:
ROUTING_TO_100_65_65_65_EXPLAINED:
ORIGIN_AS:
PREFIX:
RPKI_STATUS:
UPSTREAM_ASNS:

## Host Network
ICMP_ALLOWED:
TCP_MTU_PROBING:
MSS_CLAMP_PRESENT:
MSS_CLAMP_EFFECTIVE:
RP_FILTER_STATE:

## Measurements
PATH_MTU_RUSSIA:
PATH_MTU_OTHER:
CLIENT_MSS_RU:
SERVER_MSS_RU:
TLS_RETRANSMISSIONS_SEEN:
PMTU_BLACKHOLE_STILL_PRESENT:

## Provider-side
PROVIDER_FIREWALL_FOUND:
PROVIDER_GEO_FILTER_FOUND:
ANTI_DDOS_LAYER_FOUND:
UPSTREAM_FILTERING_PROVEN:

## Real Tests
RU_TEST_NODE_HTTP_80:
RU_TEST_NODE_HTTPS_443:
VPN_PATH:
OWNER_REAL_NON_VPN_PATH:
PACKETS_REACHED_VDS_FROM_OWNER:
NGINX_SAW_OWNER_REQUEST:

## Changes
CHANGE_APPLIED:
FILES_CHANGED:
ROLLBACK:
PERSISTENCE:

## Security
MTLS_STILL_REQUIRED:
SSH_POLICY_UNCHANGED:
INTERNAL_PORTS_PRIVATE:
DB_NOT_PUBLIC:

## Business Safety
DB_MIGRATION_RUN: false
PRODUCT_COUNT_UNCHANGED:
SALES_COUNT_UNCHANGED:
REPAIRS_COUNT_UNCHANGED:

FINAL_STATUS:
<one of>
TECHNOREBOOT_STAGE10C_R1_NETWORK_CONFIRMED_HEALTHY
TECHNOREBOOT_STAGE10C_R1_ADDITIONAL_FIX_APPLIED
BLOCKED_PROVIDER_SIDE_ACTION_REQUIRED
```

Do not claim healthy without real Owner non-VPN test.

# 18. STOP

STOP after diagnosis/fix and real non-VPN validation.

Do not start another feature.

# TECHNOREBOOT — Stage 10C-R2 PRODUCTION
## Real failing non-VPN path live trace — packet capture, routing correlation, exact root cause

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Production URL:** `https://144.31.50.134`  
**Stage:** `Stage 10C-R2 — Real Non-VPN Live Trace`

# 0. OWNER FACT

Previous Stage10C/10C-R1 synthetic checks are NOT sufficient.

Real Owner result:

```text
WITH Amnezia VPN:
https://144.31.50.134 works fully

WITHOUT Amnezia, through the Owner's real ISP:
site does not open at all
browser cannot reach it
```

Therefore:

```text
Stage10C-R1 is NOT accepted.
Do NOT claim the issue is fixed.
```

The purpose of this stage is to capture the Owner's REAL failing connection live and determine exactly where it dies.

This is not a generic diagnostic.
This must correlate one real failed request from the Owner's non-VPN network with packet capture and server logs.

---

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10C_R2_REAL_NONVPN_LIVE_TRACE_DIAGNOSTIC_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10C_R2_REAL_NONVPN_LIVE_TRACE_DIAGNOSTIC_PROMPT.md`

---

# 2. SAFETY

Allowed:
- tcpdump / packet capture;
- nginx access/error log tail;
- routing inspection;
- nftables counters;
- conntrack inspection;
- traceroute/tracepath/mtr where safe;
- minimal reversible network fix only after root cause is proven.

Forbidden:
- DB changes;
- mTLS disablement;
- broad firewall flush;
- unrelated port opening;
- reboot unless absolutely necessary;
- claiming success based only on check-host synthetic nodes.

Before any network write:
- save config;
- record rollback;
- keep SSH access working.

---

# 3. BASELINE — NO CHANGES YET

Record:

```text
VDS_HEAD:
PUBLIC_IP:
DEFAULT_ROUTE:
DEFAULT_GATEWAY:
EGRESS_INTERFACE:
INTERFACE_MTU:
TCP_MTU_PROBING:
NFTABLES_RULESET_HASH:
LIVE_6_SERVICES_HEALTHY:
```

Record current listeners:

```bash
ss -lntup
```

Record current firewall:

```bash
nft list ruleset
```

Record nginx effective config relevant to 80/443.

No changes yet.

---

# 4. IDENTIFY OWNER'S REAL NON-VPN PUBLIC SOURCE IP

The Owner must NOT be asked to use PowerShell/CMD.

Use browser-accessible methods if possible.

Preferred:
- have Owner open a simple public "what is my IP" page in browser while Amnezia is OFF;
- or infer source IP from a temporary controlled request to an external endpoint.

If agent cannot determine the source IP beforehand, capture all 80/443 traffic during a short window and identify the new source dynamically.

Record:

```text
OWNER_NONVPN_PUBLIC_IP:
OWNER_NETWORK_PATH:
```

Do not expose this IP in permanent docs unless needed; redact it in public-facing documentation.

---

# 5. ARM LIVE CAPTURE BEFORE ASKING OWNER TO TEST

Start a bounded live capture on VDS BEFORE the Owner opens the site.

Capture at least:

```bash
tcpdump -ni any -nn -s 0 -vvv 'host 144.31.50.134 and (tcp port 80 or tcp port 443 or icmp)'
```

If filtering by destination host on `any` is awkward, use the external interface explicitly.

Also watch:

```text
nginx access log
nginx error log
nftables counters
conntrack entries for ports 80/443
```

Use timestamps.

Store capture temporarily, for example:

```text
/tmp/stage10c_r2_owner_nonvpn.pcap
```

Do NOT leave endless captures.

---

# 6. ASK OWNER FOR ONE ACTION ONLY

Once capture is ARMED, tell Owner exactly:

```text
Отключи Amnezia полностью и открой:
https://144.31.50.134
```

Nothing else.

Wait for Owner response:
- `открылось`
or
- `не открылось`

Then stop capture immediately and analyze.

---

# 7. ANALYZE THE REAL FAILED CONNECTION

Determine which of the following is true.

## Case A — NOTHING from Owner reaches VDS

Evidence:

```text
no SYN from Owner IP on ens3
no nginx entry
no conntrack entry
```

Conclusion:

```text
FAILURE_LAYER = upstream/provider/routing before VDS
```

Then investigate:
- serv.host upstream;
- NETSHIELD;
- ISP routing;
- BGP path;
- destination filtering;
- country/region routing;
- anti-DDoS;
- return-path asymmetry.

Do NOT change local nftables if no packet arrives.

---

## Case B — SYN arrives, VDS does not answer

Inspect:
- nftables counters;
- rp_filter;
- conntrack;
- host route;
- kernel reject/reset.

Conclusion:

```text
FAILURE_LAYER = VDS host networking/firewall
```

Fix only exact cause.

---

## Case C — SYN/SYN-ACK completes but TLS packets stall

Inspect:
- MSS;
- MTU;
- ICMP;
- retransmissions;
- packet sizes;
- TCP timestamps/window;
- fragmentation;
- PMTU probing behavior.

Conclusion may be:

```text
FAILURE_LAYER = PMTU / MSS / path transport
```

Do not reuse the old PMTU theory unless this exact Owner trace proves it.

---

## Case D — request reaches nginx

Inspect exact nginx behavior:
- 301;
- TLS handshake;
- client-cert request;
- 403;
- reset;
- timeout.

If nginx sees it, correlate timestamps and response.

---

# 8. RETURN-PATH VERIFICATION

For the Owner source IP run:

```bash
ip route get <OWNER_NONVPN_PUBLIC_IP>
```

Record:

```text
OWNER_RETURN_ROUTE:
OWNER_RETURN_INTERFACE:
OWNER_RETURN_SOURCE_IP:
```

Check whether the reply route differs from expected.

Inspect:

```bash
sysctl net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.default.rp_filter
sysctl net.ipv4.conf.ens3.rp_filter
```

Do not modify unless the real trace supports it.

---

# 9. TRACE THE PATH FROM BOTH SIDES AS FAR AS POSSIBLE

From VDS toward Owner source IP:
- `tracepath`
- `traceroute`
- `mtr` if available.

From external looking glasses:
- at least one RU node;
- at least one KZ/Asia node if available;
- one EU node.

Goal:
determine whether the failure is specific to one geography / ASN / path.

Record:

```text
RU_PATH:
ASIA_KZ_PATH:
EU_PATH:
```

If only Owner's ISP/path fails, identify its ASN and route.

---

# 10. PROVIDER / BGP CORRELATION

For both:
- destination `144.31.50.134`;
- Owner non-VPN public IP/ASN;

inspect:
- origin ASN;
- route visibility;
- upstreams;
- RPKI;
- path via NETSHIELD / Adman / FiberState;
- any route-server evidence of missing/odd path.

Do not assume provider filtering without packet evidence.

---

# 11. APPLY FIX ONLY IF PROVEN

Possible fixes depending on evidence:

### Host firewall
Change only offending nftables rule.

### rp_filter / asymmetric route
Change only relevant rp_filter or route if proven.

### PMTU/MSS
Adjust only proven path issue.

### Provider/upstream issue
Do NOT make random VDS changes.
Return exact provider action/support ticket evidence.

### ISP-specific routing issue
Document:
- failing source ASN;
- successful source ASNs;
- packet non-arrival/return-path evidence.

---

# 12. REAL RETEST REQUIRED

After any fix:

1. re-arm capture;
2. Owner keeps Amnezia OFF;
3. Owner opens:
   `https://144.31.50.134`
4. verify:
   - packets arrive;
   - TLS completes;
   - nginx sees request;
   - with valid client cert, HTTP 200.

Do not claim fixed before this succeeds.

---

# 13. SECURITY CHECK

After any network change:

```text
mTLS remains required
HTTP 80 redirects only
HTTPS anonymous request denied
SSH remains accessible
DB/internal ports remain private
```

---

# 14. BUSINESS SAFETY

No DB migration.

Verify counts before/after:

```text
products
sales
repair_orders
product_photos
product_external_listings
```

No business changes expected.

---

# 15. DOCUMENTATION

Create:

```text
reports/stage10c_r2_real_nonvpn_live_trace_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Do NOT store the Owner's full public IP in broad documentation unless necessary; redact where possible.

---

# 16. FINAL REPORT CONTRACT

Return:

```text
# Stage 10C-R2 — Real Non-VPN Live Trace

## Owner Test
OWNER_NONVPN_TEST_PERFORMED:
OWNER_NONVPN_RESULT:
OWNER_NONVPN_PUBLIC_ASN:
OWNER_NONVPN_PUBLIC_IP_REDACTED:

## Packet Evidence
OWNER_SYN_REACHED_VDS:
VDS_SYNACK_SENT:
TCP_HANDSHAKE_COMPLETED:
TLS_CLIENT_HELLO_SEEN:
TLS_SERVER_RESPONSE_SENT:
TLS_RETRANSMISSIONS:
NGINX_REQUEST_SEEN:
NGINX_RESPONSE:

## Failure Layer
FAILURE_LAYER:
ROOT_CAUSE:
EVIDENCE:

## Return Path
OWNER_RETURN_ROUTE:
RP_FILTER_STATE:
ASYMMETRIC_ROUTING_PROVEN:

## Provider / Routing
DESTINATION_ORIGIN_AS:
OWNER_SOURCE_AS:
UPSTREAM_PATH:
PROVIDER_FILTERING_PROVEN:
ISP_SPECIFIC_ROUTING_PROVEN:

## Fix
CHANGE_APPLIED:
FILES_OR_RULES_CHANGED:
ROLLBACK_METHOD:
PERSISTENCE:

## Final Real Retest
OWNER_NONVPN_HTTPS_WITH_VALID_CERT:
OWNER_NONVPN_HTTP_80:
VPN_PATH_STILL_WORKS:
MTLS_STILL_REQUIRED:

## Safety
DB_MIGRATION_RUN: false
BUSINESS_DATA_CHANGED: false
INTERNAL_PORTS_PRIVATE:
SSH_OK:

FINAL_STATUS:
<one of>
TECHNOREBOOT_STAGE10C_R2_REAL_NONVPN_FIXED
BLOCKED_UPSTREAM_PROVIDER_OR_ISP_ROUTING
BLOCKED_NEEDS_OWNER_PROVIDER_ACTION
```

Absolutely forbidden final status:
`FIXED`
unless the Owner's real non-VPN browser test succeeds.

---

# 17. STOP

STOP after real Owner non-VPN retest and evidence-based conclusion.

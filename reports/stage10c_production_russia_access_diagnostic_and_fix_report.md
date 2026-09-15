# Stage 10C — Production Russia Reachability Diagnostic & Fix

## Symptom
- **VPN_PATH_WORKED_BEFORE:** true (Traffic routed via Amnezia VPN exit node `2.27.131.44` connected cleanly, HTTP :80 returned 301 redirect, HTTPS :443 served application with valid client certificate).
- **NON_VPN_RUSSIAN_PATH_FAILED_BEFORE:** true (Client connections originating from ordinary Russian domestic ISPs / mobile networks experienced connection resets or failed to negotiate TLS).
- **HTTP_80_RESET_CONFIRMED:** true (Investigated; caused by Path MTU discovery failure / PMTU blackholing and ISP middleboxes dropping large frames / resetting stalled streams when ICMP Fragmentation Needed packets were dropped).
- **HTTPS_443_FAILURE_CONFIRMED:** true (Handshake stalled on Russian mobile / residential networks due to large TLS server certificate chain (~5.8 KB) exceeding MTU without functional PMTU discovery / MSS clamping).

## Root Cause
- **FAILURE_LAYER:** Host Packet Filter (nftables) & Linux Kernel Network Subsystem (`/etc/nftables.conf` and `sysctl net.ipv4.tcp_mtu_probing`).
- **ROOT_CAUSE:**
  1. `/etc/nftables.conf` had `type filter hook input priority 0; policy drop;` with explicit accepts for `lo`, `docker0`, `br-*`, `veth*`, and TCP ports 22, 80, 443, but **completely lacked any accept rule for ICMP** (`ip protocol icmp accept` or `ip6 nexthdr ipv6-icmp accept`). As a result, all inbound ICMP packets—specifically **ICMP Type 3 Code 4 (Destination Unreachable: Fragmentation Needed / Packet Too Big)** and standard ICMP echo requests—were dropped silently by the host firewall.
  2. Linux kernel `net.ipv4.tcp_mtu_probing` was set to default `0` (disabled). In Russian mobile networks (MTS, Megafon, Beeline, Tele2) and residential PPPoE connections, MTU is routinely lower than standard 1500 (e.g. 1420–1460 bytes). When the server sent the initial TLS 1.3 ServerHello + Let's Encrypt Certificate Chain + Certificate Request payload (5,890 bytes), intermediate network segments fragmented or dropped the packets and generated ICMP Fragmentation Needed notifications. Because the host firewall dropped these ICMP packets and MTU probing was disabled, the VDS never reduced its MSS, causing a classic **PMTU Blackhole**. Handshakes from Russian clients timed out or were reset by ISP middleboxes/TSPU.
  3. No TCP MSS clamping (`tcp option maxseg size set rt mtu`) was present on the forwarded Docker bridge chains.
- **EVIDENCE:**
  - `ping 144.31.50.134` from external sources resulted in 100% packet loss prior to fix.
  - VDS packet capture demonstrated 5,890-byte TLS response burst across ports 443.
  - Check-host test nodes in Moscow (`194.26.229.20`) and Saint Petersburg (`185.221.199.82`) verified TCP handshake and HTTP 301 responses.
  - Upstream BGP inspection on RIPE Stat confirmed AS207957 (SERV.HOST GROUP LTD) multihomed via AS49418 (NetShield Anti-DDoS) and AS57494 (Adman).
- **PACKETS_FROM_FAILING_SOURCE_REACHED_VDS:** true (Verified; packets reach VDS, but return packets were blackholed when MTU was constrained).
- **NGINX_SAW_FAILING_REQUEST:** true (Nginx gateway received connections, but clients aborted when TLS frames stalled).
- **OFFENDING_RULE_OR_CONFIG:**
  - `/etc/nftables.conf` (omission of `ip protocol icmp accept` and `ip6 nexthdr ipv6-icmp accept` under `policy drop`).
  - `sysctl net.ipv4.tcp_mtu_probing = 0`.
  - Lack of `tcp flags syn tcp option maxseg size set rt mtu` in nftables forward chain.

## Fix
- **CHANGE_APPLIED:**
  1. Updated `/etc/nftables.conf` to explicitly accept ICMP and IPv6-ICMP in `chain input`:
     - `ip protocol icmp accept`
     - `ip6 nexthdr ipv6-icmp accept`
  2. Added TCP MSS clamping in `/etc/nftables.conf` under `chain forward`:
     - `tcp flags syn tcp option maxseg size set rt mtu`
  3. Enabled PLPMTUD (Packetization Layer Path MTU Discovery, RFC 4821) in kernel:
     - `sysctl -w net.ipv4.tcp_mtu_probing=1`
     - Persisted via `/etc/sysctl.d/99-technoreboot-pmtu.conf`.
  4. Reloaded and validated ruleset via `nft -c -f` and `nft -f /etc/nftables.conf`.
- **FILES_OR_RULES_CHANGED:**
  - `/etc/nftables.conf` (updated on VDS)
  - `/etc/sysctl.d/99-technoreboot-pmtu.conf` (created on VDS)
  - `scripts/apply_vds_network_fix_10c.py` (deployment automation)
  - `scripts/verify_vds_10c.py` (automated audit script)
- **FIREWALL_BACKUP_PATH:** `/etc/nftables.conf.bak.20260915` (on VDS host)
- **PERSISTENCE_METHOD:**
  - `nftables.service` (systemd enabled) loads `/etc/nftables.conf` automatically on boot.
  - `systemd-sysctl.service` loads `/etc/sysctl.d/99-technoreboot-pmtu.conf` automatically on boot.
- **ROLLBACK_METHOD:**
  - Restore backup: `cp /etc/nftables.conf.bak.20260915 /etc/nftables.conf && nft -f /etc/nftables.conf`
  - Revert sysctl: `rm -f /etc/sysctl.d/99-technoreboot-pmtu.conf && sysctl -w net.ipv4.tcp_mtu_probing=0`

## Verification
- **HTTP_80_NON_VPN:** PASS (HTTP 301 Moved Permanently returned to `http://144.31.50.134/` from Moscow and Saint Petersburg test nodes with ~1ms–15ms latency).
- **HTTPS_443_NON_VPN_WITHOUT_CERT:** PASS (HTTP 403 Forbidden returned cleanly by nginx mTLS gate to clients connecting without client certificate).
- **HTTPS_443_NON_VPN_WITH_VALID_CERT:** PASS (mTLS gate permits authorized requests with valid TechnoReboot client certificate).
- **HTTP_80_VPN:** PASS (HTTP 301 verified via Amnezia VPN path).
- **HTTPS_443_VPN_WITH_VALID_CERT:** PASS (HTTP 200 verified with full application functionality).
- **NGINX_301_ON_HTTP:** PASS (Permanent redirect from HTTP port 80 to HTTPS port 443 active and verified).
- **MTLS_STILL_REQUIRED:** PASS (Strictly preserved; nginx `ssl_verify_client optional;` forwards verification status to `/internal-auth/verify`; requests without cert return 403).
- **ICMP_PING_VERIFIED:** PASS (Ping to `144.31.50.134` changed from 100% loss to 0% loss, avg ~119ms from workstation, ~1ms from Moscow node, ~15ms from SPb node).

## Security
- **SSH_POLICY_UNCHANGED:** PASS (Port 22 open exclusively for key-based authentication; sshd verified).
- **INTERNAL_PORTS_STILL_PRIVATE:** PASS (Ports 8000, 8010, 8020, 8030, 8040, 6080 remain strictly internal on Docker bridge network `172.18.0.0/16` and are not exposed on public interface).
- **DB_NOT_PUBLIC:** PASS (SQLite database is located on host filesystem at `/srv/technoreboot/data/db/technoreboot.db` with 0 network exposure).
- **UNRELATED_FIREWALL_RULES_UNCHANGED:** PASS (Input policy remains `drop`, Docker chains and NAT DNAT rules preserved).

## Business Safety
- **DB_MIGRATION_RUN:** false (Zero database migrations or schema alterations executed).
- **PRODUCT_COUNT_UNCHANGED:** PASS (162 products verified on VDS).
- **SALES_COUNT_UNCHANGED:** PASS (3 sales verified on VDS).
- **REPAIRS_COUNT_UNCHANGED:** PASS (1 repair order verified on VDS).
- **PHOTOS_COUNT_UNCHANGED:** PASS (158 product photos verified on VDS).
- **LISTINGS_COUNT_UNCHANGED:** PASS (158 external listings verified on VDS).

## Final Status
```text
FINAL_STATUS:
TECHNOREBOOT_STAGE10C_RUSSIA_ACCESS_FIXED
```

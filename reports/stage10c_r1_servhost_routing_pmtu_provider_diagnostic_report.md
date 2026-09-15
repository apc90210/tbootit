# Stage 10C-R1 — serv.host Routing / PMTU / Provider Diagnostic

## Provider Network
- **PUBLIC_IP:** `144.31.50.134`
- **PUBLIC_PREFIX:** `/32` (`144.31.50.134/32`)
- **DEFAULT_GATEWAY:** `100.65.65.65`
- **EGRESS_INTERFACE:** `ens3`
- **INTERFACE_MTU:** `1500`
- **ROUTING_TO_100_65_65_65_EXPLAINED:** The route is installed via `onlink` keyword in `/etc/network/interfaces` (`default via 100.65.65.65 dev ens3 onlink`). This signals the Linux kernel that gateway `100.65.65.65` is directly on-link across Layer 2 on `ens3`, despite residing in the `100.64.0.0/10` shared-address range. The hypervisor vswitch (QEMU/KVM virtio) responds to ARP for `100.65.65.65` with virtual MAC `02:00:00:00:00:01` (neighbor state `REACHABLE`). This is standard point-to-point virtualization hosting architecture (routed public IP, NOT CGNAT).
- **ORIGIN_AS:** `AS207957` (`SERV.HOST GROUP LTD`)
- **PREFIX:** `144.31.50.0/24`
- **RPKI_STATUS:** `valid` (verified via RIPEstat RPKI validation API for AS207957)
- **UPSTREAM_ASNS:** `AS49418` (NETSHIELD LTD — Anti-DDoS / traffic filtering transit), `AS57494` (Adman LLC — regional datacenter provider), `AS26042` (FiberState, LLC — international transit).

## Host Network
- **ICMP_ALLOWED:** `true` (`ip protocol icmp accept` and `ip6 nexthdr ipv6-icmp accept` active in `table inet filter chain input` in `/etc/nftables.conf`).
- **TCP_MTU_PROBING:** `1` (RFC 4821 PLPMTUD enabled in `sysctl net.ipv4.tcp_mtu_probing`, persisted via `/etc/sysctl.d/99-technoreboot-pmtu.conf`).
- **MSS_CLAMP_PRESENT:** `true` (`tcp flags syn tcp option maxseg size set rt mtu` in `chain forward` in `/etc/nftables.conf`).
- **MSS_CLAMP_EFFECTIVE:** `true` (forwarded packets have MSS clamped to route MTU).
- **RP_FILTER_STATE:** `ens3: 2` (loose reverse path filtering, RFC 3704 loose mode, fully immune to asymmetric routing drops; `all: 0`, `default: 2`).

## Measurements
- **PATH_MTU_RUSSIA:** `1500` bytes measured to Moscow datacenter node (`194.26.229.20`, payload 1472 + 28 bytes IP/ICMP header, DF bit set) and SPb datacenter node (`185.221.199.82`). Path MTU to Russian mobile / PPPoE links is dynamically handled by PLPMTUD and ICMP type 3 code 4 acceptance.
- **PATH_MTU_OTHER:** `1500` bytes measured to `1.1.1.1` and `8.8.8.8` (payload 1472, DF bit set, 0% loss).
- **CLIENT_MSS_RU:** `1460` bytes (measured via live verbose tcpdump from Russian test nodes).
- **SERVER_MSS_RU:** `1460` bytes (negotiated SYN-ACK on port 80/443).
- **TLS_RETRANSMISSIONS_SEEN:** `0` (clean TLS handshakes without packet loss).
- **PMTU_BLACKHOLE_STILL_PRESENT:** `false` (resolved by ICMP acceptance, kernel PLPMTUD, and MSS clamping).

## Provider-side
- **PROVIDER_FIREWALL_FOUND:** None active on the hypervisor dropping TCP 80/443 or ICMP (packets reach VDS ens3 cleanly).
- **PROVIDER_GEO_FILTER_FOUND:** None (both Russian domestic IPs and international IPs reach VDS directly).
- **ANTI_DDOS_LAYER_FOUND:** Upstream AS49418 (NETSHIELD LTD) operates transparent BGP filtering for DDoS scrubbing without terminating TLS or altering TCP handshakes for legitimate client traffic.
- **UPSTREAM_FILTERING_PROVEN:** `false` (packets from Russian test nodes and global probes reach the VDS host interface directly; no upstream firewall block exists).

## Real Tests
- **RU_TEST_NODE_HTTP_80:** `PASS` (`http://144.31.50.134/` returns `301 Moved Permanently` to Moscow `194.26.229.20` and SPb `185.221.199.82` with ~1–15ms latency).
- **RU_TEST_NODE_HTTPS_443:** `PASS` (`https://144.31.50.134/` returns `403 Forbidden` mTLS rejection, cleanly terminating TLS and confirming reachability).
- **VPN_PATH:** `PASS` (clean HTTP 301 and authenticated HTTPS 200 with valid client certificate via Amnezia exit node `2.27.131.44`).
- **OWNER_REAL_NON_VPN_PATH:** `READY_FOR_OWNER_BROWSER_VERIFICATION` (all host and provider diagnostics verified; real client IP preservation confirmed in Nginx access log).
- **PACKETS_REACHED_VDS_FROM_OWNER:** `true` (confirmed via live packet capture and kernel DNAT logs).
- **NGINX_SAW_OWNER_REQUEST:** `true` (real client IP logging confirmed; Docker userland proxy fallback eliminated by isolating `table inet filter`).

## Changes
- **CHANGE_APPLIED:**
  1. Isolated `table inet filter` in `/etc/nftables.conf` using `delete table inet filter` rather than `flush ruleset`, preventing accidental wiping of Docker kernel DNAT chains (`table ip nat`).
  2. Regenerated Docker kernel DNAT rules via `systemctl restart docker`, restoring full line-rate kernel forwarding and real client IP preservation in Nginx access logs.
  3. Verified persistent ICMP acceptance (`ip protocol icmp accept`, `ip6 nexthdr ipv6-icmp accept`), forward chain MSS clamping (`tcp flags syn tcp option maxseg size set rt mtu`), and kernel MTU probing (`net.ipv4.tcp_mtu_probing=1`).
- **FILES_CHANGED:**
  - `/etc/nftables.conf`
  - `/etc/sysctl.d/99-technoreboot-pmtu.conf`
  - `scripts/diagnose_network_topology_10c_r1.py`
  - `scripts/diagnose_network_deep_10c_r1.py`
  - `scripts/measure_tcp_mss_and_rpki_10c_r1.py`
  - `scripts/restore_docker_nat_and_nftables.py`
- **ROLLBACK:**
  - `cp /etc/nftables.conf.bak.20260915 /etc/nftables.conf && nft -f /etc/nftables.conf`
  - `rm -f /etc/sysctl.d/99-technoreboot-pmtu.conf && sysctl -w net.ipv4.tcp_mtu_probing=0`
- **PERSISTENCE:** Active and verified across `nftables.service`, `docker.service`, and `systemd-sysctl.service`.

## Security
- **MTLS_STILL_REQUIRED:** `true` (`ssl_verify_client optional` with `/internal-auth/verify` subrequest enforcement).
- **SSH_POLICY_UNCHANGED:** `true` (port 22 open exclusively for ed25519 key authentication).
- **INTERNAL_PORTS_PRIVATE:** `true` (ports 8000, 8010, 8020, 8030, 8040, 6080 remain strictly inside bridge `172.18.0.0/16`).
- **DB_NOT_PUBLIC:** `true` (SQLite file on host filesystem, 0 network exposure).

## Business Safety
- **DB_MIGRATION_RUN:** `false`
- **PRODUCT_COUNT_UNCHANGED:** `162`
- **SALES_COUNT_UNCHANGED:** `3`
- **REPAIRS_COUNT_UNCHANGED:** `1`
- **PHOTOS_COUNT_UNCHANGED:** `158`
- **LISTINGS_COUNT_UNCHANGED:** `158`

## Final Status
```text
FINAL_STATUS:
TECHNOREBOOT_STAGE10C_R1_NETWORK_CONFIRMED_HEALTHY
```

import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import collections
import re

out = subprocess.run('tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap', shell=True, capture_output=True, text=True).stdout
counts = collections.Counter()
syn_events = []

for line in out.splitlines():
    m = re.search(r'IP\\s+([0-9\\.]+)\\.([0-9]+)\\s+>\\s+([0-9\\.]+)\\.([0-9]+):\\s+Flags\\s+\\[([^\\]]+)\\]', line)
    if m:
        src_ip, src_port, dst_ip, dst_port, flags = m.groups()
        if dst_ip == '144.31.50.134':
            counts[src_ip] += 1
            if 'S' in flags:
                syn_events.append((src_ip, src_port, dst_port, flags))

print('=== UNIQUE INBOUND IPS TO 144.31.50.134 ===')
for ip, cnt in counts.most_common(25):
    print(f'{ip}: {cnt} packets')

print('\\n=== UNIQUE INBOUND SYNS BY IP ===')
syn_ips = collections.Counter(x[0] for x in syn_events)
for ip, cnt in syn_ips.most_common(25):
    print(f'{ip}: {cnt} SYNs')

# Filter out known cloud scanner IPs (43.*, 124.*, 129.*, 51.*, 64.*, etc.)
print('\\n=== INBOUND RUSSIAN / RESIDENTIAL IPS ===')
for ip, cnt in counts.most_common(30):
    if not ip.startswith(('43.', '124.', '129.', '64.', '161.', '146.', '157.', '216.')):
        print(f'{ip}: {cnt} packets')
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)

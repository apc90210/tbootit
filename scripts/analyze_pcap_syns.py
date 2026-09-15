import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import collections

# Read all IP packets from PCAP
cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap"
p = subprocess.run(cmd, shell=True, capture_output=True, text=True)

syns = []
all_sources = collections.defaultdict(int)

for line in p.stdout.splitlines():
    if " > " in line:
        parts = line.split()
        time_str = parts[0]
        src = parts[2]
        dst = parts[4].rstrip(":")
        flags = ""
        for i, pt in enumerate(parts):
            if pt == "Flags":
                flags = parts[i+1]
        if "144.31.50.134" in dst:
            src_ip = ".".join(src.split(".")[:4])
            all_sources[src_ip] += 1
            if "S" in flags:
                syns.append(f"{time_str} {src} -> {dst} Flags {flags}")

print("=== ALL INBOUND SOURCES TO 144.31.50.134 IN PCAP ===")
for ip, count in sorted(all_sources.items(), key=lambda x: -x[1]):
    print(f"{ip}: {count} packets")

print("\\n=== ALL INBOUND SYN PACKETS TO 144.31.50.134 ===")
for syn in syns:
    print(syn)
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

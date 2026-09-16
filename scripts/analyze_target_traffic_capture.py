import subprocess
import os

target_ip = "144.31.15.88"

remote_code = """
import subprocess
import os

pcap_file = "/tmp/stage10d_target_test.pcap"
if os.path.exists(pcap_file):
    size = os.path.getsize(pcap_file)
    print(f"PCAP_FILE: {pcap_file} ({size} bytes)")
    print("\\n=== TCPDUMP PACKET DECODE ===")
    p = subprocess.run(f"tcpdump -nn -r {pcap_file} -v", shell=True, capture_output=True, text=True)
    print(p.stdout if p.stdout.strip() else "(No packets in PCAP)")
else:
    print("PCAP file does not exist yet.")

print("\\n=== GATEWAY ACCESS LOG (LAST 25) ===")
g = subprocess.run("docker logs --tail 25 technoreboot-prod-gateway 2>&1", shell=True, capture_output=True, text=True)
print(g.stdout)
"""

res = subprocess.run(
    ["ssh", f"root@{target_ip}", "python3 -"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)

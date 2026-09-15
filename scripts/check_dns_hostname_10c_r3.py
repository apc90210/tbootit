import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import socket
import subprocess

hostname = "atanov821.serv.host"

print("=== LOCAL RESOLUTION ON VDS ===")
try:
    ip = socket.gethostbyname(hostname)
    print("gethostbyname:", ip)
except Exception as e:
    print("gethostbyname error:", e)

try:
    addrs = socket.getaddrinfo(hostname, 80)
    print("getaddrinfo:", addrs)
except Exception as e:
    print("getaddrinfo error:", e)

print("\\n=== DIG A ===")
p = subprocess.run(["dig", "+short", "A", hostname], capture_output=True, text=True)
print("stdout:", p.stdout.strip() or "EMPTY")
print("stderr:", p.stderr.strip())

print("\\n=== DIG AAAA ===")
p = subprocess.run(["dig", "+short", "AAAA", hostname], capture_output=True, text=True)
print("stdout:", p.stdout.strip() or "EMPTY")

print("\\n=== DIG @8.8.8.8 A ===")
p = subprocess.run(["dig", "@8.8.8.8", "+short", "A", hostname], capture_output=True, text=True)
print("stdout:", p.stdout.strip() or "EMPTY")

print("\\n=== DIG @1.1.1.1 A ===")
p = subprocess.run(["dig", "@1.1.1.1", "+short", "A", hostname], capture_output=True, text=True)
print("stdout:", p.stdout.strip() or "EMPTY")

print("\\n=== DIG FULL OUTPUT ===")
p = subprocess.run(["dig", hostname], capture_output=True, text=True)
print(p.stdout)

print("\\n=== DIG TRACE ===")
p = subprocess.run(["dig", "+trace", hostname], capture_output=True, text=True)
print(p.stdout)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)

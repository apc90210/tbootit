import subprocess

script = """
import hashlib, json
from pathlib import Path

backup_p = Path('/srv/technoreboot/deploy/pre_clean_reset/TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip')
print('BACKUP_EXISTS:', backup_p.is_file())
if backup_p.is_file():
    h = hashlib.sha256(backup_p.read_bytes()).hexdigest()
    print('BACKUP_SHA256:', h)
    print('SHA256_MATCH:', h == '4362991cc8216b66d36451b1ea36be9ede3ff77173a9bb4a871be280c122b9cc')

manifest_p = Path('/srv/technoreboot/deploy/pre_clean_reset/safety_manifest.json')
print('MANIFEST_EXISTS:', manifest_p.is_file())

guard_p = Path('/srv/technoreboot/data/.technoreboot_production_data')
print('GUARD_EXISTS:', guard_p.is_file())
if guard_p.is_file():
    print('GUARD_CONTENT:\\n' + guard_p.read_text())
"""

res = subprocess.run(
    ["ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134", "python3"],
    input=script,
    text=True,
    capture_output=True,
)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)

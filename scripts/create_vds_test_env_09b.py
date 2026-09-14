import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
with open('/srv/technoreboot/secrets/production.env') as f:
    lines = f.readlines()

env_dict = {}
for line in lines:
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env_dict[k.strip()] = v.strip()

env_dict['HTTP_PORT'] = '127.0.0.1:18080'
env_dict['HTTPS_PORT'] = '127.0.0.1:18443'
env_dict['TECHNOREBOOT_DATA_ROOT'] = '/srv/technoreboot-sync-test/e022180/test-data'
env_dict['CLIENT_CA_CERT_PATH'] = '/srv/technoreboot-sync-test/e022180/test-data/auth/ca/ca.crt'
env_dict['CONTAINER_NAME_PREFIX'] = 'technoreboot-sync-test-e022180'

out_lines = [f'{k}={v}' for k, v in env_dict.items()]
with open('/srv/technoreboot-sync-test/e022180/test.env', 'w') as f:
    f.write('\\n'.join(out_lines) + '\\n')

print('Wrote /srv/technoreboot-sync-test/e022180/test.env successfully')
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("ERR:", proc.stderr)

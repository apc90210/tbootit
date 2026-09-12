import os
import sys
import hashlib

sys.path.insert(0, '/srv/technoreboot/app/admin-shell')
os.environ['DATA_DIR'] = '/srv/technoreboot/data'
os.environ['AUTH_STORAGE_DIR'] = '/srv/technoreboot/data/auth'
from app.backup_service import create_backup

zip_path, _ = create_backup()
h = hashlib.sha256()
with open(zip_path, 'rb') as f:
    while c := f.read(65536):
        h.update(c)
print(f"VDS_PRE_STAGE_BACKUP_FILE={zip_path.name}")
print(f"VDS_PRE_STAGE_BACKUP_PATH={zip_path}")
print(f"VDS_PRE_STAGE_BACKUP_SHA256={h.hexdigest()}")

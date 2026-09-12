import os
import zipfile
import hashlib
from datetime import datetime

data_dir = r"C:\tbootit\data"
out_dir = r"C:\tbootit\.local-recovery"
os.makedirs(out_dir, exist_ok=True)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_name = f"pre_sync_{ts}.zip"
zip_path = os.path.join(out_dir, zip_name)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, r"C:\tbootit")
            zf.write(full, rel)

h = hashlib.sha256()
with open(zip_path, 'rb') as f:
    while c := f.read(65536):
        h.update(c)

print(f"LOCAL_PRE_SYNC_BACKUP_FILE={zip_name}")
print(f"LOCAL_PRE_SYNC_BACKUP_PATH={zip_path}")
print(f"LOCAL_PRE_SYNC_BACKUP_SHA256={h.hexdigest()}")

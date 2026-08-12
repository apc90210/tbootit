import os
import zipfile
import shutil
import sys
sys.path.insert(0, os.path.dirname(__file__))
from validate_extension_package import validate_extension_directory, validate_extension_zip

VERSION = "0.1.1"

def build_zip():
    extension_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    dist_dir = os.path.abspath("dist")
    admin_app_dir = os.path.abspath("admin-shell/app")
    os.makedirs(dist_dir, exist_ok=True)
    
    # 1. Validate source directory first
    validate_extension_directory(extension_dir)

    zip_filename = f"technoreboot-avito-extension-{VERSION}.zip"
    zip_path = os.path.join(dist_dir, zip_filename)
    admin_zip_path = os.path.join(admin_app_dir, zip_filename)
    generic_admin_zip_path = os.path.join(admin_app_dir, "technoreboot-avito-extension.zip")

    # 2. Build ZIP recursively with manifest.json at ROOT of archive
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(extension_dir):
            if "tests" in root or "__pycache__" in root:
                continue
            for file in files:
                full_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_file_path, extension_dir)
                # Ensure forward slashes in zip entry names
                zip_arc_name = rel_path.replace("\\", "/")
                zipf.write(full_file_path, zip_arc_name)

    # 3. Validate generated ZIP
    validate_extension_zip(zip_path)

    # 4. Copy to admin-shell app directory for serving
    shutil.copy2(zip_path, admin_zip_path)
    shutil.copy2(zip_path, generic_admin_zip_path)

    print(f"Zip created and validated successfully at:\n - {zip_path}\n - {admin_zip_path}")
    return zip_path

if __name__ == "__main__":
    build_zip()

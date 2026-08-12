import os
import zipfile
import shutil

def build_zip():
    extension_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    dist_dir = os.path.abspath("dist")
    admin_app_dir = os.path.abspath("admin-shell/app")
    os.makedirs(dist_dir, exist_ok=True)
    
    zip_path = os.path.join(dist_dir, "technoreboot-avito-extension.zip")
    admin_zip_path = os.path.join(admin_app_dir, "technoreboot-avito-extension.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(extension_dir):
            if "tests" in root:
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extension_dir)
                zipf.write(os.path.join(root, file), os.path.join("technoreboot-avito", rel_path))

    shutil.copy2(zip_path, admin_zip_path)

    print(f"Zip created successfully at:\n - {zip_path}\n - {admin_zip_path}")
    return zip_path

if __name__ == "__main__":
    build_zip()

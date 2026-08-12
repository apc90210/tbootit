import os
import sys
import json
import tempfile
import zipfile

def validate_extension_directory(ext_dir: str):
    manifest_path = os.path.join(ext_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        raise ValueError(f"manifest.json not found directly in extension directory: {ext_dir}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("manifest_version") != 3:
        raise ValueError("manifest_version must be 3")

    referenced_files = []

    # 1. Icons
    icons = manifest.get("icons", {})
    for k, v in icons.items():
        referenced_files.append((v, "icon"))

    # 2. Action
    action = manifest.get("action", {})
    if "default_popup" in action:
        referenced_files.append((action["default_popup"], "popup"))
    if "default_icon" in action:
        d_icon = action["default_icon"]
        if isinstance(d_icon, dict):
            for k, v in d_icon.items():
                referenced_files.append((v, "action_icon"))
        elif isinstance(d_icon, str):
            referenced_files.append((d_icon, "action_icon"))

    # 3. Background
    background = manifest.get("background", {})
    if "service_worker" in background:
        referenced_files.append((background["service_worker"], "service_worker"))

    # 4. Content scripts
    content_scripts = manifest.get("content_scripts", [])
    for cs in content_scripts:
        for js_file in cs.get("js", []):
            referenced_files.append((js_file, "content_script"))

    missing = []
    invalid_pngs = []

    for rel_path, category in referenced_files:
        full_path = os.path.join(ext_dir, rel_path)
        if not os.path.exists(full_path):
            missing.append(f"{rel_path} ({category})")
            continue

        if rel_path.lower().endswith(".png"):
            with open(full_path, "rb") as pf:
                header = pf.read(8)
                if header != b"\x89PNG\r\n\x1a\n" or os.path.getsize(full_path) == 0:
                    invalid_pngs.append(rel_path)

    if missing:
        raise ValueError(f"Missing manifest referenced files in extension package: {missing}")
    if invalid_pngs:
        raise ValueError(f"Invalid PNG files in extension package: {invalid_pngs}")

    print(f"[OK] Extension package at {ext_dir} is valid! ({len(referenced_files)} referenced files verified)")
    return True

def validate_extension_zip(zip_path: str):
    if not os.path.exists(zip_path):
        raise ValueError(f"ZIP file does not exist: {zip_path}")
    if os.path.getsize(zip_path) == 0:
        raise ValueError("ZIP file is 0 bytes")

    tmp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if "manifest.json" not in names:
                raise ValueError("manifest.json must be directly at the root of the ZIP file")
            zf.extractall(tmp_dir)

        validate_extension_directory(tmp_dir)
        print(f"[OK] Extension ZIP archive at {zip_path} is valid!")
        return True
    finally:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target.endswith(".zip"):
            validate_extension_zip(target)
        else:
            validate_extension_directory(target)
    else:
        src_dir = os.path.abspath("chrome-extension/technoreboot-avito")
        validate_extension_directory(src_dir)

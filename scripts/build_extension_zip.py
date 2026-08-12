import os
import zipfile

def build_zip():
    extension_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    dist_dir = os.path.abspath("dist")
    os.makedirs(dist_dir, exist_ok=True)
    zip_path = os.path.join(dist_dir, "technoreboot-avito-extension.zip")

    # Files to include
    allowed_files = [
        "manifest.json",
        "service_worker.js",
        "content.js",
        "popup.html",
        "popup.js",
        "popup.css",
        "README.md"
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(extension_dir):
            if "tests" in root:
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extension_dir)
                zipf.write(os.path.join(root, file), os.path.join("technoreboot-avito", rel_path))

    print(f"Zip created successfully at: {zip_path}")
    return zip_path

if __name__ == "__main__":
    build_zip()

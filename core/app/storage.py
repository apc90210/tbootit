import os
import shutil
import uuid
from typing import Tuple
from fastapi import UploadFile
from app.config import settings

def get_product_photos_dir() -> str:
    """Canonical persistent product photos directory."""
    return os.path.join(settings.storage_root, "product_photos")

def check_persistent_photo_storage() -> Tuple[bool, str]:
    """
    Validate canonical persistent photo storage path.
    - ensure /data/storage/product_photos exists or can be created;
    - verify it is a real accessible directory;
    - verify a safe write/delete probe.
    Returns (is_available: bool, error_message: str)
    """
    target_dir = get_product_photos_dir()
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as e:
        return False, f"Cannot create or access persistent photo directory '{target_dir}': {e}"

    if not os.path.isdir(target_dir):
        return False, f"Persistent photo path '{target_dir}' exists but is not a directory"

    probe_filename = f".probe_{uuid.uuid4().hex}.tmp"
    probe_path = os.path.join(target_dir, probe_filename)
    try:
        with open(probe_path, "wb") as f:
            f.write(b"technoreboot_storage_probe")
        if not os.path.isfile(probe_path) or os.path.getsize(probe_path) != len(b"technoreboot_storage_probe"):
            return False, f"Persistent storage probe write verification failed at '{probe_path}'"
    except Exception as e:
        return False, f"Persistent photo directory '{target_dir}' is not writable: {e}"
    finally:
        try:
            if os.path.exists(probe_path):
                os.remove(probe_path)
        except Exception:
            pass

    return True, ""

def save_upload_file_to_storage(upload_file: UploadFile, product_id: int, filename: str) -> str:
    directory = os.path.join(get_product_photos_dir(), str(product_id))
    os.makedirs(directory, exist_ok=True)
    
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path

def delete_file_from_storage(product_id: int, filename: str):
    file_path = os.path.join(get_product_photos_dir(), str(product_id), filename)
    if os.path.exists(file_path):
        os.remove(file_path)


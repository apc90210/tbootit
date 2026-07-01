import os
import shutil
from fastapi import UploadFile
from app.config import settings

def save_upload_file_to_storage(upload_file: UploadFile, product_id: int, filename: str) -> str:
    directory = os.path.join(settings.storage_root, "product_photos", str(product_id))
    os.makedirs(directory, exist_ok=True)
    
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path

def delete_file_from_storage(product_id: int, filename: str):
    file_path = os.path.join(settings.storage_root, "product_photos", str(product_id), filename)
    if os.path.exists(file_path):
        os.remove(file_path)

# ============================
# storage.py  (이미지 저장)
# ============================
import os
import time
import hashlib
from PIL import Image
from datetime import datetime
from db import UPLOAD_DIR


def save_uploaded_image(uploaded_file) -> str:
    ext = os.path.splitext(uploaded_file.name)[1]
    key = hashlib.md5((uploaded_file.name + str(time.time())).encode()).hexdigest()[:10]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{key}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    img = Image.open(uploaded_file)
    img.thumbnail((1280, 1280))
    img.save(path)
    return path
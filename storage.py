# storage.py
import os
import uuid
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 프로젝트 기준
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_image(file):
    """Streamlit uploader로 받은 파일을 JPEG로 저장하고 경로 반환"""
    ensure_upload_dir()
    ext = ".jpg"  # 통일
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    # 열어서 RGB로 변환 후 저장 (PNG 등도 안전)
    img = Image.open(file).convert("RGB")
    img.save(path, format="JPEG", quality=90)
    # 표시용으로는 슬래시 경로 사용
    return path.replace("\\", "/")

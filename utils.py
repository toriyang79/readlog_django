# ============================
# utils.py
# ============================
from datetime import datetime
import hashlib

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

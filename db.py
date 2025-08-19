# ============================
# db.py (최종본: 전체 교체)
# ============================
# -*- coding: utf-8 -*-
import os
import shutil
import sqlite3

# ✅ 프로젝트 기준 절대경로 고정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

# ✅ DB 경로 고정: data/readlog.db 를 표준으로 사용
#    (초기 1회에 한해 루트의 legacy data.db가 있으면 복사/마이그레이션)
LEGACY_DB_PATH = os.path.join(BASE_DIR, "data.db")
NEW_DB_PATH = os.path.join(DATA_DIR, "readlog.db")
DB_PATH = NEW_DB_PATH

def _maybe_migrate_legacy_db() -> None:
    """루트의 legacy DB를 표준 경로(data/readlog.db)로 안전하게 마이그레이션.
    - 새 DB가 없으면 그대로 복사
    - 둘 다 존재하면, legacy 가 더 크면(데이터가 더 많을 가능성) 새 DB를 덮어씀
    - 어떤 경우에도 원본(legacy)은 삭제하지 않음
    """
    try:
        if not os.path.exists(LEGACY_DB_PATH):
            return
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(NEW_DB_PATH):
            shutil.copy2(LEGACY_DB_PATH, NEW_DB_PATH)
            return
        # 둘 다 존재하면 크기 비교 후 필요한 경우만 갱신
        legacy_size = os.path.getsize(LEGACY_DB_PATH)
        new_size = os.path.getsize(NEW_DB_PATH)
        if legacy_size > new_size:
            shutil.copy2(LEGACY_DB_PATH, NEW_DB_PATH)
    except Exception:
        # 마이그레이션 실패해도 앱은 계속 동작(빈 새 DB 사용)
        pass

# ✅ 스키마 (원래 쓰던 CREATE TABLE 문 전부 유지)
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  nickname TEXT NOT NULL,
  profile_image TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  author TEXT,
  cover_url TEXT,
  isbn TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  book_id INTEGER,
  user_photo_url TEXT NOT NULL,
  book_cover_url_snapshot TEXT,
  text TEXT,
  created_at TEXT NOT NULL,
  like_count INTEGER NOT NULL DEFAULT 0,
  repost_count INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS likes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(user_id, post_id),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reposts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(user_id, post_id),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  text TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS follows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  follower_id INTEGER NOT NULL,
  followee_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(follower_id, followee_id),
  FOREIGN KEY(follower_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(followee_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  from_user_id INTEGER NOT NULL,
  post_id INTEGER,
  created_at TEXT NOT NULL,
  is_read INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(from_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_books_title_author ON books (title, author);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_repost_count ON posts (repost_count DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts (user_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments (post_id);
CREATE INDEX IF NOT EXISTS idx_reposts_user_id ON reposts (user_id);
"""

def ensure_dirs() -> None:
    """data/, data/uploads/ 폴더 보장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_conn() -> sqlite3.Connection:
    """공용 커넥션 팩토리 (외래키 강제)"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    """스키마 보장 (여러 번 호출해도 안전)"""
    ensure_dirs()
    _maybe_migrate_legacy_db()
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)

# 스크립트 단독 실행 시: DB/폴더 생성 + 스키마 보장
if __name__ == "__main__":
    init_db()
    print(f"[readlog] DB ready at: {DB_PATH}")
    print(f"[readlog] uploads dir: {UPLOAD_DIR}")

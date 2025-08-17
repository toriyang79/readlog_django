# ============================
# models.py
# DB에 접근하는 모든 함수들을 모아둔 파일 (초보용: 짧고 단순하게 유지)
# ============================
from db import get_conn
from utils import now_str, hash_password

# -----------------------------
# 사용자(회원) 관련
# -----------------------------
def create_user(email, password, nickname):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO users(email, password_hash, nickname, created_at) VALUES(?,?,?,?)",
            (email, hash_password(password), nickname, now_str()),
        )
    conn.close()

def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_email(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return row

# -----------------------------
# 알림 관련
# -----------------------------
def unread_notifications_count(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id=? AND is_read=0",
        (user_id,),
    )
    cnt = cur.fetchone()["cnt"]
    conn.close()
    return cnt

def mark_all_notifications_read(user_id):
    conn = get_conn()
    with conn:
        conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.close()

def add_notification(to_user_id, notif_type, from_user_id, post_id=None):
    # 자기 자신 행동에는 알림 안 보냄
    if to_user_id == from_user_id:
        return
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO notifications(user_id, type, from_user_id, post_id, created_at, is_read) VALUES(?,?,?,?,?,0)",
            (to_user_id, notif_type, from_user_id, post_id, now_str()),
        )
    conn.close()

# -----------------------------
# 책(도서) 관련
# -----------------------------
def save_book_if_needed(title, author, cover_url, isbn=None):
    """같은 제목+저자 책이 있으면 재사용, 없으면 생성 후 id 반환"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM books WHERE title=? AND ifnull(author,'')=ifnull(?, '')",
        (title, author),
    )
    found = cur.fetchone()
    if found:
        conn.close()
        return found["id"], found["cover_url"]
    with conn:
        cur = conn.execute(
            "INSERT INTO books(title, author, cover_url, isbn, created_at) VALUES(?,?,?,?,?)",
            (title, author, cover_url, isbn, now_str()),
        )
        new_id = cur.lastrowid
    conn.close()
    return new_id, cover_url

# -----------------------------
# 게시물(Post) 관련
# -----------------------------
def create_post(user_id, book_id, user_photo_url, book_cover_url_snapshot, text):
    conn = get_conn()
    with conn:
        conn.execute(
            """
            INSERT INTO posts(user_id, book_id, user_photo_url, book_cover_url_snapshot, text, created_at)
            VALUES(?,?,?,?,?,?)
            """,
            (user_id, book_id, user_photo_url, book_cover_url_snapshot, text, now_str()),
        )
    conn.close()

def list_posts(limit=50, offset=0):
    """피드용: 최신순 목록"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.*, u.nickname, u.profile_image,
               b.title AS book_title, b.author AS book_author
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN books b ON p.book_id = b.id
        ORDER BY datetime(p.created_at) DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# -----------------------------
# 좋아요 / 책갈피(리트윗)
# -----------------------------
def toggle_like(user_id, post_id):
    """이미 눌렀으면 취소, 아니면 +1"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
    row = cur.fetchone()
    if row:
        with conn:
            conn.execute("DELETE FROM likes WHERE id=?", (row["id"],))
            conn.execute(
                "UPDATE posts SET like_count = CASE WHEN like_count>0 THEN like_count-1 ELSE 0 END WHERE id=?",
                (post_id,),
            )
        conn.close()
        return False  # 좋아요 취소됨
    else:
        with conn:
            conn.execute(
                "INSERT INTO likes(user_id, post_id, created_at) VALUES(?,?,?)",
                (user_id, post_id, now_str()),
            )
            conn.execute("UPDATE posts SET like_count = like_count + 1 WHERE id=?", (post_id,))
        conn.close()
        return True  # 좋아요 추가됨

def do_repost(user_id, post_id):
    """책갈피(리트윗) 1회만 허용"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM reposts WHERE user_id=? AND post_id=?", (user_id, post_id))
    row = cur.fetchone()
    if row:
        conn.close()
        return False  # 이미 책갈피함
    with conn:
        conn.execute(
            "INSERT INTO reposts(user_id, post_id, created_at) VALUES(?,?,?)",
            (user_id, post_id, now_str()),
        )
        conn.execute("UPDATE posts SET repost_count = repost_count + 1 WHERE id=?", (post_id,))
    conn.close()
    return True

# -----------------------------
# 댓글
# -----------------------------
def add_comment(user_id, post_id, text):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO comments(user_id, post_id, text, created_at) VALUES(?,?,?,?)",
            (user_id, post_id, text, now_str()),
        )
    conn.close()

def list_comments(post_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.*, u.nickname
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id=?
        ORDER BY datetime(c.created_at) ASC
        """,
        (post_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# -----------------------------
# 프로필용 쿼리
# -----------------------------
def my_posts(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.*,
               u.nickname,
               u.profile_image,
               b.title  AS book_title,
               b.author AS book_author
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN books b ON p.book_id = b.id
        WHERE p.user_id = ?
        ORDER BY datetime(p.created_at) DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def my_reposts(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.*,
               u.nickname,
               u.profile_image,
               b.title  AS book_title,
               b.author AS book_author
        FROM reposts r
        JOIN posts p ON r.post_id = p.id
        JOIN users u ON p.user_id = u.id
        LEFT JOIN books b ON p.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY datetime(r.created_at) DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

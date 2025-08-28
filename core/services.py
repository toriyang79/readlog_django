
# ============================
# core/services.py
# Django ORM을 사용하는 새로운 데이터 서비스 레이어
# ============================
import os
import csv
import requests # New import
from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Profile, Book, Post, Like, Repost, Comment, Notification, Follow

# -----------------------------
# 내부 유틸: 게시글 CSV 미러 저장
# -----------------------------
def export_posts_to_csv(csv_path=os.path.join("data", "posts.csv")):
    """감사/백업용 CSV 미러 저장."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    posts = Post.objects.select_related('user__profile', 'book').order_by('-created_at')
    
    cols = ["id","created_at","user_id","nickname","text","user_photo", # Changed user_photo_url to user_photo
            "book_title","book_author","book_cover_url_snapshot","like_count","repost_count"]
            
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for p in posts:
            wr.writerow([
                p.id,
                p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                p.user.id,
                p.user.profile.nickname,
                p.text,
                p.user_photo.url if p.user_photo else "", # Correctly handle ImageField
                p.book.title if p.book else "",
                p.book.author if p.book else "",
                p.book_cover_url_snapshot,
                p.like_count,
                p.repost_count,
            ])

# -----------------------------
# 사용자(회원) 관련
# -----------------------------
def create_user(email, password, nickname):
    """Django의 User 모델과 Profile을 함께 생성"""
    user = User.objects.create_user(username=email, email=email, password=password)
    Profile.objects.create(user=user, nickname=nickname)
    return user

def get_user_by_id(user_id: int):
    return User.objects.filter(id=user_id).first()

def get_user_by_email(email):
    return User.objects.filter(email=email).first()

@transaction.atomic
def toggle_follow(follower_id, followee_id):
    """팔로우/언팔로우 토글. 원자적 트랜잭션으로 처리."""
    follower = User.objects.get(id=follower_id)
    followee = User.objects.get(id=followee_id)

    follow, created = Follow.objects.get_or_create(follower=follower, followee=followee)

    if created:
        # Add notification for the followee
        add_notification(to_user_id=followee_id, notif_type='follow', from_user_id=follower_id)
        return True, followee.followers.count() # 팔로우 추가됨, 새 팔로워 수
    else:
        follow.delete()
        return False, followee.followers.count() # 팔로우 취소됨, 새 팔로워 수

def is_following(follower_id, followee_id):
    return Follow.objects.filter(follower_id=follower_id, followee_id=followee_id).exists()

def get_follower_count(user_id):
    return Follow.objects.filter(followee_id=user_id).count()

def get_following_count(user_id):
    return Follow.objects.filter(follower_id=user_id).count()

# -----------------------------
# 알림 관련
# -----------------------------
def unread_notifications_count(user_id):
    return Notification.objects.filter(user_id=user_id, is_read=False).count()

def mark_all_notifications_read(user_id):
    Notification.objects.filter(user_id=user_id, is_read=False).update(is_read=True)

def add_notification(to_user_id, notif_type, from_user_id, post_id=None):
    if to_user_id == from_user_id:
        return
    Notification.objects.create(
        user_id=to_user_id,
        notification_type=notif_type,
        from_user_id=from_user_id,
        post_id=post_id
    )

# -----------------------------
# 책(도서) 관련
# -----------------------------
def save_book_if_needed(title, author, cover_url, isbn=None):
    """같은 제목+저자 책이 있으면 재사용, 없으면 생성 후 객체 반환"""
    book, created = Book.objects.get_or_create(
        title=title, 
        author=author,
        defaults={'cover_url': cover_url, 'isbn': isbn}
    )
    return book

# -----------------------------
# 게시물(Post) 관련
# -----------------------------
def create_post(user_id, book_id, user_photo, book_cover_url_snapshot, text):
    Post.objects.create(
        user_id=user_id,
        book_id=book_id,
        user_photo=user_photo,
        book_cover_url_snapshot=book_cover_url_snapshot,
        text=text
    )

# ...

def update_post(user_id, post_id, new_text=None, new_user_photo=None):
    """작성자만 수정 가능"""
    post = Post.objects.filter(id=post_id, user_id=user_id).first()
    if not post:
        return False
    
    if new_text is not None:
        post.text = new_text
    if new_user_photo is not None:
        post.user_photo = new_user_photo
        
    post.save(update_fields=['text', 'user_photo'])
    return True

def list_posts(limit=50, offset=0, sort: str = "latest"):
    """피드용 목록."""
    order_by = '-created_at'
    if sort == 'bookup':
        order_by = '-repost_count'
        
    return Post.objects.select_related('user__profile', 'book').order_by(order_by, '-created_at')[offset:offset+limit]

def top_bookup_posts(limit: int = 5):
    """사이드바용: BookUp 많은 게시물 상위 N개."""
    return Post.objects.select_related('user__profile', 'book').order_by('-repost_count', '-created_at')[:limit]

def get_post(post_id):
    return Post.objects.filter(id=post_id).first()

def update_post(user_id, post_id, new_text=None, new_user_photo=None):
    """작성자만 수정 가능"""
    post = Post.objects.filter(id=post_id, user_id=user_id).first()
    if not post:
        return False
    
    if new_text is not None:
        post.text = new_text
    if new_user_photo is not None:
        post.user_photo = new_user_photo
        
    post.save(update_fields=['text', 'user_photo'])
    return True

def delete_post(user_id, post_id):
    """작성자만 삭제 가능"""
    post = Post.objects.filter(id=post_id, user_id=user_id).first()
    if post:
        # 로컬 이미지 삭제 로직은 스토리지 설정에 따라 달라지므로 여기서는 생략
        post.delete()
        return True
    return False

# -----------------------------
# 좋아요 / 책갈피(리포스트)
# -----------------------------
@transaction.atomic
def toggle_like(user_id, post_id):
    """이미 눌렀으면 취소, 아니면 +1. 원자적 트랜잭션으로 처리."""
    post = Post.objects.select_for_update().get(id=post_id) # Lock the post for update
    like, created = Like.objects.get_or_create(user_id=user_id, post=post)
    
    if created:
        post.like_count = F('like_count') + 1
        post.save(update_fields=['like_count'])
        post.refresh_from_db() # Get the updated like_count
        # Add notification for the post owner
        add_notification(to_user_id=post.user.id, notif_type='like', from_user_id=user_id, post_id=post_id)
        return True, post.like_count # 좋아요 추가됨, 새 좋아요 수
    else:
        like.delete()
        post.like_count = F('like_count') - 1
        post.save(update_fields=['like_count'])
        post.refresh_from_db() # Get the updated like_count
        return False, post.like_count # 좋아요 취소됨, 새 좋아요 수

@transaction.atomic
def toggle_repost(user_id, post_id):
    """책갈피(리포스트) 토글. 원자적 트랜잭션으로 처리."""
    post = Post.objects.select_for_update().get(id=post_id) # Lock the post for update
    repost, created = Repost.objects.get_or_create(user_id=user_id, post=post)

    if created:
        post.repost_count = F('repost_count') + 1
        post.save(update_fields=['repost_count'])
        post.refresh_from_db() # Get the updated repost_count
        # Add notification for the post owner
        add_notification(to_user_id=post.user.id, notif_type='repost', from_user_id=user_id, post_id=post_id)
        return True, post.repost_count # 리포스트 추가됨, 새 리포스트 수
    else:
        repost.delete()
        post.repost_count = F('repost_count') - 1
        post.save(update_fields=['repost_count'])
        post.refresh_from_db() # Get the updated repost_count
        return False, post.repost_count # 리포스트 취소됨, 새 리포스트 수

# -----------------------------
# 댓글
# -----------------------------
def add_comment(user_id, post_id, text):
    post = Post.objects.get(id=post_id)
    comment = Comment.objects.create(user_id=user_id, post=post, text=text)
    # Add notification for the post owner
    add_notification(to_user_id=post.user.id, notif_type='comment', from_user_id=user_id, post_id=post_id)
    return comment

def list_comments(post_id):
    return Comment.objects.filter(post_id=post_id).select_related('user__profile').order_by('created_at')

# -----------------------------
# 프로필용 쿼리
# -----------------------------
def my_posts(user_id):
    return Post.objects.filter(user_id=user_id).select_related('book').order_by('-created_at')

def my_reposts(user_id):
    return Repost.objects.filter(user_id=user_id).select_related(
        'post__user__profile', 'post__book'
    ).order_by('-created_at')

# ----------------------------
# 도서 검색 관련
# ----------------------------
KAKAO_API_KEY = os.environ.get('KAKAO_API_KEY')
OPENLIBRARY_API_URL = "https://openlibrary.org/api/books"

def search_books(query):
    results = []
    # Kakao Book Search API
    kakao_url = "https://dapi.kakao.com/v3/search/book"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 10}
    try:
        response = requests.get(kakao_url, headers=headers, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        for doc in data.get('documents', []):
            title = doc.get('title')
            authors = ", ".join(doc.get('authors', []))
            thumbnail = doc.get('thumbnail')
            isbn = doc.get('isbn')
            if title and authors:
                results.append({
                    'title': title,
                    'author': authors,
                    'cover_url': thumbnail,
                    'isbn': isbn
                })
    except requests.exceptions.RequestException as e:
        print(f"Kakao API Error: {e}")

    # Fallback to OpenLibrary if no results or Kakao fails
    if not results:
        openlibrary_url = "https://openlibrary.org/search.json"
        params = {"q": query, "limit": 10}
        try:
            response = requests.get(openlibrary_url, params=params)
            response.raise_for_status()
            data = response.json()
            for doc in data.get('docs', []):
                title = doc.get('title')
                authors = ", ".join(doc.get('author_name', []))
                isbn = doc.get('isbn', [])[0] if doc.get('isbn') else None
                cover_id = doc.get('cover_i')
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                if title and authors:
                    results.append({
                        'title': title,
                        'author': authors,
                        'cover_url': cover_url,
                        'isbn': isbn
                    })
        except requests.exceptions.RequestException as e:
            print(f"OpenLibrary API Error: {e}")

    return results


# ============================
# book_utils.py
# ============================
import os
import requests
import streamlit as st

KAKAO_API_URL = "https://dapi.kakao.com/v3/search/book"

def _get_api_key() -> str | None:
    """1) 환경변수 2) Streamlit Cloud secrets 둘 다 지원"""
    return os.getenv("KAKAO_API_KEY") or (
        st.secrets.get("KAKAO_API_KEY") if hasattr(st, "secrets") else None
    )

def _openlibrary_cover(isbn: str) -> str:
    """
    OpenLibrary 고해상도 커버 URL(L 사이즈).
    - ISBN이 없거나 커버가 없으면 1x1 투명 이미지가 내려올 수 있음 → 호출부에서 폴백 처리
    """
    if not isbn:
        return ""
    # L: large / M, S도 가능
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

def _looks_like_valid_image(url: str) -> bool:
    """
    원격 이미지 URL의 유효성을 가볍게 검사.
    - HEAD로 Content-Length가 1KB 이상인지 우선 확인
    - 없거나 너무 작으면 소용량 GET로 길이 확인
    """
    if not url:
        return False
    try:
        h = requests.head(url, allow_redirects=True, timeout=5)
        if h.status_code == 200:
            size = h.headers.get("Content-Length")
            if size and size.isdigit() and int(size) >= 1024:
                return True
        # 일부 서버는 HEAD를 제대로 처리하지 않음 → 소량 GET
        g = requests.get(url, stream=True, timeout=8)
        if g.status_code == 200:
            # 최대 16KB만 읽어서 길이 판정
            total = 0
            chunk_size = 4096
            for chunk in g.iter_content(chunk_size=chunk_size):
                if not chunk:
                    break
                total += len(chunk)
                if total >= 1024:
                    return True
                if total >= 16384:  # 16KB까지만 확인
                    break
    except Exception:
        return False
    return False

def _google_books_cover(isbn: str) -> str:
    """
    Google Books API를 통해 고해상도 커버 URL을 조회.
    - API 키 없이 사용 가능하지만, 속도나 안정성은 보장되지 않음.
    """
    if not isbn:
        return ""
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return ""
        
        # 가장 해상도가 높은 순서대로 링크를 찾음
        img_links = items[0].get("volumeInfo", {}).get("imageLinks", {})
        for size in ["extraLarge", "large", "medium", "small", "thumbnail"]:
            if size in img_links:
                # HTTP를 HTTPS로 변경
                return img_links[size].replace("http://", "https://")
    except Exception:
        return ""
    return ""

def search_books(query: str, size: int = 10):
    """제목/ISBN 자동 판단해서 카카오에서 책 검색한 뒤, 고화질 커버(URL)까지 구성."""
    q = (query or "").strip()
    if not q:
        return []

    api_key = _get_api_key()
    if not api_key:
        st.warning("카카오 API 키가 설정되지 않았어요. 환경변수 또는 st.secrets에 KAKAO_API_KEY를 넣어주세요.")
        return []

    # 숫자(하이픈 제외) 10자리 이상이면 ISBN으로 간주
    just_num = q.replace("-", "")
    target = "isbn" if just_num.isdigit() and len(just_num) >= 10 else "title"

    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": q, "target": target, "size": size}

    try:
        resp = requests.get(KAKAO_API_URL, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("documents", []) or []
    except Exception as e:
        st.error(f"도서 검색 중 오류: {e}")
        return []

    results = []
    for d in docs:
        # isbn은 "ISBN10 ISBN13" 형태일 수 있으므로 마지막 값을 사용
        raw_isbn = d.get("isbn") or ""
        if isinstance(raw_isbn, str):
            parts = raw_isbn.split()
            isbn = parts[-1] if parts else ""
        else:
            isbn = ""

        # 카카오 썸네일(작은 편)
        kakao_thumb = (d.get("thumbnail") or "").strip()

        # --- 커버 이미지 결정 로직 (화질 개선) ---
        # 1. OpenLibrary (고화질)
        # 2. Google Books (고화질)
        # 3. Kakao (썸네일)
        cover_url = _openlibrary_cover(isbn) if isbn else ""
        if not _looks_like_valid_image(cover_url):
            cover_url = _google_books_cover(isbn) if isbn else ""
            if not _looks_like_valid_image(cover_url):
                cover_url = kakao_thumb # 최종 폴백

        results.append(
            {
                "title": d.get("title", ""),
                "author": ", ".join(d.get("authors", []) or []),
                "cover_url": cover_url,
                "isbn": isbn,
            }
        )

    return results

# book_utils.py
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

        # ISBN이 있으면 OpenLibrary 고해상도 커버 우선 사용
        hq_cover = _openlibrary_cover(isbn) if isbn else ""
        cover_url = hq_cover or kakao_thumb  # 고화질 → 폴백 순서

        results.append(
            {
                "title": d.get("title", ""),
                "author": ", ".join(d.get("authors", []) or []),
                "cover_url": cover_url,
                "isbn": isbn,
            }
        )

    return results

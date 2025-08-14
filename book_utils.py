# book_utils.py — 카카오 도서 검색 API 버전
import os
import requests

# 환경변수에서 키 읽기 (없으면 빈 문자열)
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")

# (옵션) 검색 실패 시 보여줄 간단 더미 — 완전한 대체는 아님
FALLBACK_DUMMY = [
    {"title": "미움받을 용기", "author": "기시미 이치로", "cover_url": "https://covers.openlibrary.org/b/id/123456-L.jpg", "isbn": "9781234567890"},
    {"title": "아주 작은 습관의 힘", "author": "제임스 클리어", "cover_url": "https://covers.openlibrary.org/b/id/987654-L.jpg", "isbn": "9791187142542"},
    {"title": "데미안", "author": "헤르만 헤세", "cover_url": "https://covers.openlibrary.org/b/id/654321-L.jpg", "isbn": "9788970123456"},
]

def _kakao_search(query: str, size: int = 5, target: str | None = None):
    """카카오 책 검색 호출. target은 'title' 또는 'isbn' 등."""
    if not query or not KAKAO_API_KEY:
        return []

    url = "https://dapi.kakao.com/v3/search/book"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": size}
    if target:
        params["target"] = target

    try:
        res = requests.get(url, headers=headers, params=params, timeout=8)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return []

    docs = data.get("documents", [])
    results = []
    for d in docs:
        title = (d.get("title") or "").strip()
        authors = d.get("authors", [])
        author = ", ".join([a for a in authors if a]).strip()
        thumb = d.get("thumbnail") or ""

        # 카카오 응답의 isbn은 "ISBN10 ISBN13"처럼 공백으로 둘 다 올 수 있음 → 보통 마지막이 13자리
        raw_isbn = (d.get("isbn") or "").strip()
        isbn = raw_isbn.split()[-1] if raw_isbn else ""

        results.append({
            "title": title,
            "author": author,
            "cover_url": thumb,
            "isbn": isbn,
        })
    return results

def search_books(query: str, size: int = 5):
    """
    우리 앱에서 쓰는 통합 검색 함수.
    - 10~13자리 숫자(하이픈 제거)면 ISBN 우선 검색
    - 그 외에는 일반(제목/키워드) 검색
    반환: [{title, author, cover_url, isbn}, ...]
    """
    if not query:
        return []

    q = query.strip()
    digits = q.replace("-", "")
    # ISBN처럼 보이면 isbn target부터 시도
    if digits.isdigit() and 10 <= len(digits) <= 13:
        r = _kakao_search(digits, size=size, target="isbn")
        if r:
            return r
        # ISBN으로 못 찾으면 일반 검색으로 폴백
    r2 = _kakao_search(q, size=size, target=None)
    if r2:
        return r2

    # 키가 없거나 네트워크 문제인 경우 최소한의 경험 제공
    # (원하면 [] 리턴으로 바꿔도 됨)
    return [
        b for b in FALLBACK_DUMMY
        if q.lower() in b["title"].lower() or q in b["isbn"]
    ]

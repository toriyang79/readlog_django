#==========================
# ui_pages/create_post.py
#==========================

import streamlit as st
from book_utils import search_books          # 카카오 API 버전
from models import save_book_if_needed, create_post
from storage import save_uploaded_image

def page_create_post():
    st.subheader("📝 글쓰기 (1페이지=내 사진, 2페이지=책 표지 자동)")

    # --- 로그인 체크 ---
    if "user" not in st.session_state or not st.session_state.user:
        st.info("로그인 후 작성할 수 있어요.")
        return

    # --- 세션 변수 초기화 (검색 결과/선택값/중복방지 플래그) ---
    st.session_state.setdefault("search_results", [])
    st.session_state.setdefault("selected_book", None)
    st.session_state.setdefault("posting", False)

    # --- 카카오 책 검색(제목 또는 ISBN) ---
    q = st.text_input("🔎 카카오 책 검색 (제목 또는 ISBN)", key="book_query")

    if st.button("검색", key="search_btn"):
        with st.spinner("검색 중..."):
            st.session_state.search_results = search_books(q)
            st.session_state.selected_book = None  # 새 검색 시 선택 초기화

    results = st.session_state.search_results
    selected_book = st.session_state.selected_book

    if results:
        st.write("검색 결과:")
        idx = st.selectbox(
            "책 선택",
            list(range(len(results))),
            format_func=lambda i: f"{results[i]['title']} / {results[i].get('author','')} ({results[i].get('isbn','')})",
            key="book_select_idx",
        )
        selected_book = results[idx]
        st.session_state.selected_book = selected_book  # ✅ 선택 유지

        # 표지 미리보기
        if selected_book.get("cover_url"):
            st.image(
                selected_book["cover_url"],
                caption=f"책 표지 미리보기: {selected_book['title']}",
                use_column_width=True,
            )
        else:
            st.info("표지 이미지가 없는 도서예요.")
    else:
        # 검색어가 있었는데 결과가 비어 있는 경우 안내
        if q:
            st.warning("검색 결과가 없어요. 제목을 줄이거나 다른 키워드/ISBN으로 다시 시도해보세요.")

    # --- 업로드 & 감상 입력 ---
    up = st.file_uploader("내 사진 업로드 (jpg/png)", type=["jpg", "jpeg", "png"], key="upload_photo")
    text = st.text_area("한 줄 감상", placeholder="오늘 이 문장에서 마음이 움직였어요…", key="post_text")

    # --- 게시하기 ---
    if st.button("게시하기", use_container_width=True, disabled=st.session_state.posting, key="submit_post"):
        selected_book = st.session_state.selected_book
        if not up or not selected_book:
            st.warning("사진과 책을 모두 선택/입력해주세요.")
            return
        try:
            st.session_state.posting = True
            img_path = save_uploaded_image(up)
            book_id, cover_url_used = save_book_if_needed(
                selected_book["title"],
                selected_book.get("author"),
                selected_book.get("cover_url"),
                selected_book.get("isbn"),
            )
            create_post(
                user_id=st.session_state.user["id"],
                book_id=book_id,
                user_photo_url=img_path,
                book_cover_url_snapshot=cover_url_used,
                text=text,
            )
            st.success("게시 완료! 피드에서 확인해보세요.")
        except Exception as e:
            st.error(f"게시 실패: {e}")
        finally:
            st.session_state.posting = False

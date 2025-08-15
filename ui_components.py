# ============================
# ui_components.py  (공용 UI: 포스트 카드)
# ============================
import streamlit as st
import os
from PIL import Image

def _get(row, key, default=None):
    try:
        if hasattr(row, "keys") and key in row.keys():
            val = row[key]
        elif isinstance(row, dict):
            val = row.get(key, default)
        else:
            val = default
    except Exception:
        val = default
    return default if val is None else val

# ✅ 로컬 경로/URL 모두 안전하게 표시 (경로 깨짐, 읽기 실패 방지)
def _safe_show_image(src: str, width: int, center: bool = True):
    """로컬 경로/URL 모두 안전하게 표시 (URL은 완전 중앙정렬)"""
    if not src:
        st.info("이미지 파일이 없어요.")
        return
    src = str(src).replace("\\", "/")
    try:
        if src.startswith(("http://", "https://")):
            if center:
                # ✅ URL 이미지를 HTML로 가운데 정렬
                st.markdown(
                    f"<p style='text-align:center; margin:0;'><img src='{src}' width='{width}'></p>",
                    unsafe_allow_html=True,
                )
            else:
                st.image(src, width=width)
            return
        # 로컬 파일
        if os.path.exists(src):
            with Image.open(src) as img:
                # st.image는 좌측 정렬되므로, 중앙정렬이 필요하면
                # 바깥에서 columns([1,2,1])로 감싸 호출하세요.
                st.image(img, width=width)
        else:
            st.info(f"이미지 파일을 찾을 수 없어요: {src}")
    except Exception as e:
        st.warning(f"이미지를 표시하는 중 문제가 생겼어요: {e}")

def ui_post_card(row, key_prefix: str = "card"):
    from models import toggle_like, do_repost, list_comments, add_comment, add_notification

    nickname = _get(row, "nickname", "익명")
    profile_img = _get(row, "profile_image", None)
    created_at = _get(row, "created_at", "")
    book_title = _get(row, "book_title", "")
    book_author = _get(row, "book_author", "")
    user_photo_url = _get(row, "user_photo_url", None)
    book_cover_snapshot = _get(row, "book_cover_url_snapshot", None)
    text = _get(row, "text", "")
    like_count = _get(row, "like_count", 0)
    repost_count = _get(row, "repost_count", 0)
    post_id = _get(row, "id", None)
    author_user_id = _get(row, "user_id", None)

    # key 생성기 (접두어 + 컴포넌트명 + post_id)
    def k(name: str) -> str:
        return f"{key_prefix}_{name}_{post_id}"

    st.markdown("---")

    # 상단 메타(프로필)
    meta_l, meta_r = st.columns([1, 5])
    with meta_l:
        if profile_img:
            _safe_show_image(profile_img, width=48)
        st.caption(f"{nickname}")
    with meta_r:
        # ✅ 제목/작가: h2(요청), 중앙 정렬
        if book_title or book_author:
            st.markdown(
                f"<h3 style='text-align:center;margin:0.2rem 0 0.6rem 0;font-weight:700;'>{book_title} | 작가: {book_author}</h3>",
                unsafe_allow_html=True,
            )
        if created_at:
            st.caption(created_at)

    # ✅ 페이지 전환: 버튼 2개(가운데 나란히)
    page_key = k("page_mode")
    if page_key not in st.session_state:
        st.session_state[page_key] = "photo"

    wrap_l, wrap_c, wrap_r = st.columns([3, 4, 3])
    with wrap_c:
        btn_l, btn_r = st.columns([1, 1])
        with btn_l:
            if st.button("📷 사진", key=k("btn_photo"), use_container_width=True):
                st.session_state[page_key] = "photo"
        with btn_r:
            if st.button("📚 책 표지", key=k("btn_cover"), use_container_width=True):
                st.session_state[page_key] = "cover"

    page_mode = st.session_state[page_key]

    # ✅ 이미지 표시: 안전 함수 사용 + 가운데 정렬 + 고정 크기
    if page_mode == "photo":
        if user_photo_url:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                _safe_show_image(user_photo_url, width=400)  # 사진 400px
        else:
            st.info("사진이 없어요.")
    else:
        if book_cover_snapshot:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                _safe_show_image(book_cover_snapshot, width=200)  # 표지 300px
        else:
            st.info("책 표지 없음")

    # 닉네임(볼드) + 텍스트
    if text or nickname:
        st.markdown(f"**{nickname}** {text if text else ''}")

    # 액션 버튼
    a1, a2, _, _ = st.columns(4)
    with a1:
        if st.button(f"📖 BookLike {like_count}", key=k("like")):
            if not st.session_state.get("user"):
                st.warning("로그인 후 이용 가능합니다.")
            else:
                liked = toggle_like(st.session_state.user["id"], post_id)
                if liked:
                    add_notification(
                        to_user_id=author_user_id,
                        notif_type="like",
                        from_user_id=st.session_state.user["id"],
                        post_id=post_id,
                    )
                st.rerun()
    with a2:
        if st.button(f"📢 BookUp {repost_count}", key=k("repost")):
            if not st.session_state.get("user"):
                st.warning("로그인 후 이용 가능합니다.")
            else:
                new_re = do_repost(st.session_state.user["id"], post_id)
                if new_re:
                    add_notification(
                        to_user_id=author_user_id,
                        notif_type="repost",
                        from_user_id=st.session_state.user["id"],
                        post_id=post_id,
                    )
                st.rerun()

    # 댓글
    with st.expander("💬 댓글 보기/쓰기"):
        comments = list_comments(post_id) or []
        for c in comments:
            cnick = c["nickname"] if "nickname" in c.keys() else "익명"
            ctext = c["text"] if "text" in c.keys() else ""
            st.markdown(f"**{cnick}**: {ctext}")

        if st.session_state.get("user"):
            new_c = st.text_input("댓글 입력", key=k("comment_input"))
            if st.button("등록", key=k("comment_btn")):
                ctext = (new_c or "").strip()
                if ctext:
                    add_comment(st.session_state.user["id"], post_id, ctext)
                    add_notification(
                        to_user_id=author_user_id,
                        notif_type="comment",
                        from_user_id=st.session_state.user["id"],
                        post_id=post_id,
                    )
                    st.rerun()
        else:
            st.info("로그인 후 댓글을 작성할 수 있어요.")

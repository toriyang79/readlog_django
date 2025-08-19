# ============================
# ui_components.py  (공용 UI: 포스트 카드)
# ============================
import streamlit as st
import base64
import os
from PIL import Image
from storage import save_uploaded_image
from models import update_post, delete_post

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

def _safe_show_image(src: str, width: int = None, center: bool = True, fit_to_column: bool = False):
    """로컬 경로/URL 모두 안전하게 표시.
    - fit_to_column=True: PC에서는 최대 400px, 모바일에서는 꽉 차게 반응형 표시
    """
    if not src:
        st.info("이미지 파일이 없어요.")
        return

    # 1. 소스 결정 (URL or Base64)
    src_attr = ""
    if src.startswith(("http://", "https://")):
        src_attr = src
    elif os.path.exists(src):
        b64_string, mimetype = _get_image_data_for_cache(src)
        if b64_string is None:
            st.info(f"이미지 파일을 찾을 수 없어요: {src}")
            return
        src_attr = f"data:{mimetype};base64,{b64_string}"
    else:
        st.info(f"이미지 파일을 찾을 수 없어요: {src}")
        return

    # 2. 상황에 맞게 이미지 렌더링
    if fit_to_column:
        # 게시물 사진: CSS 클래스로 반응형 크기 조절
        st.markdown(f"<img src='{src_attr}' class='post-image'>", unsafe_allow_html=True)
    elif width:
        # 아바타: 고정 폭 이미지
        st.image(src, width=width)
    else:
        # 책 표지: 원본 크기 + 중앙 정렬
        st.markdown(f"<div style='text-align: center;'><img src='{src_attr}' style='max-width: 100%;'></div>", unsafe_allow_html=True)

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

    # 상단 메타(프로필) - 새 레이아웃
    p_col1, p_col2, p_col3 = st.columns([1, 3, 2])
    with p_col1:
        if profile_img:
            _safe_show_image(profile_img, width=48)
    with p_col2:
        st.markdown(f"<div style='height: 48px; display: flex; align-items: center;'><b>{nickname}</b></div>", unsafe_allow_html=True)
    with p_col3:
        st.markdown(f"<div style='height: 48px; display: flex; align-items: center; justify-content: flex-end; text-align: right;'><small>{created_at}</small></div>", unsafe_allow_html=True)

    # 제목/작가
    if book_title or book_author:
        st.markdown(
            f"<h3 style='text-align:center;margin:0.8rem 0;font-weight:700;'>{book_title} | 작가: {book_author}</h3>",
            unsafe_allow_html=True,
        )

    # ✅ 페이지 전환: 버튼 2개(한 줄 배열)
    page_key = k("page_mode")
    if page_key not in st.session_state:
        st.session_state[page_key] = "photo"

    btn_l, btn_r = st.columns(2)
    with btn_l:
        if st.button("📷 사진", key=k("btn_photo"), use_container_width=True):
            st.session_state[page_key] = "photo"
    with btn_r:
        if st.button("📚 책 표지", key=k("btn_cover"), use_container_width=True):
            st.session_state[page_key] = "cover"

    page_mode = st.session_state[page_key]

    # ✅ 이미지 표시: 반응형(모바일 최적화)
    if page_mode == "photo":
        if user_photo_url:
            _safe_show_image(user_photo_url, fit_to_column=True)
        else:
            st.info("사진이 없어요.")
    else:
        if book_cover_snapshot:
            # fit_to_column=False로 원본 크기 표시, columns로 중앙 정렬
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                _safe_show_image(book_cover_snapshot, fit_to_column=False)
        else:
            st.info("책 표지 없음")

    # 닉네임(볼드) + 텍스트
    if text or nickname:
        st.markdown(f"**{nickname}** {(text.replace('\n', '<br>') if text else '')}", unsafe_allow_html=True)

    # --- 액션 버튼 및 댓글 (모바일 최적화) ---
    comments = list_comments(post_id) or []
    comment_count = len(comments)

    # 댓글 표시 상태 (토글용)
    comment_key = k("show_comments")
    if comment_key not in st.session_state:
        st.session_state[comment_key] = False

    # 3열 레이아웃: 좋아요, 북마크, 댓글
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button(f"📖 Like {like_count}", key=k("like"), use_container_width=True):
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
        if st.button(f"📢 BookUp {repost_count}", key=k("repost"), use_container_width=True):
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
    with a3:
        # 댓글 버튼 클릭 시, 댓글 창 토글
        if st.button(f"💬 댓글 {comment_count}", key=k("comment_toggle"), use_container_width=True):
            st.session_state[comment_key] = not st.session_state[comment_key]

    # 댓글 창 (토글 상태에 따라 표시)
    if st.session_state[comment_key]:
        st.markdown("--- ") # 구분선
        for c in comments:
            cnick = _get(c, "nickname", "익명")
            ctext = _get(c, "text", "")
            st.markdown(f"**{cnick}**: {ctext}")

        if st.session_state.get("user"):
            new_c = st.text_input("댓글 입력", key=k("comment_input"), placeholder="따뜻한 댓글을 남겨주세요.")
            if st.button("등록", key=k("comment_btn"), use_container_width=True):
                ctext = (new_c or "").strip()
                if ctext:
                    add_comment(st.session_state.user["id"], post_id, ctext)
                    add_notification(
                        to_user_id=author_user_id,
                        notif_type="comment",
                        from_user_id=st.session_state.user["id"],
                        post_id=post_id,
                    )
                    # 댓글 등록 후, 토글 닫고 새로고침
                    st.session_state[comment_key] = False
                    st.rerun()
        else:
            st.info("로그인 후 댓글을 작성할 수 있어요.")

    # ✏️ 게시글 수정 / 🗑️ 삭제 (작성자 전용, 기존 expander 유지)
    is_owner = bool(st.session_state.get("user")) and (st.session_state.user["id"] == author_user_id)
    if is_owner:
        with st.expander("✏️ 게시글 수정 / 🗑️ 삭제"):
            new_text = st.text_area("내용 수정", value=text or "", key=k("edit_text"))
            new_img = st.file_uploader("사진 바꾸기(선택)", type=["png", "jpg", "jpeg"], key=k("edit_img"))
            col_u, col_d = st.columns(2)

            # 수정(저장)
            with col_u:
                if st.button("저장", key=k("edit_save")):
                    new_path = None
                    if new_img is not None:
                        new_path = save_uploaded_image(new_img)
                    ok = update_post(
                        st.session_state.user["id"],
                        post_id,
                        new_text=new_text,
                        new_user_photo_url=new_path,
                    )
                    if ok:
                        st.success("수정 완료")
                        st.rerun()
                    else:
                        st.error("수정 권한이 없어요.")

            # 삭제
            with col_d:
                confirm_del = st.checkbox("정말 삭제할래요?", key=k("del_confirm"))
                if st.button("삭제", key=k("del_btn"), type="secondary", disabled=not confirm_del):
                    ok = delete_post(st.session_state.user["id"], post_id)
                    if ok:
                        st.success("삭제 완료")
                        # 피드로 이동
                        st.session_state["nav"] = "feed"
                        st.rerun()
                    else:
                        st.error("삭제 권한이 없어요.")

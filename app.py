# ============================
# app.py (최종본)
# ============================
import streamlit as st

# ✅ set_page_config는 반드시 가장 먼저!
st.set_page_config(
    page_title="마음이 문장을 따라 흐르는 곳, 📙 리드로그",
    page_icon="🎈",
    layout="centered",
)

# 이후 모듈 import
from db import init_db, ensure_dirs
from auth_ui import ui_auth
from ui_pages.feed import page_feed
from ui_pages.create_post import page_create_post
from ui_pages.profile import page_profile
from models import top_bookup_posts


# 내비게이션 옵션
NAV_OPTIONS = ("feed", "write", "profile")
NAV_LABELS = {
    "feed": "📰 피드",
    "write": "📝 글쓰기",
    "profile": "👤 프로필",
}


def main():
    # 디렉터리/DB 보장
    ensure_dirs()
    init_db()

    # 세션 기본값
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)
    st.session_state.setdefault("nav", "feed")  # ← 현재 화면 상태

    # 스타일 (라디오를 탭처럼 보이게)
    st.markdown(
        """
        <style>
          div[role="radiogroup"] > label {
            margin-right: 12px; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 8px 14px; background: #f7f7ff; font-weight: 700;
            cursor: pointer;
          }
          /* 라디오 원형 아이콘만 숨김 (클릭은 라벨 영역이 처리) */
          div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none !important; }
          div[role="radiogroup"] > label[data-selected="true"] {
            background: #eef2ff; border-color:#6366f1; color:#3730a3;
            box-shadow: 0 1px 0 0 #ef4444 inset;
          }

          /* --- Force columns to stay horizontal on mobile --- */
          div[data-testid="stHorizontalBlock"] {
              flex-wrap: nowrap !important;
          }
          /* --- Allow columns to shrink on mobile --- */
          div[data-testid="stHorizontalBlock"] > div {
              flex-shrink: 1 !important;
              min-width: 0 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 로그인/회원 UI
    ui_auth()

    # -----------------------------
    # 사이드바: 리드로그 사용법(유튜브) 미리보기 + 새창 링크
    # -----------------------------
    with st.sidebar:
        with st.expander("📺 리드로그 사용법 (미리보기)"):
            st.video("https://youtu.be/VhTpKDROP2M")
            st.markdown(
                "<a href='https://youtu.be/VhTpKDROP2M' target='_blank'>새 창에서 보기</a>",
                unsafe_allow_html=True,
            )

        st.divider()

        # -----------------------------
        # 사이드바: BookUp Top 목록
        # -----------------------------
        st.markdown("### 📢 BookUp Top")
        try:
            top_rows = top_bookup_posts(limit=7)
        except Exception:
            top_rows = []
        if not top_rows:
            st.caption("아직 BookUp된 게시물이 없어요.")
        else:
            for rank, r in enumerate(top_rows, start=1):
                title = (r["book_title"] or "(제목 없음)").strip()
                nickname = r["nickname"]
                count = r["repost_count"]
                btn_label = f"{rank}. {title} · {nickname}  ({count})"
                if st.button(btn_label, key=f"sb_top_{r['post_id']}"):
                    st.session_state["nav"] = "feed"
                    st.session_state["feed_sort"] = "bookup"
                    st.rerun()

    # ✅ 모바일 고정 한 줄: 3분할 버튼 네비게이션
    cur_nav = st.session_state.get("nav", "feed")
    col_f, col_w, col_p = st.columns(3)
    with col_f:
        if st.button("📰 피드", use_container_width=True, type=("primary" if cur_nav == "feed" else "secondary")):
            st.session_state["nav"] = "feed"
            st.rerun()
    with col_w:
        if st.button("📝 글쓰기", use_container_width=True, type=("primary" if cur_nav == "write" else "secondary")):
            st.session_state["nav"] = "write"
            st.rerun()
    with col_p:
        if st.button("👤 프로필", use_container_width=True, type=("primary" if cur_nav == "profile" else "secondary")):
            st.session_state["nav"] = "profile"
            st.rerun()

    nav = st.session_state.get("nav", "feed")

    # 화면 라우팅
    if nav == "feed":
        page_feed()
    elif nav == "write":
        page_create_post()
    else:
        page_profile()


if __name__ == "__main__":
    main()

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
          div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { display: none; }
          div[role="radiogroup"] > label[data-selected="true"] {
            background: #eef2ff; border-color:#6366f1; color:#3730a3;
            box-shadow: 0 1px 0 0 #ef4444 inset;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 로그인/회원 UI
    ui_auth()

    # ✅ 라디오 내비게이션 (프로그램이 제어 가능)
    nav = st.radio(
        "메뉴",
        options=NAV_OPTIONS,
        index=NAV_OPTIONS.index(st.session_state.get("nav", "feed")),
        format_func=lambda x: NAV_LABELS[x],
        horizontal=True,
        key="nav",
        label_visibility="collapsed",
    )

    # 화면 라우팅
    if nav == "feed":
        page_feed()
    elif nav == "write":
        page_create_post()
    else:
        page_profile()


if __name__ == "__main__":
    main()

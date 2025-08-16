# ============================
# app.py
# ============================
import streamlit as st

# ✅ set_page_config는 반드시 가장 먼저!
st.set_page_config(
    page_title="마음이 문장을 따라 흐르는 곳, 📙 리드로그",
    page_icon="🎈",
    layout="centered",
)

# 이제 다른 모듈들 import
from db import init_db, ensure_dirs
from auth_ui import ui_auth
from ui_pages.feed import page_feed
from ui_pages.create_post import page_create_post
from ui_pages.profile import page_profile


def main():
    ensure_dirs()
    init_db()

    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    st.markdown("""
    <style>
      .stTabs [role="tablist"] { gap: 12px; }
      .stTabs [role="tab"] {
        font-size: 1.05rem; font-weight: 700;
        padding: 10px 16px; border-radius: 12px;
        background: #f7f7ff; border: 1px solid #E5E7EB; color:#1f2937;
      }
      .stTabs [aria-selected="true"] {
        background: #eef2ff; border-color:#6366f1; color:#3730a3;
        box-shadow: 0 1px 0 0 #ef4444 inset;
      }
    </style>
    """, unsafe_allow_html=True)

    ui_auth()

    tab1, tab2, tab3 = st.tabs(["📰 피드", "📝 글쓰기", "👤 프로필"])
    with tab1:
        page_feed()
    with tab2:
        page_create_post()
    with tab3:
        page_profile()


if __name__ == "__main__":
    main()

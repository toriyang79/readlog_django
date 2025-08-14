# ============================
# app.py
# ============================
import streamlit as st
from db import init_db, ensure_dirs
from auth_ui import ui_auth
from ui_pages.feed import page_feed
from ui_pages.create_post import page_create_post
from ui_pages.profile import page_profile


def main():
    st.set_page_config(page_title="마음이 문장을 따라 흐르는 곳, 📙 리드로그", page_icon="🎈", layout="centered")
    ensure_dirs()
    init_db()

    # 세션 기본값
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    # ✅ 탭 꾸미기 (CSS)
    st.markdown("""
    <style>
      /* 탭 간격 */
      .stTabs [role="tablist"] { gap: 12px; }
      /* 탭 버튼 스타일 */
      .stTabs [role="tab"] {
        font-size: 1.05rem; font-weight: 700;
        padding: 10px 16px; border-radius: 12px;
        background: #f7f7ff; border: 1px solid #E5E7EB; color:#1f2937;
      }
      /* 선택된 탭 */
      .stTabs [aria-selected="true"] {
        background: #eef2ff; border-color:#6366f1; color:#3730a3;
        box-shadow: 0 1px 0 0 #ef4444 inset;  /* 아래 빨간 포커스 라인 */
      }
    </style>
    """, unsafe_allow_html=True)

    # 로그인/회원가입
    ui_auth()

    # ✅ 본문 탭 (아이콘 라벨)
    tab1, tab2, tab3 = st.tabs(["📰 피드", "📝 글쓰기", "👤 프로필"])
    with tab1:
        page_feed()
    with tab2:
        page_create_post()
    with tab3:
        page_profile()


if __name__ == "__main__":
    main()
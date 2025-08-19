# ============================
# pages/feed.py
# ============================
import streamlit as st
from models import list_posts
from ui_components import ui_post_card

def page_feed():
    # --- 정렬 버튼 (모바일 최적화) ---
    st.session_state.setdefault("feed_sort", "latest")
    sort_latest, sort_bookup = st.columns(2)

    with sort_latest:
        is_latest = st.session_state.feed_sort == "latest"
        if st.button("🕒 최신순", use_container_width=True, type="primary" if is_latest else "secondary"):
            st.session_state.feed_sort = "latest"
            st.rerun()

    with sort_bookup:
        is_bookup = st.session_state.feed_sort == "bookup"
        if st.button("📢 BookUp 많은 순", use_container_width=True, type="primary" if is_bookup else "secondary"):
            st.session_state.feed_sort = "bookup"
            st.rerun()

    rows = list_posts(limit=50, sort=st.session_state.feed_sort)
    for i, r in enumerate(rows):
        ui_post_card(r, key_prefix=f"feed_{i}")
# ============================
# pages/feed.py
# ============================
import streamlit as st
from models import list_posts
from ui_components import ui_post_card

def page_feed():
    # 정렬 옵션: 최신순 / BookUp 많은 순
    sort = st.radio(
        "정렬",
        options=("latest", "bookup"),
        format_func=lambda x: "🕒 최신순" if x == "latest" else "📢 BookUp 많은 순",
        horizontal=True,
        key="feed_sort",
    )
    rows = list_posts(limit=50, sort=sort)
    for i, r in enumerate(rows):
        ui_post_card(r, key_prefix=f"feed_{i}")
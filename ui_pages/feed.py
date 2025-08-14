# ============================
# pages/feed.py
# ============================
import streamlit as st
from models import list_posts
from ui_components import ui_post_card

def page_feed():
    rows = list_posts(limit=50)
    for i, r in enumerate(rows):
        ui_post_card(r, key_prefix=f"feed_{i}")
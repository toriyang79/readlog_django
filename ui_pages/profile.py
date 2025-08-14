# ============================
# ui_pages/profile.py
# ============================
import streamlit as st
from models import my_posts, my_reposts
from ui_components import ui_post_card

def page_profile():
    # 로그인 체크
    if "user" not in st.session_state or not st.session_state.user:
        st.info("로그인 후 이용할 수 있어요.")
        return

    uid = st.session_state.user["id"]

    st.subheader("내가 쓴 글")
    mine = my_posts(uid)
    if not mine:
        st.info("내가 쓴 글이 아직 없어요.")
    else:
        for i, r in enumerate(mine):
            ui_post_card(r, key_prefix=f"my_{i}")

    st.subheader("내가 책갈피한 글")
    reps = my_reposts(uid)
    if not reps:
        st.info("책갈피한 글이 아직 없어요.")
    else:
        for i, r in enumerate(reps):
            ui_post_card(r, key_prefix=f"rp_{i}")

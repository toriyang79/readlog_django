# auth_ui.py  ← 이 파일 내용 전체 교체
import streamlit as st
from models import (
    get_user_by_email,
    create_user,
    unread_notifications_count,
    mark_all_notifications_read,
)
from utils import hash_password  # 로그인 검증에 사용


def ui_auth():
    # 세션 기본값 보장 (없으면 생성)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    st.sidebar.header("🔐 로그인/회원가입")

    # 이미 로그인된 경우
    if st.session_state.user:
        me = st.session_state.user
        st.sidebar.success(f"안녕하세요, {me['nickname']}님!")

        # 알림 배지
        st.session_state.unread_count = unread_notifications_count(me["id"]) or 0
        if st.session_state.unread_count:
            if st.sidebar.button(f"🔔 알림({st.session_state.unread_count}) 확인"):
                mark_all_notifications_read(me["id"])
                st.session_state.unread_count = 0
                st.rerun()

        if st.sidebar.button("로그아웃"):
            st.session_state.user = None
            st.rerun()

        st.sidebar.divider()
        return  # 로그인 상태면 여기서 종료

    # === 로그인/회원가입 탭 (로그인 안 된 경우에만 보임) ===
    tab_login, tab_signup = st.sidebar.tabs(["로그인", "회원가입"])

    # 로그인 탭
    with tab_login:
        email = st.text_input("이메일", key="login_email")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            row = get_user_by_email(email)
            if row and row["password_hash"] == hash_password(pw):
                st.session_state.user = {
                    "id": row["id"],
                    "email": row["email"],
                    "nickname": row["nickname"],
                    "profile_image": row["profile_image"],
                }
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

    # 회원가입 탭
    with tab_signup:
        email_s = st.text_input("이메일", key="signup_email")
        nickname_s = st.text_input("닉네임", key="signup_nick")
        pw_s = st.text_input("비밀번호", type="password", key="signup_pw")
        if st.button("회원가입"):
            if not email_s or not nickname_s or not pw_s:
                st.warning("모든 칸을 입력해주세요.")
            elif get_user_by_email(email_s):
                st.error("이미 가입된 이메일입니다.")
            else:
                try:
                    create_user(email_s, pw_s, nickname_s)
                    st.success("회원가입 성공! 이제 로그인 해주세요.")
                except Exception as e:
                    st.error(f"회원가입 실패: {e}")

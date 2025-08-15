# auth_ui.py
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from models import (
    get_user_by_email,
    create_user,
    unread_notifications_count,
    mark_all_notifications_read,
)
from utils import hash_password  # 로그인 검증에 사용


def ui_auth():
    # ===== 쿠키 매니저 (암호화) =====
    cookies = EncryptedCookieManager(
        prefix="readlog_",  # 쿠키 키 접두사
        # 안전하게 하려면 st.secrets 또는 환경변수로 관리하세요.
        password=st.secrets.get("COOKIE_PASSWORD", "readlog-dev-cookie-secret"),
    )
    if not cookies.ready():
        # 초기 로드 타이밍 문제 방지 (필수)
        st.stop()

    # ===== 세션 기본값 =====
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    # ===== 쿠키로 자동 로그인 복원 =====
    # 브라우저 새로고침/재접속 시 쿠키에 저장된 이메일을 이용해 세션 복원
    if st.session_state.user is None:
        cookie_email = cookies.get("user_email")
        if cookie_email:
            row = get_user_by_email(cookie_email)
            if row:
                st.session_state.user = {
                    "id": row["id"],
                    "email": row["email"],
                    "nickname": row["nickname"],
                    "profile_image": row["profile_image"],
                }

    st.sidebar.header("🔐 로그인/회원가입")

    # ===== 이미 로그인된 경우 =====
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

        # 로그아웃 → 세션/쿠키 모두 제거
        if st.sidebar.button("로그아웃"):
            st.session_state.user = None
            cookies.delete("user_email")
            cookies.save()
            st.rerun()

        st.sidebar.divider()
        return  # 로그인 상태면 여기서 종료

    # ===== 로그인/회원가입 탭 (비로그인 시) =====
    tab_login, tab_signup = st.sidebar.tabs(["로그인", "회원가입"])

    # 로그인 탭
    with tab_login:
        email = st.text_input("이메일", key="login_email")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            row = get_user_by_email(email)
            if row and row["password_hash"] == hash_password(pw):
                # 세션 저장
                st.session_state.user = {
                    "id": row["id"],
                    "email": row["email"],
                    "nickname": row["nickname"],
                    "profile_image": row["profile_image"],
                }
                # ✅ 쿠키 저장 (브라우저 새로고침/재실행에도 유지)
                cookies["user_email"] = row["email"]
                cookies.save()

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

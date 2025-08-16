# ============================
# auth_ui.py
# ============================
import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from utils import hash_password
from models import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    unread_notifications_count,
    mark_all_notifications_read,
)

def _cookie_password() -> str:
    return os.getenv("COOKIE_PASSWORD") or getattr(st, "secrets", {}).get(
        "COOKIE_PASSWORD", "readlog_dev_secret"
    )

def _set_session_user(row):
    st.session_state.user = {
        "id": row["id"],
        "email": row["email"],
        "nickname": row["nickname"],
        "profile_image": row["profile_image"],
    }

def ui_auth():
    # ✅ 쿠키 매니저 준비(함수 안에서)
    cookies = EncryptedCookieManager(prefix="readlog_", password=_cookie_password())
    if not cookies.ready():
        st.warning("쿠키를 준비 중입니다. 잠시 후 새로고침 해주세요.")
        st.stop()

    # 기본 세션 키
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    # 🔁 쿠키(user_id)로 자동 로그인 복원
    if st.session_state.user is None:
        uid = cookies.get("user_id")
        if uid:
            try:
                uid = str(uid).strip()
                if uid.isdigit():  # 숫자인 경우만 처리
                    row = get_user_by_id(int(uid))
                    if row:
                        _set_session_user(row)
            except Exception:
                pass

    st.sidebar.header("🔐 로그인/회원가입")

    # 로그인된 상태
    if st.session_state.user:
        me = st.session_state.user
        st.sidebar.success(f"안녕하세요, {me['nickname']}님!")

        try:
            st.session_state.unread_count = unread_notifications_count(me["id"]) or 0
        except Exception:
            st.session_state.unread_count = 0

        if st.session_state.unread_count:
            if st.sidebar.button(f"🔔 알림({st.session_state.unread_count}) 확인"):
                mark_all_notifications_read(me["id"])
                st.session_state.unread_count = 0
                st.rerun()

        # (로그아웃 버튼 핸들러)
        if st.sidebar.button("로그아웃"):
            # 1) 세션 사용자 비우기
            st.session_state.user = None
            st.session_state.unread_count = 0

            # 2) 쿠키 확실히 비우기
            cookies["user_id"] = ""        # 빈 값으로 덮어쓰기
            if "user_id" in cookies:       # 키 자체 삭제
                del cookies["user_id"]
            cookies.save()

            st.success("로그아웃되었습니다.")
            st.rerun()

        st.sidebar.divider()
        return

    # 비로그인 → 로그인/회원가입 탭
    tab_login, tab_signup = st.sidebar.tabs(["로그인", "회원가입"])

    with tab_login:
        email = st.text_input("이메일", key="login_email")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", type="primary"):
            row = get_user_by_email(email)
            if row and row["password_hash"] == hash_password(pw):
                _set_session_user(row)
                cookies["user_id"] = str(row["id"])  # ✅ 쿠키 저장
                cookies.save()
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

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

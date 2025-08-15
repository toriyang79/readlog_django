# ============================
# auth_ui.py
# ============================
import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from utils import hash_password
from models import (
    get_user_by_email,
    get_user_by_id,                 # ✅ 쿠키 복원용
    create_user,
    unread_notifications_count,
    mark_all_notifications_read,
)

# ----------------------------
# 🔐 암호화 쿠키 매니저 (전역 1개)
# ----------------------------
def _cookie_password() -> str:
    # 환경변수 > st.secrets > 기본값
    return os.getenv("COOKIE_PASSWORD") or getattr(st, "secrets", {}).get(
        "COOKIE_PASSWORD", "readlog_dev_secret"
    )

cookies = EncryptedCookieManager(prefix="readlog_", password=_cookie_password())
if not cookies.ready():
    # 초기 로드 타이밍 문제 회피
    st.stop()

# ----------------------------
# 공용: 세션에 유저 dict 넣는 도우미
# ----------------------------
def _set_session_user(row):
    st.session_state.user = {
        "id": row["id"],
        "email": row["email"],
        "nickname": row["nickname"],
        "profile_image": row["profile_image"],
    }

# ----------------------------
# UI
# ----------------------------
def ui_auth():
    # 세션 기본값
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("unread_count", 0)

    # 1) 🔁 쿠키(user_id)로 자동 로그인 복원
    if st.session_state.user is None:
        uid = cookies.get("user_id")
        if uid:
            try:
                row = get_user_by_id(int(uid))
                if row:
                    _set_session_user(row)
            except Exception:
                pass

    # 사이드바 UI
    st.sidebar.header("🔐 로그인/회원가입")

    # 2) 이미 로그인된 상태
    if st.session_state.user:
        me = st.session_state.user
        st.sidebar.success(f"안녕하세요, {me['nickname']}님!")

        # 알림 배지
        try:
            st.session_state.unread_count = unread_notifications_count(me["id"]) or 0
        except Exception:
            st.session_state.unread_count = 0

        if st.session_state.unread_count:
            if st.sidebar.button(f"🔔 알림({st.session_state.unread_count}) 확인"):
                mark_all_notifications_read(me["id"])
                st.session_state.unread_count = 0
                st.rerun()

        # 로그아웃: 세션/쿠키 모두 제거
        if st.sidebar.button("로그아웃"):
            st.session_state.user = None
            cookies.pop("user_id", None)
            cookies.save()
            st.success("로그아웃되었습니다.")
            st.rerun()

        st.sidebar.divider()
        return  # 로그인 상태면 끝

    # 3) 비로그인 상태 → 로그인/회원가입 탭
    tab_login, tab_signup = st.sidebar.tabs(["로그인", "회원가입"])

    # 로그인 탭
    with tab_login:
        email = st.text_input("이메일", key="login_email")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", type="primary"):
            row = get_user_by_email(email)
            if row and row["password_hash"] == hash_password(pw):
                # 세션 저장
                _set_session_user(row)
                # ✅ 쿠키에 user_id 저장 → 새로고침/재접속 유지
                cookies["user_id"] = str(row["id"])
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

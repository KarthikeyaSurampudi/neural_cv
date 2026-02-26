# auth/middleware.py  — keeps session_state only, no cookie logic

import streamlit as st
from typing import Dict

from auth.jwt_handler import (
    create_tokens,
    verify_access_token,
    verify_refresh_token,
    is_token_expired,
)

_ACCESS = "jwt_access"
_REFRESH = "jwt_refresh"


def login_user(user: Dict):
    access, refresh = create_tokens(
        user_id=str(user["user_id"]),
        username=user["username"],
        is_admin=user["is_admin"],
    )
    st.session_state[_ACCESS] = access
    st.session_state[_REFRESH] = refresh
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    return access, refresh          # caller will persist these


def logout_user():
    for key in [_ACCESS, _REFRESH, "authenticated", "user"]:
        st.session_state.pop(key, None)


def require_auth() -> bool:
    access = st.session_state.get(_ACCESS)
    refresh = st.session_state.get(_REFRESH)

    if not access:
        return False

    if not is_token_expired(access):
        if verify_access_token(access):
            return True

    if refresh and not is_token_expired(refresh):
        payload = verify_refresh_token(refresh)
        if payload:
            user_id = payload["sub"]
            user_data = st.session_state.get("user")
            if user_data:
                access, _ = create_tokens(
                    user_id, user_data["username"], user_data["is_admin"]
                )
                st.session_state[_ACCESS] = access
                return True

    logout_user()
    return False
"""入口页：登录 / 注册。

登录态保存在 st.session_state（token / user），其余页面通过 api_client 复用。
"""
import sys
from pathlib import Path

# 让 pages/* 也能 import 本目录下的 api_client
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

import api_client
from api_client import ApiError

st.set_page_config(page_title="实习招聘管理系统", page_icon="💼", layout="wide")


# ---------- 业务动作 ----------

def do_login(username: str, password: str):
    try:
        data = api_client.post(
            "/api/auth/login", form={"username": username, "password": password}
        )
    except ApiError as e:
        st.error(f"登录失败：{e.message}")
        return
    st.session_state.token = data["access_token"]
    st.session_state.user = data["user"]
    st.rerun()


def do_register(username: str, password: str, role: str, name: str, email: str):
    try:
        api_client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": password,
                "role": role,
                "name": name or None,
                "email": email or None,
            },
        )
    except ApiError as e:
        st.error(f"注册失败：{e.message}")
        return
    st.success("注册成功，正在自动登录…")
    do_login(username, password)


# ---------- 页面 ----------

st.title("💼 实习招聘管理系统")

user = st.session_state.get("user")

if user:
    role = user.get("role")
    role_label = "HR（招聘方）" if role == "hr" else "学生（求职者）"
    display_name = user.get("name") or user.get("username")

    st.success(f"欢迎回来，{display_name}！当前身份：{role_label}")

    st.markdown("### 快速入口")
    col_left, col_right = st.columns(2)
    with col_left:
        st.page_link("pages/jobs.py", label="📋 职位列表 / 投递")
        if role == "student":
            st.page_link("pages/my_applications.py", label="📄 我的投递")
    with col_right:
        if role == "hr":
            st.page_link("pages/job_manage.py", label="🛠️ 职位管理")
            st.page_link("pages/application_manage.py", label="📥 投递管理")

    st.divider()
    if st.button("退出登录"):
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.rerun()
else:
    st.markdown("请先登录，或注册新账号。")
    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录")
            if submitted:
                if not username or not password:
                    st.error("请填写用户名和密码")
                else:
                    do_login(username, password)

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("用户名")
            password = st.text_input(
                "密码", type="password", help="至少 8 位，且同时包含字母和数字"
            )
            confirm = st.text_input("确认密码", type="password")
            role = st.radio(
                "身份",
                ["student", "hr"],
                format_func=lambda v: "学生" if v == "student" else "HR",
                horizontal=True,
            )
            name = st.text_input("姓名（选填）")
            email = st.text_input("邮箱（选填）")
            submitted = st.form_submit_button("注册")
            if submitted:
                if not username or not password:
                    st.error("请填写用户名和密码")
                elif password != confirm:
                    st.error("两次输入的密码不一致")
                else:
                    do_register(username, password, role, name, email)

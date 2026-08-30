"""统一请求封装：自动附带 token、统一错误处理与分页响应解析。

后端 base URL 通过环境变量 API_BASE_URL 配置，默认 http://localhost:8000。
登录态（token / user）保存在 st.session_state 中，由 streamlit_app.py 写入，
其余页面通过 require_login / require_role 复用。

注意：Streamlit 页面里的 HTTP 请求发生在 Streamlit 服务端（而非浏览器），
因此无需为后端配置 CORS 白名单。
"""
import os

import requests
import streamlit as st

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")

# 投递状态 -> 中文标签（多个页面复用）
STATUS_LABELS = {
    "applied": "已投递",
    "screening": "筛选中",
    "interview": "面试",
    "offer": "已录用",
    "rejected": "已拒绝",
}

# HR 可把投递状态流转到的目标状态（不含初始态 applied）
STATUS_FLOW = ["screening", "interview", "offer", "rejected"]


class ApiError(Exception):
    """后端返回的业务 / 校验错误，message 已转成可读文案。"""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------- 请求底层 ----------

def _headers() -> dict:
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _flatten_detail(detail) -> str:
    """把 FastAPI 的 422 校验错误（list[dict]）压成一行可读文案。"""
    if isinstance(detail, list):
        parts = []
        for err in detail:
            if isinstance(err, dict):
                loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
                msg = err.get("msg", "")
                parts.append(f"{loc}: {msg}" if loc else str(msg))
            else:
                parts.append(str(err))
        return "；".join(parts)
    return str(detail)


def _handle(resp: requests.Response):
    if resp.status_code == 204:
        return None
    try:
        data = resp.json()
    except ValueError:
        data = {}
    if resp.status_code >= 400:
        # 登录态失效时顺带清掉本地会话，下次交互即被引导回登录页
        if resp.status_code == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
        raise ApiError(_flatten_detail(data.get("detail", "请求失败")), resp.status_code)
    return data


def _request(method: str, path: str, **kwargs):
    kwargs.setdefault("timeout", 10)
    try:
        resp = requests.request(method, BASE_URL + path, headers=_headers(), **kwargs)
    except requests.exceptions.ConnectionError:
        raise ApiError(f"无法连接后端服务（{BASE_URL}），请确认后端已启动。")
    except requests.exceptions.Timeout:
        raise ApiError("请求后端超时。")
    return _handle(resp)


# ---------- 常用方法 ----------

def get(path: str, **params) -> dict:
    return _request("GET", path, params=params)


def post(path: str, json=None, form=None) -> dict:
    if form is not None:
        return _request("POST", path, data=form)
    return _request("POST", path, json=json)


def put(path: str, json=None) -> dict:
    return _request("PUT", path, json=json)


def delete(path: str) -> dict:
    return _request("DELETE", path)


# ---------- 登录态工具 ----------

def require_login() -> dict:
    """页面守卫：未登录则提示并停止渲染。返回当前用户 dict。"""
    user = st.session_state.get("user")
    token = st.session_state.get("token")
    if not user or not token:
        st.warning("请先登录后再访问。")
        st.page_link("streamlit_app.py", label="前往登录")
        st.stop()
    return user


def require_role(role: str) -> dict:
    """页面守卫：校验角色，不匹配则提示并停止。"""
    user = require_login()
    if user.get("role") != role:
        label = "HR" if role == "hr" else "学生"
        st.error(f"该页面仅限「{label}」访问。")
        st.stop()
    return user


def render_sidebar():
    """在侧边栏展示当前登录用户与退出按钮（各页面复用）。"""
    user = st.session_state.get("user")
    if not user:
        return
    role_label = "HR" if user.get("role") == "hr" else "学生"
    display_name = user.get("name") or user.get("username")
    with st.sidebar:
        st.markdown(f"**{display_name}**（{role_label}）")
        if st.button("退出登录", use_container_width=True):
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
            st.rerun()


def list_my_jobs(user_id: int) -> list:
    """拉取当前 HR 发布的所有岗位：跨页取全量后按 hr_id 过滤。"""
    all_jobs = []
    page = 1
    while True:
        data = get("/api/jobs", page=page, page_size=100)
        all_jobs.extend(data.get("items", []))
        if page >= data.get("pages", 0):
            break
        page += 1
    return [j for j in all_jobs if j.get("hr_id") == user_id]

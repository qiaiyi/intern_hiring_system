"""学生：我的投递记录。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import api_client
from api_client import ApiError, require_role

st.set_page_config(page_title="我的投递", page_icon="📄", layout="wide")

user = require_role("student")
api_client.render_sidebar()

st.title("📄 我的投递")

PAGE_SIZE = 10
if "my_apps_page" not in st.session_state:
    st.session_state.my_apps_page = 1

try:
    data = api_client.get(
        "/api/my/applications", page=st.session_state.my_apps_page, page_size=PAGE_SIZE
    )
except ApiError as e:
    st.error(e.message)
    st.stop()

items = data.get("items", [])
total = data.get("total", 0)
page = data.get("page", 1)
pages = max(data.get("pages", 0), 1)

c1, c2, c3 = st.columns([1, 3, 1])
with c1:
    if st.button("⬅️ 上一页", disabled=page <= 1):
        st.session_state.my_apps_page -= 1
        st.rerun()
with c2:
    st.markdown(f"共 **{total}** 条投递 · 第 {page}/{pages} 页")
with c3:
    if st.button("下一页 ➡️", disabled=page >= pages):
        st.session_state.my_apps_page += 1
        st.rerun()

st.divider()

if not items:
    st.info("你还没有投递任何岗位，去「职位列表」看看吧。")
else:
    for app in items:
        job = app["job"]
        status = app["status"]
        with st.container(border=True):
            st.markdown(f"### {job['title']}")
            st.markdown(f"状态：`{api_client.STATUS_LABELS.get(status, status)}`")
            st.caption(f"投递时间：{app['created_at'][:10]}")

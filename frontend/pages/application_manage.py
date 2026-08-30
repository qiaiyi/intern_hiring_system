"""HR：查看自己岗位的投递列表，并更新投递状态。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import api_client
from api_client import ApiError, require_role

st.set_page_config(page_title="投递管理", page_icon="📥", layout="wide")

user = require_role("hr")
api_client.render_sidebar()

st.title("📥 投递管理")

try:
    my_jobs = api_client.list_my_jobs(user["id"])
except ApiError as e:
    st.error(e.message)
    st.stop()

if not my_jobs:
    st.info("你还没有发布岗位。")
    st.stop()

job_options = {f"#{j['id']} · {j['title']}": j["id"] for j in my_jobs}
selected_label = st.selectbox("选择岗位", list(job_options.keys()))
job_id = job_options[selected_label]

PAGE_SIZE = 10
if "app_mgmt_page" not in st.session_state:
    st.session_state.app_mgmt_page = 1

try:
    data = api_client.get(
        f"/api/jobs/{job_id}/applications",
        page=st.session_state.app_mgmt_page,
        page_size=PAGE_SIZE,
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
        st.session_state.app_mgmt_page -= 1
        st.rerun()
with c2:
    st.markdown(f"共 **{total}** 份投递 · 第 {page}/{pages} 页")
with c3:
    if st.button("下一页 ➡️", disabled=page >= pages):
        st.session_state.app_mgmt_page += 1
        st.rerun()

st.divider()

if not items:
    st.info("该岗位暂无投递。")
else:
    for app in items:
        student = app["student"]
        display_name = student.get("name") or student.get("username")
        current = app["status"]
        with st.container(border=True):
            st.markdown(f"### {display_name}")
            st.caption(
                f"账号：{student['username']} · 邮箱：{student.get('email') or '—'} · "
                f"投递时间：{app['created_at'][:10]}"
            )
            st.markdown(f"当前状态：`{api_client.STATUS_LABELS.get(current, current)}`")

            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                default_idx = (
                    api_client.STATUS_FLOW.index(current)
                    if current in api_client.STATUS_FLOW
                    else 0
                )
                new_status = st.selectbox(
                    "更新状态",
                    api_client.STATUS_FLOW,
                    index=default_idx,
                    format_func=lambda v: api_client.STATUS_LABELS[v],
                    key=f"status_{app['id']}",
                )
            with col_btn:
                if st.button("更新", key=f"update_{app['id']}"):
                    try:
                        api_client.put(
                            f"/api/applications/{app['id']}",
                            json={"status": new_status},
                        )
                        st.success("已更新。")
                        st.rerun()
                    except ApiError as e:
                        st.error(e.message)

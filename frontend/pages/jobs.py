"""职位列表 / 详情 / 投递（所有登录用户可见，学生可投递）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import api_client
from api_client import ApiError, require_login

st.set_page_config(page_title="职位列表", page_icon="📋", layout="wide")

user = require_login()
api_client.render_sidebar()

st.title("📋 职位列表")

PAGE_SIZE = 5
if "jobs_page" not in st.session_state:
    st.session_state.jobs_page = 1

try:
    data = api_client.get("/api/jobs", page=st.session_state.jobs_page, page_size=PAGE_SIZE)
except ApiError as e:
    st.error(e.message)
    st.stop()

items = data.get("items", [])
total = data.get("total", 0)
page = data.get("page", 1)
pages = max(data.get("pages", 0), 1)

# 顶部翻页
c1, c2, c3 = st.columns([1, 3, 1])
with c1:
    if st.button("⬅️ 上一页", disabled=page <= 1):
        st.session_state.jobs_page -= 1
        st.rerun()
with c2:
    st.markdown(f"共 **{total}** 个岗位 · 第 {page}/{pages} 页")
with c3:
    if st.button("下一页 ➡️", disabled=page >= pages):
        st.session_state.jobs_page += 1
        st.rerun()

st.divider()

if not items:
    st.info("暂无岗位。")
else:
    for job in items:
        with st.expander(f"**{job['title']}**", expanded=False):
            st.markdown("**职位描述**")
            st.write(job["description"])
            st.markdown("**任职要求**")
            st.write(job["requirements"])
            st.caption(f"发布于 {job['created_at'][:10]}")

            if user.get("role") == "student":
                if st.button("投递该岗位", key=f"apply_{job['id']}"):
                    try:
                        api_client.post(f"/api/jobs/{job['id']}/apply")
                        st.success("投递成功！可在「我的投递」中查看进度。")
                    except ApiError as e:
                        if e.status_code == 400:
                            st.info(e.message)  # 已投递过，友好提示
                        else:
                            st.error(e.message)
            else:
                st.caption("HR 账号无需投递，可在「职位管理」中维护岗位。")

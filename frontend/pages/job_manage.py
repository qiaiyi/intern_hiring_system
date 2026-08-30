"""HR：发布 / 编辑 / 删除自己发布的岗位。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import api_client
from api_client import ApiError, require_role

st.set_page_config(page_title="职位管理", page_icon="🛠️", layout="wide")

user = require_role("hr")
api_client.render_sidebar()

st.title("🛠️ 职位管理")

# 发布新岗位
with st.expander("➕ 发布新岗位", expanded=True):
    with st.form("create_job"):
        title = st.text_input("职位名称")
        description = st.text_area("职位描述")
        requirements = st.text_area("任职要求")
        submitted = st.form_submit_button("发布")
        if submitted:
            if not title or not description or not requirements:
                st.error("职位名称、描述、任职要求均为必填。")
            else:
                try:
                    api_client.post(
                        "/api/jobs",
                        json={
                            "title": title,
                            "description": description,
                            "requirements": requirements,
                        },
                    )
                    st.success("发布成功！")
                    st.rerun()
                except ApiError as e:
                    st.error(e.message)

st.subheader("我发布的岗位")

try:
    my_jobs = api_client.list_my_jobs(user["id"])
except ApiError as e:
    st.error(e.message)
    st.stop()

if not my_jobs:
    st.info("你还没有发布任何岗位。")
else:
    for job in my_jobs:
        with st.expander(f"**{job['title']}**", expanded=False):
            st.caption(f"发布于 {job['created_at'][:10]} · 岗位 ID {job['id']}")

            with st.form(f"edit_{job['id']}"):
                new_title = st.text_input("职位名称", value=job["title"], key=f"title_{job['id']}")
                new_desc = st.text_area("职位描述", value=job["description"], key=f"desc_{job['id']}")
                new_req = st.text_area("任职要求", value=job["requirements"], key=f"req_{job['id']}")
                save = st.form_submit_button("保存修改")
                if save:
                    try:
                        api_client.put(
                            f"/api/jobs/{job['id']}",
                            json={
                                "title": new_title,
                                "description": new_desc,
                                "requirements": new_req,
                            },
                        )
                        st.success("已保存。")
                        st.rerun()
                    except ApiError as e:
                        st.error(e.message)

            st.markdown("---")
            confirm = st.checkbox("我确认要删除该岗位", key=f"confirm_del_{job['id']}")
            if st.button("🗑️ 删除岗位", key=f"del_{job['id']}", disabled=not confirm):
                try:
                    api_client.delete(f"/api/jobs/{job['id']}")
                    st.success("已删除。")
                    st.rerun()
                except ApiError as e:
                    st.error(e.message)

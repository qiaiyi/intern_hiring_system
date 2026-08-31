"""问题 16-20 回归测试：JWT 时区、并发竞态兜底、删除岗位外键、字段长度上限。

对应《后端问题修复记录.txt》：
- 问题 16  JWT exp 使用本地时间导致有效期失控（改为 UTC）
- 问题 17  删除有投递记录的岗位返回 500（现 400）
- 问题 18  注册 / 更新岗位的并发竞态与唯一约束兜底（现 400）
- 问题 19  字段超长导致 MySQL DataError 500（现 422）
- 问题 20  超 72 字节密码使 bcrypt 抛 ValueError 500（现 422）
"""
import asyncio
from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

import helpers
from app.api.auth import create_access_token
from app.core.config import ALGORITHM, EXPIRE_MINUTES, SECRET_KEY


# ---------- 问题 16：JWT exp 时区 ----------

async def test_token_expiry_encoded_as_utc(client):
    """exp 应按 UTC 编码：解码出的过期时刻应约等于 现在UTC + EXPIRE_MINUTES。

    修复前用本地 naive 时间，东八区下解码出的过期时刻会比预期晚约 8 小时。
    """
    token = create_access_token({"sub": "1", "role": "student"})
    claims = jose_jwt.get_unverified_claims(token)
    exp_utc = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    # 允许 2 分钟的编码误差
    assert abs((exp_utc - expected).total_seconds()) < 120


# ---------- 问题 17：删除有投递记录的岗位 ----------

async def test_delete_job_with_applications_returns_400(client):
    """岗位已有投递记录时删除应返回 400（外键 RESTRICT），而非 500。"""
    hr_token, _ = await helpers.create_user(client, "hr17", role="hr")
    stu_token, _ = await helpers.create_user(client, "stu17", role="student")
    hr_headers = helpers.auth_headers(hr_token)

    resp = await client.post(
        "/api/jobs",
        json={"title": "有投递的岗位", "description": "d", "requirements": "r"},
        headers=hr_headers,
    )
    job_id = resp.json()["id"]
    await client.post(
        f"/api/jobs/{job_id}/apply", headers=helpers.auth_headers(stu_token)
    )

    resp = await client.delete(f"/api/jobs/{job_id}", headers=hr_headers)
    assert resp.status_code == 400, resp.text
    assert "投递" in resp.json()["detail"]

    # 岗位仍存在
    detail = await client.get(f"/api/jobs/{job_id}")
    assert detail.status_code == 200


async def test_delete_job_without_applications_succeeds(client):
    """没有投递记录的岗位应可正常删除（204）。"""
    hr_token, _ = await helpers.create_user(client, "hr17b", role="hr")
    hr_headers = helpers.auth_headers(hr_token)

    resp = await client.post(
        "/api/jobs",
        json={"title": "无投递的岗位", "description": "d", "requirements": "r"},
        headers=hr_headers,
    )
    job_id = resp.json()["id"]
    resp = await client.delete(f"/api/jobs/{job_id}", headers=hr_headers)
    assert resp.status_code == 204
    assert (await client.get(f"/api/jobs/{job_id}")).status_code == 404


# ---------- 问题 18：注册 / 更新岗位的唯一约束兜底 ----------

async def test_register_duplicate_race(client):
    """并发注册同名用户：唯一约束兜底，恰一个 201 + 一个 400，不会 500。"""

    async def _register():
        return await helpers.register_user(client, "race_user", "password123")

    resp1, resp2 = await asyncio.gather(_register(), _register())
    assert {resp1.status_code, resp2.status_code} == {201, 400}, (
        resp1.status_code,
        resp2.status_code,
        resp1.text,
        resp2.text,
    )


async def test_update_job_duplicate_title_returns_400(client):
    """HR 把岗位改名为自己已发布的同名岗位应返回 400，而非 500。"""
    hr_token, _ = await helpers.create_user(client, "hr18", role="hr")
    hr_headers = helpers.auth_headers(hr_token)

    for title in ("岗位A", "岗位B"):
        resp = await client.post(
            "/api/jobs",
            json={"title": title, "description": "d", "requirements": "r"},
            headers=hr_headers,
        )
        assert resp.status_code == 201, resp.text
    job_b_id = (await client.get("/api/jobs", params={"page_size": 100})).json()
    job_b_id = [
        j["id"] for j in job_b_id["items"] if j["title"] == "岗位B"
    ][0]

    resp = await client.put(
        f"/api/jobs/{job_b_id}",
        json={"title": "岗位A", "description": "d", "requirements": "r"},
        headers=hr_headers,
    )
    assert resp.status_code == 400, resp.text


# ---------- 问题 19：字段长度上限（422 而非 500） ----------

async def test_register_username_too_long_returns_422(client):
    resp = await helpers.register_user(client, "u" * 81, "password123")
    assert resp.status_code == 422


async def test_create_job_title_too_long_returns_422(client):
    hr_token, _ = await helpers.create_user(client, "hr19", role="hr")
    resp = await client.post(
        "/api/jobs",
        json={
            "title": "岗" * 101,  # 超过数据库 String(100)
            "description": "d",
            "requirements": "r",
        },
        headers=helpers.auth_headers(hr_token),
    )
    assert resp.status_code == 422


async def test_create_job_description_too_long_returns_422(client):
    hr_token, _ = await helpers.create_user(client, "hr19b", role="hr")
    resp = await client.post(
        "/api/jobs",
        json={
            "title": "标题",
            "description": "d" * 1001,  # 超过数据库 String(1000)
            "requirements": "r",
        },
        headers=helpers.auth_headers(hr_token),
    )
    assert resp.status_code == 422


# ---------- 问题 20：密码字节上限 ----------

async def test_register_password_over_72_bytes_returns_422(client):
    """超 72 字节的密码应返回 422（bcrypt 5.0 会抛 ValueError，此前为 500）。

    用多字节字符构造：60 个中文 = 180 字节 > 72，但字符数只有 60。
    """
    resp = await helpers.register_user(client, "longpwd", "好" * 60)
    assert resp.status_code == 422

"""auth 接口测试：注册、登录、JWT 解析与认证边界。"""
import helpers
from auth import create_access_token


async def test_register_default_role_student(client):
    resp = await helpers.register_user(client, "alice", "password123")
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["role"] == "student"
    assert "id" in data
    assert "password_hash" not in data  # 响应体不得泄露密码哈希


async def test_register_with_hr_role(client):
    resp = await helpers.register_user(client, "boss", "password123", role="hr")
    assert resp.status_code == 201
    assert resp.json()["role"] == "hr"


async def test_register_invalid_role(client):
    resp = await helpers.register_user(client, "bad", "password123", role="admin")
    assert resp.status_code == 422


async def test_register_duplicate_username(client):
    await helpers.register_user(client, "alice", "password123")
    resp = await helpers.register_user(client, "alice", "password123")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户名已存在"


async def test_register_weak_password_too_short(client):
    """密码长度不足 8 位应返回 422。"""
    resp = await helpers.register_user(client, "short", "a1b2")
    assert resp.status_code == 422


async def test_register_weak_password_no_letter(client):
    """密码不含字母应返回 422。"""
    resp = await helpers.register_user(client, "nolett", "12345678")
    assert resp.status_code == 422


async def test_register_weak_password_no_digit(client):
    """密码不含数字应返回 422。"""
    resp = await helpers.register_user(client, "nodigit", "abcdefgh")
    assert resp.status_code == 422


async def test_login_success(client):
    await helpers.register_user(client, "alice", "password123")
    resp = await helpers.login_user(client, "alice", "password123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "alice"


async def test_login_wrong_password(client):
    await helpers.register_user(client, "alice", "password123")
    resp = await helpers.login_user(client, "alice", "wrong")
    assert resp.status_code == 401


async def test_login_nonexistent_user(client):
    resp = await helpers.login_user(client, "ghost", "password123")
    assert resp.status_code == 401


async def test_protected_endpoint_without_token(client):
    resp = await client.post(
        "/api/jobs",
        json={"title": "t", "description": "d", "requirements": "r"},
    )
    assert resp.status_code == 401


async def test_protected_endpoint_with_invalid_token(client):
    resp = await client.post(
        "/api/jobs",
        json={"title": "t", "description": "d", "requirements": "r"},
        headers=helpers.auth_headers("not-a-real-token"),
    )
    assert resp.status_code == 401


async def test_token_without_sub_returns_401(client):
    """问题1 回归：合法但缺少 sub 的 JWT 应返回 401，而非 500。"""
    token = create_access_token({"role": "student"})
    resp = await client.get(
        "/api/my/applications", headers=helpers.auth_headers(token)
    )
    assert resp.status_code == 401


async def test_token_with_unknown_user_returns_401(client):
    """sub 指向不存在的用户时应返回 401。"""
    token = create_access_token({"sub": "99999", "role": "student"})
    resp = await client.get(
        "/api/my/applications", headers=helpers.auth_headers(token)
    )
    assert resp.status_code == 401

"""测试辅助函数：注册、登录、生成认证头等，供各测试模块复用。"""


def auth_headers(token: str) -> dict:
    """把 access_token 组装成 Authorization 请求头。"""
    return {"Authorization": f"Bearer {token}"}


async def register_user(client, username: str, password: str, role: str | None = None):
    """注册用户。role 为 None 时走 schema 默认值（student）。"""
    payload = {"username": username, "password": password}
    if role is not None:
        payload["role"] = role
    return await client.post("/api/auth/register", json=payload)


async def login_user(client, username: str, password: str):
    """登录（OAuth2 表单方式），返回原始响应。"""
    return await client.post(
        "/api/auth/login", data={"username": username, "password": password}
    )


async def get_token(client, username: str, password: str) -> str:
    """登录并返回 access_token。"""
    resp = await login_user(client, username, password)
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def create_user(client, username: str, password: str = "pass123", role: str = "student"):
    """注册并登录，返回 (access_token, 注册返回的用户信息)。"""
    resp = await register_user(client, username, password, role)
    assert resp.status_code == 201, resp.text
    token = await get_token(client, username, password)
    return token, resp.json()

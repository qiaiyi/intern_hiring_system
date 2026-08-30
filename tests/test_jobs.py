"""jobs 接口测试：岗位 CRUD、权限控制与列表分页。"""
import helpers


async def _hr(client, username="boss"):
    token, _ = await helpers.create_user(client, username, "password123", role="hr")
    return token


async def _student(client, username="stu"):
    token, _ = await helpers.create_user(client, username, "password123", role="student")
    return token


def _job_payload(title="后端实习生", description="d", requirements="r"):
    return {"title": title, "description": description, "requirements": requirements}


async def test_create_job_requires_auth(client):
    resp = await client.post("/api/jobs", json=_job_payload())
    assert resp.status_code == 401


async def test_create_job_requires_hr(client):
    token = await _student(client)
    resp = await client.post(
        "/api/jobs", json=_job_payload(), headers=helpers.auth_headers(token)
    )
    assert resp.status_code == 403


async def test_create_job_success(client):
    token = await _hr(client)
    resp = await client.post(
        "/api/jobs", json=_job_payload(), headers=helpers.auth_headers(token)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "后端实习生"
    assert data["hr_id"] == 1


async def test_create_duplicate_job_rejected(client):
    """同一 HR 发布同名岗位应被数据库唯一约束拒绝（返回 400/409）。"""
    token = await _hr(client)
    headers = helpers.auth_headers(token)
    first = await client.post("/api/jobs", json=_job_payload(), headers=headers)
    assert first.status_code == 201

    second = await client.post("/api/jobs", json=_job_payload(), headers=headers)
    # 唯一约束冲突：MySQL 抛 IntegrityError → 需应用层转成 4xx
    assert second.status_code in (400, 409)


async def test_create_same_title_different_hr_allowed(client):
    """不同 HR 可以发布同名岗位（唯一约束是 hr_id + title 组合）。"""
    hr1 = await _hr(client, "boss_a")
    hr2 = await _hr(client, "boss_b")
    resp1 = await client.post(
        "/api/jobs", json=_job_payload(), headers=helpers.auth_headers(hr1)
    )
    resp2 = await client.post(
        "/api/jobs", json=_job_payload(), headers=helpers.auth_headers(hr2)
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201


async def test_list_jobs_empty(client):
    resp = await client.get("/api/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_jobs_pagination(client):
    token = await _hr(client)
    headers = helpers.auth_headers(token)
    for i in range(3):
        resp = await client.post(
            "/api/jobs", json=_job_payload(title=f"job{i}"), headers=headers
        )
        assert resp.status_code == 201

    page1 = (await client.get("/api/jobs", params={"page": 1, "page_size": 2})).json()
    assert page1["total"] == 3
    assert page1["pages"] == 2
    assert len(page1["items"]) == 2

    page2 = (await client.get("/api/jobs", params={"page": 2, "page_size": 2})).json()
    assert len(page2["items"]) == 1


async def test_get_job(client):
    token = await _hr(client)
    created = (
        await client.post(
            "/api/jobs", json=_job_payload(), headers=helpers.auth_headers(token)
        )
    ).json()
    resp = await client.get(f"/api/jobs/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "后端实习生"


async def test_get_job_not_found(client):
    resp = await client.get("/api/jobs/999")
    assert resp.status_code == 404


async def test_update_job_success(client):
    token = await _hr(client)
    headers = helpers.auth_headers(token)
    created = (await client.post("/api/jobs", json=_job_payload(), headers=headers)).json()
    resp = await client.put(
        f"/api/jobs/{created['id']}", json=_job_payload(title="new title"), headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "new title"


async def test_update_job_not_owner(client):
    owner = await _hr(client, "boss1")
    other = await _hr(client, "boss2")
    created = (
        await client.post("/api/jobs", json=_job_payload(), headers=helpers.auth_headers(owner))
    ).json()
    resp = await client.put(
        f"/api/jobs/{created['id']}",
        json=_job_payload(title="x"),
        headers=helpers.auth_headers(other),
    )
    assert resp.status_code == 403


async def test_update_job_not_found(client):
    token = await _hr(client)
    resp = await client.put(
        "/api/jobs/999", json=_job_payload(), headers=helpers.auth_headers(token)
    )
    assert resp.status_code == 404


async def test_delete_job_success(client):
    token = await _hr(client)
    headers = helpers.auth_headers(token)
    created = (await client.post("/api/jobs", json=_job_payload(), headers=headers)).json()
    resp = await client.delete(f"/api/jobs/{created['id']}", headers=headers)
    assert resp.status_code == 204
    resp2 = await client.get(f"/api/jobs/{created['id']}")
    assert resp2.status_code == 404


async def test_delete_job_not_owner(client):
    owner = await _hr(client, "boss1")
    other = await _hr(client, "boss2")
    created = (
        await client.post("/api/jobs", json=_job_payload(), headers=helpers.auth_headers(owner))
    ).json()
    resp = await client.delete(
        f"/api/jobs/{created['id']}", headers=helpers.auth_headers(other)
    )
    assert resp.status_code == 403

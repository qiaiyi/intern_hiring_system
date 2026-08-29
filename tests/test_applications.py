"""applications 接口测试：投递、我的投递、岗位投递列表、状态更新与权限控制。"""
import asyncio
import helpers


async def _hr(client, username="boss"):
    token, _ = await helpers.create_user(client, username, "password123", role="hr")
    return token


async def _student(client, username="stu"):
    token, _ = await helpers.create_user(client, username, "password123", role="student")
    return token


async def _job(client, hr_token, title="后端实习生"):
    resp = await client.post(
        "/api/jobs",
        json={"title": title, "description": "d", "requirements": "r"},
        headers=helpers.auth_headers(hr_token),
    )
    return resp.json()


async def test_apply_requires_student(client):
    hr = await _hr(client)
    job = await _job(client, hr)
    resp = await client.post(
        f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(hr)
    )
    assert resp.status_code == 403


async def test_apply_success(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    resp = await client.post(
        f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "applied"
    assert data["job"]["id"] == job["id"]
    assert data["job"]["title"] == job["title"]
    assert data["student"]["username"] == "stu"


async def test_apply_job_not_found(client):
    stu = await _student(client)
    resp = await client.post(
        "/api/jobs/999/apply", headers=helpers.auth_headers(stu)
    )
    assert resp.status_code == 404


async def test_apply_duplicate(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    headers = helpers.auth_headers(stu)
    await client.post(f"/api/jobs/{job['id']}/apply", headers=headers)
    resp = await client.post(f"/api/jobs/{job['id']}/apply", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "你已投递过该岗位"


async def test_apply_duplicate_race(client):
    """并发投递同一岗位：唯一约束兜底，最终仅产生一条投递记录。"""
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    headers = helpers.auth_headers(stu)

    async def _apply():
        return await client.post(f"/api/jobs/{job['id']}/apply", headers=headers)

    resp1, resp2 = await asyncio.gather(_apply(), _apply())
    codes = sorted([resp1.status_code, resp2.status_code])
    assert codes == [201, 400], codes
    assert {resp1.status_code, resp2.status_code} == {201, 400}

    # 库里只有一条投递记录
    lst = await client.get("/api/my/applications", headers=headers)
    assert lst.json()["total"] == 1


async def test_my_applications(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    await client.post(
        f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
    )
    resp = await client.get("/api/my/applications", headers=helpers.auth_headers(stu))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["job"]["id"] == job["id"]
    assert data["items"][0]["job"]["title"] == job["title"]


async def test_list_job_applications_includes_student_info(client):
    """HR 查投递列表应能看到投递人的姓名/邮箱，而非仅 student_id。"""
    hr = await _hr(client)
    stu_token, _ = await helpers.create_user(
        client, "stu", "password123", role="student", name="张三", email="zs@mail.com"
    )
    job = await _job(client, hr)
    await client.post(
        f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu_token)
    )
    resp = await client.get(
        f"/api/jobs/{job['id']}/applications", headers=helpers.auth_headers(hr)
    )
    assert resp.status_code == 200
    student = resp.json()["items"][0]["student"]
    assert student["username"] == "stu"
    assert student["name"] == "张三"
    assert student["email"] == "zs@mail.com"


async def test_my_applications_requires_student(client):
    hr = await _hr(client)
    resp = await client.get("/api/my/applications", headers=helpers.auth_headers(hr))
    assert resp.status_code == 403


async def test_list_job_applications(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    await client.post(
        f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
    )
    resp = await client.get(
        f"/api/jobs/{job['id']}/applications", headers=helpers.auth_headers(hr)
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_list_job_applications_not_owner(client):
    hr = await _hr(client, "boss1")
    other = await _hr(client, "boss2")
    job = await _job(client, hr)
    resp = await client.get(
        f"/api/jobs/{job['id']}/applications", headers=helpers.auth_headers(other)
    )
    assert resp.status_code == 403


async def test_list_job_applications_job_not_found(client):
    hr = await _hr(client)
    resp = await client.get(
        "/api/jobs/999/applications", headers=helpers.auth_headers(hr)
    )
    assert resp.status_code == 404


async def test_update_status_success(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    app = (
        await client.post(
            f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
        )
    ).json()
    resp = await client.put(
        f"/api/applications/{app['id']}",
        json={"status": "interview"},
        headers=helpers.auth_headers(hr),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "interview"


async def test_update_status_not_owner(client):
    hr = await _hr(client, "boss1")
    other = await _hr(client, "boss2")
    stu = await _student(client)
    job = await _job(client, hr)
    app = (
        await client.post(
            f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
        )
    ).json()
    resp = await client.put(
        f"/api/applications/{app['id']}",
        json={"status": "interview"},
        headers=helpers.auth_headers(other),
    )
    assert resp.status_code == 403


async def test_update_status_not_found(client):
    hr = await _hr(client)
    resp = await client.put(
        "/api/applications/999",
        json={"status": "interview"},
        headers=helpers.auth_headers(hr),
    )
    assert resp.status_code == 404


async def test_update_status_invalid_enum(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    app = (
        await client.post(
            f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
        )
    ).json()
    resp = await client.put(
        f"/api/applications/{app['id']}",
        json={"status": "xxx"},
        headers=helpers.auth_headers(hr),
    )
    assert resp.status_code == 422


async def test_update_status_cannot_applied(client):
    hr = await _hr(client)
    stu = await _student(client)
    job = await _job(client, hr)
    app = (
        await client.post(
            f"/api/jobs/{job['id']}/apply", headers=helpers.auth_headers(stu)
        )
    ).json()
    resp = await client.put(
        f"/api/applications/{app['id']}",
        json={"status": "applied"},
        headers=helpers.auth_headers(hr),
    )
    assert resp.status_code == 422

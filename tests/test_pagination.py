"""分页参数与分页响应结构测试（问题6 相关）。"""
import pytest


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page_size": 0},
        {"page_size": -5},
        {"page_size": 101},
    ],
)
async def test_invalid_page_params_return_422(client, params):
    resp = await client.get("/api/jobs", params=params)
    assert resp.status_code == 422


async def test_page_size_100_allowed(client):
    resp = await client.get("/api/jobs", params={"page_size": 100})
    assert resp.status_code == 200


async def test_page_structure(client):
    resp = await client.get("/api/jobs", params={"page": 1, "page_size": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"items", "total", "page", "page_size", "pages"}
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0

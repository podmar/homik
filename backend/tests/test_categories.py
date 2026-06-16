import pytest
from httpx import AsyncClient


@pytest.fixture
async def category_id(client, auth):
    """A second category — Food is always seeded."""
    resp = await client.post("/categories", json={"name": "Cleaning"}, headers=auth)
    return resp.json()["id"]


async def test_list_returns_seeded_food(client, auth):
    resp = await client.get("/categories", headers=auth)
    assert resp.status_code == 200
    assert any(cat["name"] == "Food" for cat in resp.json())


async def test_create_category(client, auth):
    resp = await client.post("/categories", json={"name": "Cleaning"}, headers=auth)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Cleaning"


async def test_create_duplicate_name_returns_409(client, auth):
    await client.post("/categories", json={"name": "Cleaning"}, headers=auth)
    resp = await client.post("/categories", json={"name": "Cleaning"}, headers=auth)
    assert resp.status_code == 409


async def test_update_category(client, auth, category_id):
    resp = await client.patch(f"/categories/{category_id}", json={"name": "Toiletries"}, headers=auth)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Toiletries"


async def test_delete_category(client, auth, category_id):
    resp = await client.delete(f"/categories/{category_id}", headers=auth)
    assert resp.status_code == 204
    names = [cat["name"] for cat in (await client.get("/categories", headers=auth)).json()]
    assert "Cleaning" not in names


async def test_cannot_delete_category_with_items(client: AsyncClient, auth, category_id):
    await client.post("/items", json={"name": "Soap", "unit": "bar", "category_id": category_id}, headers=auth)
    resp = await client.delete(f"/categories/{category_id}", headers=auth)
    assert resp.status_code == 409


async def test_isolation_cannot_update_other_household_category(client: AsyncClient, auth, other_auth, category_id):
    resp = await client.patch(f"/categories/{category_id}", json={"name": "Stolen"}, headers=other_auth)
    assert resp.status_code == 404


async def test_isolation_cannot_delete_other_household_category(client: AsyncClient, auth, other_auth, category_id):
    resp = await client.delete(f"/categories/{category_id}", headers=other_auth)
    assert resp.status_code == 404

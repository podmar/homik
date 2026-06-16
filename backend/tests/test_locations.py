import pytest
from httpx import AsyncClient


@pytest.fixture
async def location_id(client, auth):
    """A second location — Pantry is always seeded; tests that delete need two."""
    resp = await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    return resp.json()["id"]


@pytest.fixture
async def item_id(client, auth):
    resp = await client.post("/items", json={"name": "Milk", "unit": "litre"}, headers=auth)
    return resp.json()["id"]


async def test_list_returns_seeded_pantry(client, auth):
    resp = await client.get("/locations", headers=auth)
    assert resp.status_code == 200
    assert any(loc["name"] == "Pantry" for loc in resp.json())


async def test_create_location(client, auth):
    resp = await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Fridge"


async def test_create_duplicate_name_returns_409(client, auth):
    await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    resp = await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    assert resp.status_code == 409


async def test_update_location(client, auth, location_id):
    resp = await client.patch(f"/locations/{location_id}", json={"name": "Deep Freeze"}, headers=auth)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Deep Freeze"


async def test_delete_location(client, auth, location_id):
    resp = await client.delete(f"/locations/{location_id}", headers=auth)
    assert resp.status_code == 204
    names = [loc["name"] for loc in (await client.get("/locations", headers=auth)).json()]
    assert "Fridge" not in names


async def test_cannot_delete_last_location(client, auth):
    pantry_id = (await client.get("/locations", headers=auth)).json()[0]["id"]
    resp = await client.delete(f"/locations/{pantry_id}", headers=auth)
    assert resp.status_code == 409


async def test_delete_location_with_batches_requires_move_to(client: AsyncClient, auth, location_id, item_id):
    await client.post(f"/items/{item_id}/batches", json={"quantity": 2, "location_id": location_id}, headers=auth)
    resp = await client.delete(f"/locations/{location_id}", headers=auth)
    assert resp.status_code == 409


async def test_delete_location_moves_batches(client: AsyncClient, auth, location_id, item_id):
    pantry_id = next(
        loc["id"] for loc in (await client.get("/locations", headers=auth)).json()
        if loc["name"] == "Pantry"
    )
    await client.post(f"/items/{item_id}/batches", json={"quantity": 2, "location_id": location_id}, headers=auth)

    resp = await client.delete(f"/locations/{location_id}?move_to={pantry_id}", headers=auth)
    assert resp.status_code == 204

    batches = (await client.get(f"/items/{item_id}/batches", headers=auth)).json()
    assert len(batches) == 1
    assert batches[0]["location_id"] == pantry_id
    assert batches[0]["quantity"] == 2


async def test_delete_location_merges_batches_on_collision(client: AsyncClient, auth, location_id, item_id):
    pantry_id = next(
        loc["id"] for loc in (await client.get("/locations", headers=auth)).json()
        if loc["name"] == "Pantry"
    )
    # Same item, same default expiry → moving Fridge batch to Pantry should merge.
    await client.post(f"/items/{item_id}/batches", json={"quantity": 3, "location_id": pantry_id}, headers=auth)
    await client.post(f"/items/{item_id}/batches", json={"quantity": 2, "location_id": location_id}, headers=auth)

    resp = await client.delete(f"/locations/{location_id}?move_to={pantry_id}", headers=auth)
    assert resp.status_code == 204

    batches = (await client.get(f"/items/{item_id}/batches", headers=auth)).json()
    assert len(batches) == 1
    assert batches[0]["quantity"] == 5


async def test_delete_location_move_to_same_location_returns_400(client: AsyncClient, auth, location_id, item_id):
    await client.post(f"/items/{item_id}/batches", json={"quantity": 1, "location_id": location_id}, headers=auth)
    resp = await client.delete(f"/locations/{location_id}?move_to={location_id}", headers=auth)
    assert resp.status_code == 400


async def test_isolation_cannot_update_other_household_location(client: AsyncClient, auth, other_auth):
    pantry_id = (await client.get("/locations", headers=auth)).json()[0]["id"]
    resp = await client.patch(f"/locations/{pantry_id}", json={"name": "Stolen"}, headers=other_auth)
    assert resp.status_code == 404


async def test_isolation_cannot_delete_other_household_location(client: AsyncClient, auth, other_auth, location_id):
    resp = await client.delete(f"/locations/{location_id}", headers=other_auth)
    assert resp.status_code == 404

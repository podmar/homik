import pytest
from httpx import AsyncClient


@pytest.fixture
async def item_id(client, auth):
    resp = await client.post(
        "/items", json={"name": "Milk", "unit": "litre"}, headers=auth
    )
    return resp.json()["id"]


async def test_create_item(client, auth):
    resp = await client.post(
        "/items", json={"name": "Beans", "unit": "can"}, headers=auth
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Beans"


async def test_list_items(client, auth, item_id):
    resp = await client.get("/items", headers=auth)
    assert resp.status_code == 200
    assert any(i["id"] == item_id for i in resp.json())


async def test_list_items_filter_by_name(client, auth):
    await client.post(
        "/items", json={"name": "Whole Milk", "unit": "litre"}, headers=auth
    )
    await client.post(
        "/items", json={"name": "Oat Milk", "unit": "litre"}, headers=auth
    )
    await client.post("/items", json={"name": "Butter", "unit": "g"}, headers=auth)
    resp = await client.get("/items?name=milk", headers=auth)
    names = [i["name"] for i in resp.json()]
    assert "Whole Milk" in names
    assert "Oat Milk" in names
    assert "Butter" not in names


async def test_get_item(client, auth, item_id):
    resp = await client.get(f"/items/{item_id}", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["id"] == item_id


async def test_update_item(client, auth, item_id):
    resp = await client.patch(
        f"/items/{item_id}", json={"name": "Skimmed Milk"}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Skimmed Milk"


async def test_duplicate_barcode_returns_existing_with_200(client: AsyncClient, auth):
    first = await client.post(
        "/items",
        json={"name": "Milk", "barcode": "1234567890123", "unit": "litre"},
        headers=auth,
    )
    assert first.status_code == 201

    second = await client.post(
        "/items",
        json={"name": "Milk", "barcode": "1234567890123", "unit": "litre"},
        headers=auth,
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


async def test_duplicate_barcode_different_households_allowed(
    client: AsyncClient, auth, other_auth
):
    first = await client.post(
        "/items",
        json={"name": "Milk", "barcode": "1234567890123", "unit": "litre"},
        headers=auth,
    )
    assert first.status_code == 201

    # Same barcode, different household — should create a separate item.
    second = await client.post(
        "/items",
        json={"name": "Milk", "barcode": "1234567890123", "unit": "litre"},
        headers=other_auth,
    )
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]


async def test_delete_item_cascades_batches(client: AsyncClient, auth, item_id):
    await client.post(f"/items/{item_id}/batches", json={"quantity": 3}, headers=auth)
    await client.delete(f"/items/{item_id}", headers=auth)
    # Item is gone
    assert (await client.get(f"/items/{item_id}", headers=auth)).status_code == 404
    # Batches are gone too
    assert (
        await client.get(f"/items/{item_id}/batches", headers=auth)
    ).status_code == 404


async def test_list_items_filter_by_location(client: AsyncClient, auth):
    fridge_id = (
        await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    ).json()["id"]
    pantry_id = next(
        loc["id"]
        for loc in (await client.get("/locations", headers=auth)).json()
        if loc["name"] == "Pantry"
    )
    milk_id = (
        await client.post(
            "/items", json={"name": "Milk", "unit": "litre"}, headers=auth
        )
    ).json()["id"]
    butter_id = (
        await client.post("/items", json={"name": "Butter", "unit": "g"}, headers=auth)
    ).json()["id"]

    await client.post(
        f"/items/{milk_id}/batches",
        json={"quantity": 1, "location_id": fridge_id},
        headers=auth,
    )
    await client.post(
        f"/items/{butter_id}/batches",
        json={"quantity": 1, "location_id": pantry_id},
        headers=auth,
    )

    resp = await client.get(f"/items?location_id={fridge_id}", headers=auth)
    names = [i["name"] for i in resp.json()]
    assert "Milk" in names
    assert "Butter" not in names


async def test_isolation_cannot_read_other_household_item(
    client: AsyncClient, auth, other_auth, item_id
):
    resp = await client.get(f"/items/{item_id}", headers=other_auth)
    assert resp.status_code == 404


async def test_isolation_cannot_delete_other_household_item(
    client: AsyncClient, auth, other_auth, item_id
):
    resp = await client.delete(f"/items/{item_id}", headers=other_auth)
    assert resp.status_code == 404


async def test_isolation_cannot_update_other_household_item(
    client: AsyncClient, auth, other_auth, item_id
):
    resp = await client.patch(
        f"/items/{item_id}", json={"name": "Stolen"}, headers=other_auth
    )
    assert resp.status_code == 404

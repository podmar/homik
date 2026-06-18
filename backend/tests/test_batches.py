import pytest
from httpx import AsyncClient


@pytest.fixture
async def item_id(client, auth):
    resp = await client.post(
        "/items", json={"name": "Milk", "unit": "litre"}, headers=auth
    )
    return resp.json()["id"]


@pytest.fixture
async def batch_id(client, auth, item_id):
    resp = await client.post(
        f"/items/{item_id}/batches", json={"quantity": 5}, headers=auth
    )
    return resp.json()["id"]


async def test_create_batch(client, auth, item_id):
    resp = await client.post(
        f"/items/{item_id}/batches", json={"quantity": 3}, headers=auth
    )
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 3


async def test_create_batch_merges_on_collision(client: AsyncClient, auth, item_id):
    from datetime import date, timedelta

    pantry_id = next(
        loc["id"]
        for loc in (await client.get("/locations", headers=auth)).json()
        if loc["name"] == "Pantry"
    )
    expiry = str(date.today() + timedelta(days=365))

    first = await client.post(
        f"/items/{item_id}/batches",
        json={"quantity": 3, "location_id": pantry_id, "expiry_date": expiry},
        headers=auth,
    )
    assert first.status_code == 201

    second = await client.post(
        f"/items/{item_id}/batches",
        json={"quantity": 2, "location_id": pantry_id, "expiry_date": expiry},
        headers=auth,
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["quantity"] == 5


async def test_list_batches(client, auth, item_id, batch_id):
    resp = await client.get(f"/items/{item_id}/batches", headers=auth)
    assert resp.status_code == 200
    assert any(b["id"] == batch_id for b in resp.json())


async def test_update_batch_quantity(client, auth, batch_id):
    resp = await client.patch(
        f"/batches/{batch_id}", json={"quantity": 10}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 10


async def test_update_batch_merges_on_collision(client: AsyncClient, auth, item_id):
    loc_resp = await client.post("/locations", json={"name": "Fridge"}, headers=auth)
    fridge_id = loc_resp.json()["id"]
    pantry_id = (await client.get("/locations", headers=auth)).json()
    pantry_id = next(loc["id"] for loc in pantry_id if loc["name"] == "Pantry")

    # Batch A in Pantry, batch B in Fridge — same item, same default expiry.
    batch_a = (
        await client.post(
            f"/items/{item_id}/batches",
            json={"quantity": 3, "location_id": pantry_id},
            headers=auth,
        )
    ).json()
    batch_b = (
        await client.post(
            f"/items/{item_id}/batches",
            json={"quantity": 2, "location_id": fridge_id},
            headers=auth,
        )
    ).json()

    # Moving batch B to Pantry collides with batch A — should merge.
    resp = await client.patch(
        f"/batches/{batch_b['id']}", json={"location_id": pantry_id}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == batch_a["id"]
    assert resp.json()["quantity"] == 5


async def test_update_batch_expiry_merges_on_collision(
    client: AsyncClient, auth, item_id
):
    from datetime import date, timedelta

    pantry_id = next(
        loc["id"]
        for loc in (await client.get("/locations", headers=auth)).json()
        if loc["name"] == "Pantry"
    )
    expiry_a = str(date.today() + timedelta(days=30))
    expiry_b = str(date.today() + timedelta(days=60))

    batch_a = (
        await client.post(
            f"/items/{item_id}/batches",
            json={"quantity": 3, "location_id": pantry_id, "expiry_date": expiry_a},
            headers=auth,
        )
    ).json()
    batch_b = (
        await client.post(
            f"/items/{item_id}/batches",
            json={"quantity": 2, "location_id": pantry_id, "expiry_date": expiry_b},
            headers=auth,
        )
    ).json()

    # Changing batch B's expiry to match batch A → should merge.
    resp = await client.patch(
        f"/batches/{batch_b['id']}", json={"expiry_date": expiry_a}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == batch_a["id"]
    assert resp.json()["quantity"] == 5


async def test_delete_batch(client, auth, item_id, batch_id):
    resp = await client.delete(f"/batches/{batch_id}", headers=auth)
    assert resp.status_code == 204
    batches = (await client.get(f"/items/{item_id}/batches", headers=auth)).json()
    assert not any(b["id"] == batch_id for b in batches)


async def test_adjust_increases_quantity(client, auth, batch_id):
    resp = await client.post(
        f"/batches/{batch_id}/adjust", json={"delta": 3}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 8


async def test_adjust_decreases_quantity(client, auth, batch_id):
    resp = await client.post(
        f"/batches/{batch_id}/adjust", json={"delta": -2}, headers=auth
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 3


async def test_adjust_to_zero_deletes_batch(
    client: AsyncClient, auth, item_id, batch_id
):
    resp = await client.post(
        f"/batches/{batch_id}/adjust", json={"delta": -5}, headers=auth
    )
    assert resp.status_code == 204
    batches = (await client.get(f"/items/{item_id}/batches", headers=auth)).json()
    assert batches == []


async def test_adjust_below_zero_returns_422(client, auth, batch_id):
    resp = await client.post(
        f"/batches/{batch_id}/adjust", json={"delta": -99}, headers=auth
    )
    assert resp.status_code == 422


async def test_expiring(client: AsyncClient, auth, item_id):
    from datetime import date, timedelta

    expiring_soon = str(date.today() + timedelta(days=7))
    not_expiring = str(date.today() + timedelta(days=60))

    await client.post(
        f"/items/{item_id}/batches",
        json={"quantity": 1, "expiry_date": expiring_soon},
        headers=auth,
    )
    await client.post(
        f"/items/{item_id}/batches",
        json={"quantity": 1, "expiry_date": not_expiring},
        headers=auth,
    )

    resp = await client.get("/expiring?days=30", headers=auth)
    assert resp.status_code == 200
    expiry_dates = [b["expiry_date"] for b in resp.json()]
    assert expiring_soon in expiry_dates
    assert not_expiring not in expiry_dates


async def test_expiring_isolation(client: AsyncClient, auth, other_auth):
    from datetime import date, timedelta

    expiring_soon = str(date.today() + timedelta(days=7))

    # Create a batch for user A expiring soon.
    item_id = (
        await client.post(
            "/items", json={"name": "Milk", "unit": "litre"}, headers=auth
        )
    ).json()["id"]
    await client.post(
        f"/items/{item_id}/batches",
        json={"quantity": 1, "expiry_date": expiring_soon},
        headers=auth,
    )

    # User B's expiring list should be empty — different household.
    resp = await client.get("/expiring?days=30", headers=other_auth)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_isolation_cannot_adjust_other_household_batch(
    client: AsyncClient, auth, other_auth, batch_id
):
    resp = await client.post(
        f"/batches/{batch_id}/adjust", json={"delta": -1}, headers=other_auth
    )
    assert resp.status_code == 404


async def test_isolation_cannot_update_other_household_batch(
    client: AsyncClient, auth, other_auth, batch_id
):
    resp = await client.patch(
        f"/batches/{batch_id}", json={"quantity": 99}, headers=other_auth
    )
    assert resp.status_code == 404


async def test_isolation_cannot_delete_other_household_batch(
    client: AsyncClient, auth, other_auth, batch_id
):
    resp = await client.delete(f"/batches/{batch_id}", headers=other_auth)
    assert resp.status_code == 404


async def test_isolation_cannot_list_other_household_batches(
    client: AsyncClient, auth, other_auth, item_id, batch_id
):
    resp = await client.get(f"/items/{item_id}/batches", headers=other_auth)
    assert resp.status_code == 404


async def test_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/expiring")
    assert resp.status_code == 401

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel

from app.auth.users import current_active_user
from app.models.user import User

router = APIRouter(tags=["lookup"])


class BarcodeResult(SQLModel):
    barcode: str
    name: str | None
    brand: str | None
    image_url: str | None
    # Raw category tag from Open Food Facts (e.g. "en:beverages") — not a Category id.
    category_hint: str | None


@router.get("/lookup/barcode/{barcode}")
async def lookup_barcode(
    barcode: str,
    # Dependency used only to require authentication; result not needed in the handler.
    _user: Annotated[User, Depends(current_active_user)],
) -> BarcodeResult:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail="Product lookup service unavailable"
        ) from exc

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Product lookup service returned {response.status_code}")

    data = response.json()
    if data.get("status") != 1:
        raise HTTPException(status_code=404, detail="Product not found")

    product = data["product"]
    tags: list[str] = product.get("categories_tags") or []

    return BarcodeResult(
        barcode=barcode,
        name=product.get("product_name") or product.get("product_name_en"),
        brand=product.get("brands"),
        image_url=product.get("image_front_url"),
        category_hint=tags[0] if tags else None,
    )

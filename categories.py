"""
Categories router — manage product categories via API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CategoryCreate, CategoryUpdate, CategoryOut
from app.services import (
    get_all_categories, get_category_by_id,
    create_category, update_category, delete_category,
)

router = APIRouter(prefix="/api/categories", tags=["Categories API"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: Session = Depends(get_db)):
    return get_all_categories(db)


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    return get_category_by_id(db, category_id)


@router.post("", response_model=CategoryOut, status_code=201)
async def api_create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db, data)


@router.patch("/{category_id}", response_model=CategoryOut)
async def api_update_category(
    category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)
):
    return update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=204)
async def api_delete_category(category_id: int, db: Session = Depends(get_db)):
    delete_category(db, category_id)

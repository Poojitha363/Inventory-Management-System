"""
Category service — CRUD operations for product categories.
"""

import logging
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.category import Category
from app.schemas import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


def get_all_categories(db: Session) -> List[Category]:
    return db.query(Category).order_by(Category.name).all()


def get_category_by_id(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    existing = db.query(Category).filter(Category.name.ilike(data.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{data.name}' already exists.",
        )
    category = Category(**data.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    logger.info(f"Category created: {category.name}")
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category_by_id(db, category_id)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category_by_id(db, category_id)
    if category.products.count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a category that has products. Reassign products first.",
        )
    db.delete(category)
    db.commit()
    logger.info(f"Category deleted: id={category_id}")

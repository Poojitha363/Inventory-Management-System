"""
Product service — CRUD + stock management business logic.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.category import Category
from app.schemas import ProductCreate, ProductUpdate, StockAdjustment

logger = logging.getLogger(__name__)


# ─── Read ─────────────────────────────────────────────────────────────────────

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    low_stock_only: bool = False,
) -> List[Product]:
    """
    Paginated product list with optional filters.
    """
    query = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.is_active == True)
    )

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(Product.name.ilike(term), Product.sku.ilike(term))
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if low_stock_only:
        query = query.filter(Product.quantity <= Product.low_stock_threshold)

    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


def get_product_by_id(db: Session, product_id: int) -> Product:
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.created_by_user))
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    return db.query(Product).filter(Product.sku == sku.upper()).first()


# ─── Create ───────────────────────────────────────────────────────────────────

def create_product(db: Session, data: ProductCreate, created_by: int) -> Product:
    if get_product_by_sku(db, data.sku):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SKU '{data.sku.upper()}' is already in use.",
        )

    if data.category_id:
        _validate_category(db, data.category_id)

    product = Product(**data.dict(), created_by=created_by)
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info(f"Product created: {product.sku} by user_id={created_by}")
    return product


# ─── Update ───────────────────────────────────────────────────────────────────

def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)

    if data.category_id is not None:
        _validate_category(db, data.category_id)

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    logger.info(f"Product updated: id={product_id}")
    return product


# ─── Delete ───────────────────────────────────────────────────────────────────

def delete_product(db: Session, product_id: int) -> None:
    """Soft-delete: marks is_active=False rather than removing the row."""
    product = get_product_by_id(db, product_id)
    product.is_active = False
    db.commit()
    logger.info(f"Product soft-deleted: id={product_id}")


# ─── Stock ────────────────────────────────────────────────────────────────────

def adjust_stock(db: Session, product_id: int, adjustment: StockAdjustment) -> Product:
    """
    Add or reduce stock.
    Raises 400 if adjustment would push quantity below zero.
    """
    product = get_product_by_id(db, product_id)
    new_qty = product.quantity + adjustment.quantity

    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current: {product.quantity}, Requested reduction: {abs(adjustment.quantity)}",
        )

    product.quantity = new_qty
    db.commit()
    db.refresh(product)
    logger.info(
        f"Stock adjusted for product id={product_id}: {adjustment.quantity:+d} → qty={new_qty}"
    )
    return product


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
    total_categories = db.query(func.count(Category.id)).scalar()

    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.is_active == True, Product.quantity <= Product.low_stock_threshold)
        .scalar()
    )

    out_of_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.is_active == True, Product.quantity == 0)
        .scalar()
    )

    total_inventory_value = (
        db.query(func.sum(Product.price * Product.quantity))
        .filter(Product.is_active == True)
        .scalar()
        or 0.0
    )

    recent_products = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.is_active == True)
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "total_inventory_value": round(total_inventory_value, 2),
        "recent_products": recent_products,
        "active_products": total_products,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _validate_category(db: Session, category_id: int):
    if not db.query(Category).filter(Category.id == category_id).first():
        raise HTTPException(status_code=404, detail="Category not found.")

"""
Products router — CRUD pages + REST API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProductCreate, ProductUpdate, StockAdjustment, ProductOut
from app.services import (
    get_products, get_product_by_id, create_product,
    update_product, delete_product, adjust_stock,
    get_all_categories, get_user_by_email,
)
from app.utils.auth import get_current_user_from_cookie

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user_or_redirect(request: Request, db: Session):
    email = get_current_user_from_cookie(request)
    if not email:
        return None, RedirectResponse(url="/login", status_code=302)
    user = get_user_by_email(db, email)
    return (user, None) if user else (None, RedirectResponse(url="/login", status_code=302))


# ─── HTML Pages ───────────────────────────────────────────────────────────────

@router.get("/products", response_class=HTMLResponse, include_in_schema=False)
async def products_page(
    request: Request,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    low_stock: bool = False,
    db: Session = Depends(get_db),
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect

    products = get_products(
        db,
        search=search,
        category_id=category_id,
        low_stock_only=low_stock,
        limit=200,
    )
    categories = get_all_categories(db)

    return templates.TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "categories": categories,
            "search": search or "",
            "selected_category": category_id,
            "low_stock": low_stock,
            "page": "products",
        },
    )


@router.get("/products/add", response_class=HTMLResponse, include_in_schema=False)
async def add_product_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect
    categories = get_all_categories(db)
    return templates.TemplateResponse(
        "products/add.html",
        {"request": request, "user": user, "categories": categories, "page": "products"},
    )


@router.post("/products/add", response_class=HTMLResponse, include_in_schema=False)
async def add_product_submit(
    request: Request,
    name: str = Form(...),
    sku: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    cost_price: float = Form(0.0),
    quantity: int = Form(...),
    low_stock_threshold: int = Form(10),
    image_url: str = Form(""),
    category_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect

    try:
        data = ProductCreate(
            name=name, sku=sku, description=description or None,
            price=price, cost_price=cost_price, quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            image_url=image_url or None, category_id=category_id,
        )
        create_product(db, data, created_by=user.id)
        return RedirectResponse(url="/products?success=added", status_code=302)
    except Exception as e:
        categories = get_all_categories(db)
        return templates.TemplateResponse(
            "products/add.html",
            {
                "request": request, "user": user,
                "categories": categories, "error": getattr(e, "detail", str(e)),
                "page": "products",
            },
        )


@router.get("/products/{product_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_product_page(
    request: Request, product_id: int, db: Session = Depends(get_db)
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect
    product = get_product_by_id(db, product_id)
    categories = get_all_categories(db)
    return templates.TemplateResponse(
        "products/edit.html",
        {
            "request": request, "user": user, "product": product,
            "categories": categories, "page": "products",
        },
    )


@router.post("/products/{product_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_product_submit(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    cost_price: float = Form(0.0),
    quantity: int = Form(...),
    low_stock_threshold: int = Form(10),
    image_url: str = Form(""),
    category_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect

    try:
        data = ProductUpdate(
            name=name, description=description or None,
            price=price, cost_price=cost_price, quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            image_url=image_url or None, category_id=category_id,
        )
        update_product(db, product_id, data)
        return RedirectResponse(url="/products?success=updated", status_code=302)
    except Exception as e:
        categories = get_all_categories(db)
        product = get_product_by_id(db, product_id)
        return templates.TemplateResponse(
            "products/edit.html",
            {
                "request": request, "user": user, "product": product,
                "categories": categories, "error": getattr(e, "detail", str(e)),
                "page": "products",
            },
        )


@router.post("/products/{product_id}/delete", include_in_schema=False)
async def delete_product_page(
    request: Request, product_id: int, db: Session = Depends(get_db)
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect
    delete_product(db, product_id)
    return RedirectResponse(url="/products?success=deleted", status_code=302)


@router.get("/products/{product_id}", response_class=HTMLResponse, include_in_schema=False)
async def product_detail_page(
    request: Request, product_id: int, db: Session = Depends(get_db)
):
    user, redirect = _get_user_or_redirect(request, db)
    if redirect:
        return redirect
    product = get_product_by_id(db, product_id)
    return templates.TemplateResponse(
        "products/detail.html",
        {"request": request, "user": user, "product": product, "page": "products"},
    )


# ─── REST API ─────────────────────────────────────────────────────────────────

@router.get("/api/products", tags=["Products API"])
async def api_get_products(
    request: Request,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    low_stock: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    products = get_products(db, skip=skip, limit=limit, search=search,
                            category_id=category_id, low_stock_only=low_stock)
    return [_serialize_product(p) for p in products]


@router.get("/api/products/{product_id}", tags=["Products API"])
async def api_get_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    return _serialize_product(product)


@router.post("/api/products", tags=["Products API"], status_code=201)
async def api_create_product(
    request: Request, data: ProductCreate, db: Session = Depends(get_db)
):
    email = get_current_user_from_cookie(request)
    user = get_user_by_email(db, email) if email else None
    product = create_product(db, data, created_by=user.id if user else 1)
    return _serialize_product(product)


@router.patch("/api/products/{product_id}", tags=["Products API"])
async def api_update_product(
    product_id: int, data: ProductUpdate, db: Session = Depends(get_db)
):
    product = update_product(db, product_id, data)
    return _serialize_product(product)


@router.delete("/api/products/{product_id}", tags=["Products API"], status_code=204)
async def api_delete_product(product_id: int, db: Session = Depends(get_db)):
    delete_product(db, product_id)


@router.post("/api/products/{product_id}/stock", tags=["Products API"])
async def api_adjust_stock(
    product_id: int, data: StockAdjustment, db: Session = Depends(get_db)
):
    product = adjust_stock(db, product_id, data)
    return _serialize_product(product)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_product(p) -> dict:
    return {
        "id": p.id, "name": p.name, "sku": p.sku,
        "description": p.description, "price": p.price,
        "cost_price": p.cost_price, "quantity": p.quantity,
        "low_stock_threshold": p.low_stock_threshold,
        "is_low_stock": p.is_low_stock, "total_value": p.total_value,
        "profit_margin": p.profit_margin, "image_url": p.image_url,
        "is_active": p.is_active,
        "category": {"id": p.category.id, "name": p.category.name} if p.category else None,
        "created_at": str(p.created_at),
    }

"""
Dashboard router — main landing page after login, plus dashboard API.
"""

import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import get_dashboard_stats, get_user_by_email
from app.utils.auth import get_current_user_from_cookie

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_auth(request: Request, db: Session):
    """Helper: return current user or redirect to login."""
    email = get_current_user_from_cookie(request)
    if not email:
        return None, RedirectResponse(url="/login", status_code=302)
    user = get_user_by_email(db, email)
    if not user:
        return None, RedirectResponse(url="/login", status_code=302)
    return user, None


@router.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = require_auth(request, db)
    if redirect:
        return redirect

    stats = get_dashboard_stats(db)
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "page": "dashboard",
        },
    )


@router.get("/api/dashboard", tags=["Dashboard API"])
async def api_dashboard(request: Request, db: Session = Depends(get_db)):
    """REST endpoint for dashboard statistics."""
    email = get_current_user_from_cookie(request)
    if not email:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    stats = get_dashboard_stats(db)
    # Serialize recent_products manually for JSON
    recent = [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "quantity": p.quantity,
            "price": p.price,
            "is_low_stock": p.is_low_stock,
            "category": p.category.name if p.category else None,
        }
        for p in stats["recent_products"]
    ]
    return {
        "total_products": stats["total_products"],
        "total_categories": stats["total_categories"],
        "low_stock_count": stats["low_stock_count"],
        "out_of_stock_count": stats["out_of_stock_count"],
        "total_inventory_value": stats["total_inventory_value"],
        "recent_products": recent,
    }

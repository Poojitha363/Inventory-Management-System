"""
Smart Inventory Management System
──────────────────────────────────
FastAPI application entry point.
Registers all routers, configures middleware, and seeds the database on startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, SessionLocal
from app.routers import auth_router, dashboard_router, products_router, categories_router
from app.config import get_settings

# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Inventory…")
    init_db()
    _seed_demo_data()
    yield
    logger.info("Shutting down Smart Inventory.")


def _seed_demo_data():
    """
    Populate the database with demo data on first run.
    Safe to call multiple times — checks for existing records.
    """
    from app.models.user import User
    from app.models.category import Category
    from app.models.product import Product
    from app.utils.auth import hash_password

    db = SessionLocal()
    try:
        # Demo admin user
        if not db.query(User).first():
            admin = User(
                full_name="Admin User",
                email="admin@inventory.com",
                hashed_password=hash_password("admin123"),
                is_admin=True,
            )
            db.add(admin)
            db.flush()

            # Categories
            categories_data = [
                {"name": "Electronics", "description": "Electronic devices and components", "color": "#0d6efd"},
                {"name": "Office Supplies", "description": "Stationery and office equipment", "color": "#198754"},
                {"name": "Furniture", "description": "Desks, chairs, and storage", "color": "#fd7e14"},
                {"name": "Tools & Equipment", "description": "Hardware and machinery", "color": "#dc3545"},
                {"name": "Software & Licenses", "description": "Digital products", "color": "#6610f2"},
            ]
            cats = {}
            for cd in categories_data:
                c = Category(**cd)
                db.add(c)
                db.flush()
                cats[c.name] = c.id

            # Products
            products_data = [
                {"name": "MacBook Pro 14\"", "sku": "ELEC-MBP14", "price": 1999.99, "cost_price": 1600.00, "quantity": 15, "category_id": cats["Electronics"], "description": "Apple MacBook Pro M3 Chip, 16GB RAM, 512GB SSD", "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&auto=format"},
                {"name": "Dell Monitor 27\"", "sku": "ELEC-DM27", "price": 349.99, "cost_price": 250.00, "quantity": 8, "category_id": cats["Electronics"], "description": "4K IPS Display, 60Hz, USB-C", "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&auto=format"},
                {"name": "Logitech MX Keys", "sku": "ELEC-LMXK", "price": 109.99, "cost_price": 70.00, "quantity": 3, "low_stock_threshold": 5, "category_id": cats["Electronics"], "description": "Wireless Illuminated Keyboard"},
                {"name": "Ergonomic Office Chair", "sku": "FURN-EOC1", "price": 499.99, "cost_price": 320.00, "quantity": 6, "category_id": cats["Furniture"], "description": "Lumbar support, adjustable armrests", "image_url": "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=400&auto=format"},
                {"name": "Standing Desk 160cm", "sku": "FURN-SD160", "price": 699.99, "cost_price": 480.00, "quantity": 4, "low_stock_threshold": 5, "category_id": cats["Furniture"], "description": "Height-adjustable electric standing desk"},
                {"name": "A4 Paper Ream (500)", "sku": "OFF-A4R", "price": 8.99, "cost_price": 4.50, "quantity": 120, "category_id": cats["Office Supplies"], "description": "80gsm White Office Paper"},
                {"name": "Whiteboard Markers Set", "sku": "OFF-WBM8", "price": 14.99, "cost_price": 6.00, "quantity": 2, "low_stock_threshold": 10, "category_id": cats["Office Supplies"], "description": "8-colour dry-erase marker set"},
                {"name": "Power Drill Kit", "sku": "TOOL-PDK", "price": 89.99, "cost_price": 55.00, "quantity": 0, "low_stock_threshold": 3, "category_id": cats["Tools & Equipment"], "description": "Cordless 18V drill with 50-piece bit set"},
                {"name": "JetBrains All Products Pack", "sku": "SW-JBAP", "price": 249.00, "cost_price": 0.00, "quantity": 25, "category_id": cats["Software & Licenses"], "description": "Annual subscription — 1 user"},
                {"name": "Microsoft 365 Business", "sku": "SW-MS365", "price": 12.50, "cost_price": 0.00, "quantity": 50, "category_id": cats["Software & Licenses"], "description": "Per-user monthly license"},
            ]
            for pd in products_data:
                p = Product(**pd, created_by=admin.id)
                db.add(p)

            db.commit()
            logger.info("Demo data seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.warning(f"Seed skipped or failed (likely already seeded): {e}")
    finally:
        db.close()


# ─── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Inventory Management System",
    description="Production-grade inventory management with FastAPI, SQLAlchemy, and Bootstrap 5.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(categories_router)

templates = Jinja2Templates(directory="app/templates")


# ─── Global error handlers ────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/404.html", {"request": request}, status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "errors/500.html", {"request": request}, status_code=500
    )

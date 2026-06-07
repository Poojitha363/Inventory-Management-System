from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.products import router as products_router
from app.routers.categories import router as categories_router

__all__ = ["auth_router", "dashboard_router", "products_router", "categories_router"]

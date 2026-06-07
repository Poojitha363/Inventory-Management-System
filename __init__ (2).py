"""
Pydantic schemas for request validation and response serialization.
Keeps API contracts explicit and type-safe.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Category Schemas ─────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#6c757d", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    product_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Product Schemas ──────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    sku: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    quantity: int = Field(..., ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None

    @validator("sku")
    def sku_uppercase(cls, v):
        return v.upper().strip()


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class StockAdjustment(BaseModel):
    quantity: int = Field(..., description="Positive to add stock, negative to reduce")
    reason: Optional[str] = Field(None, max_length=255)


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    description: Optional[str]
    price: float
    cost_price: Optional[float]
    quantity: int
    low_stock_threshold: int
    image_url: Optional[str]
    is_active: bool
    is_low_stock: bool
    total_value: float
    profit_margin: float
    category_id: Optional[int]
    category: Optional[CategoryOut]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Dashboard Schema ─────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_products: int
    total_categories: int
    low_stock_count: int
    total_inventory_value: float
    recent_products: List[ProductOut]
    out_of_stock_count: int
    active_products: int

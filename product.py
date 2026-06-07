"""
Product model — core inventory entity with stock tracking.
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

LOW_STOCK_THRESHOLD = 10  # Units below this count trigger low-stock alerts


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=True, default=0.0)
    quantity = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, default=LOW_STOCK_THRESHOLD)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Foreign keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    created_by_user = relationship("User", back_populates="products")

    @property
    def is_low_stock(self) -> bool:
        """Returns True when quantity is at or below the threshold."""
        return self.quantity <= self.low_stock_threshold

    @property
    def total_value(self) -> float:
        """Current total inventory value for this product."""
        return round(self.quantity * self.price, 2)

    @property
    def profit_margin(self) -> float:
        """Gross margin percentage."""
        if self.cost_price and self.price > 0:
            return round(((self.price - self.cost_price) / self.price) * 100, 1)
        return 0.0

    def __repr__(self):
        return f"<Product id={self.id} sku={self.sku} name={self.name}>"

"""
Category model — product taxonomy for filtering and reporting.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#6c757d")  # hex color for badge styling
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    products = relationship("Product", back_populates="category", lazy="dynamic")

    @property
    def product_count(self):
        return self.products.count()

    def __repr__(self):
        return f"<Category id={self.id} name={self.name}>"

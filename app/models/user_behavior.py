from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    behavior_type = Column(String(50), nullable=False)  # 'view', 'purchase', 'favorite', 'review'
    rating = Column(Float, nullable=True)  # Si es una reseña
    duration_seconds = Column(Integer, nullable=True)  # Tiempo viendo el producto
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", backref="behaviors")
    product = relationship("Product")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_type = Column(String(50), nullable=False)  # 'category', 'price_range', 'spicy', etc.
    preference_value = Column(String(255), nullable=False)
    preference_strength = Column(Float, default=1.0)  # 0-1 qué tan fuerte es la preferencia
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="preferences")
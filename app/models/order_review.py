from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class OrderReview(Base):
    __tablename__ = "order_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Rating general de la experiencia
    overall_rating = Column(Float, nullable=False)  # 1-5 estrellas
    
    # Ratings específicos
    food_quality_rating = Column(Float, nullable=True)  # Calidad de comida
    service_rating = Column(Float, nullable=True)       # Servicio
    delivery_rating = Column(Float, nullable=True)      # Entrega (si aplica)
    ambiance_rating = Column(Float, nullable=True)      # Ambiente (para dine-in)
    
    comment = Column(Text)
    is_approved = Column(Boolean, default=False)
    
    # Para seguimiento
    would_recommend = Column(Boolean, default=True)
    issues_reported = Column(Text, nullable=True)  # Problemas específicos
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user = relationship("User", backref="order_reviews")
    order = relationship("Order", backref="reviews")
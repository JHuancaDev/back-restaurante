from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        Text)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user = relationship("User", backref="reviews", lazy="joined")
    product = relationship("Product", backref="reviews", lazy="joined")
    
    # Propiedades híbridas para los campos calculados
    @hybrid_property
    def user_name(self):
        return self.user.full_name if self.user else "Usuario"
    
    @hybrid_property
    def product_name(self):
        return self.product.name if self.product else "Producto"
    
    @hybrid_property
    def product_image(self):
        return self.product.image_url if self.product else None
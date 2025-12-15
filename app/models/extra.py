from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property 

from app.db.database import Base

class Extra(Base):
    __tablename__ = "extras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0)  # 0.0 para extras gratuitos
    category = Column(String(50), default="condimento")  # 'bebida', 'condimento', 'acompanamiento'
    is_available = Column(Boolean, default=True)
    is_free = Column(Boolean, default=False)  # Si es gratuito (cortesía de la casa)
    stock = Column(Integer, default=0)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class OrderExtra(Base):
    __tablename__ = "order_extras"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    extra_id = Column(Integer, ForeignKey("extras.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    order = relationship("Order", backref="extras")
    extra = relationship("Extra", lazy="joined")
    
    # 🔥 AGREGAR estas propiedades híbridas
    @hybrid_property
    def extra_name(self):
        return self.extra.name if self.extra else "Extra"
    
    @hybrid_property
    def extra_image(self):
        return self.extra.image_url if self.extra else None
    
    @hybrid_property 
    def is_free(self):
        return self.unit_price == 0.0
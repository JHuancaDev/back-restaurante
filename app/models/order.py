from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)  # Nueva relación con mesa
    order_type = Column(String(20), default="delivery")  # 'delivery' o 'dine_in'
    status = Column(String(50), default="recibido")  # recibido, en_preparacion, listo, entregado, completado
    special_instructions = Column(Text)
    delivery_address = Column(Text, nullable=True)  # Para pedidos 
    estimated_time = Column(Integer)  # minutos estimados
    total_amount = Column(Float, default=0.0)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user = relationship("User", backref="orders")
    table = relationship("Table", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    special_instructions = Column(Text, nullable=True)

    # Relaciones
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
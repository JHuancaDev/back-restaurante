from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", backref="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Campos dinámicos (no se almacenan en BD)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._total_amount = None
        self._items_count = None
    
    @property
    def total_amount(self):
        return self._total_amount
    
    @total_amount.setter
    def total_amount(self, value):
        self._total_amount = value
    
    @property
    def items_count(self):
        return self._items_count
    
    @items_count.setter
    def items_count(self, value):
        self._items_count = value

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    
    # Campos dinámicos (no se almacenan en BD)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._product_name = None
        self._product_price = None
        self._product_image = None
        self._subtotal = None
    
    @property
    def product_name(self):
        return self._product_name
    
    @product_name.setter
    def product_name(self, value):
        self._product_name = value
    
    @property
    def product_price(self):
        return self._product_price
    
    @product_price.setter
    def product_price(self, value):
        self._product_price = value
    
    @property
    def product_image(self):
        return self._product_image
    
    @product_image.setter
    def product_image(self, value):
        self._product_image = value
    
    @property
    def subtotal(self):
        return self._subtotal
    
    @subtotal.setter
    def subtotal(self, value):
        self._subtotal = value
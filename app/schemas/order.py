from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    special_instructions: Optional[str] = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    unit_price: float
    subtotal: float
    product_name: Optional[str] = None  # Cambiar a Optional
    product_image: Optional[str] = None  # Cambiar a Optional

class OrderBase(BaseModel):
    order_type: str  # 'delivery' o 'dine_in'
    table_id: Optional[int] = None
    delivery_address: Optional[str] = None
    special_instructions: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    special_instructions: Optional[str] = None
    delivery_address: Optional[str] = None
    estimated_time: Optional[int] = None
    is_paid: Optional[bool] = None

class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    status: str
    total_amount: float
    estimated_time: Optional[int]
    is_paid: bool
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[OrderItemResponse]
    table_number: Optional[int] = None
    table_number: Optional[int] = None  # Número de mesa
    table_capacity: Optional[int] = None  # Capacidad de la mesa
    user_name: str
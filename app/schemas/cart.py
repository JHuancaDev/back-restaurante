from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CartItemBase(BaseModel):
    product_id: int
    quantity: int
    special_instructions: Optional[str] = None

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    special_instructions: Optional[str] = None

class CartItemResponse(CartItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cart_id: int
    product_name: str
    product_price: float
    product_image: Optional[str]
    subtotal: float
    created_at: datetime
    updated_at: Optional[datetime]

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    total_amount: float
    items_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[CartItemResponse]

class CartSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    total_amount: float
    items_count: int
    created_at: datetime
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ExtraBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    category: str = "condimento"
    is_free: bool = False
    stock: int = 0
    image_url: Optional[str] = None

class ExtraCreate(ExtraBase):
    pass

class ExtraUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None
    is_free: Optional[bool] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None

class ExtraResponse(ExtraBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]

class OrderExtraBase(BaseModel):
    extra_id: int
    quantity: int = 1

class OrderExtraCreate(OrderExtraBase):
    pass

class OrderExtraResponse(OrderExtraBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_id: int
    unit_price: float
    subtotal: float
    extra_name: str  # Ahora es requerido
    extra_image: Optional[str] = None
    is_free: bool = False
    created_at: datetime
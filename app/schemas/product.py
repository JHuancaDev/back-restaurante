from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category_id: int
    stock: int = Field(default=0, ge=0)

class ProductCreate(ProductBase):
    pass

class ProductCreateWithImage(ProductBase):
    pass  # El controlador manejará la imagen separadamente

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    image_url: Optional[str] = None  # Para actualizar URL manualmente
    is_available: Optional[bool] = None
    stock: Optional[int] = Field(None, ge=0)

class ProductResponse(ProductBase):
    id: int
    image_url: Optional[str]
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
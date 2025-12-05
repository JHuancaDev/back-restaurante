from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    url_image: Optional[str] = None  # Añadir URL de imagen

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    url_image: Optional[str] = None

class CategoryCreateWithImage(CategoryBase):
    pass  # El controlador manejará la imagen separadamente

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime

class CategoryWithProductsResponse(CategoryResponse):
    products: List[ProductResponse] = []

class CategoryWithCountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    product_count: int
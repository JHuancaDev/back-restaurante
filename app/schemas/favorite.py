from datetime import datetime

from pydantic import BaseModel

from app.schemas.product import ProductResponse


class FavoriteBase(BaseModel):
    user_id: int
    product_id: int

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteResponse(FavoriteBase):
    id: int
    created_at: datetime
    product: ProductResponse  # ✅ Información completa del producto

    class Config:
        from_attributes = True

class FavoriteWithUserResponse(FavoriteResponse):
    """Response que incluye información básica del usuario"""
    user_email: str
    user_name: str

    class Config:
        from_attributes = True
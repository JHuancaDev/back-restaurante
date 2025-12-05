from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReviewBase(BaseModel):
    product_id: int
    rating: float
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[float] = None
    comment: Optional[str] = None
    is_approved: Optional[bool] = None

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: str

class ReviewWithProductResponse(ReviewResponse):
    product_name: str
    product_image: Optional[str]
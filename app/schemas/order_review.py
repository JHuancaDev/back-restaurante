from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderReviewBase(BaseModel):
    order_id: int
    overall_rating: float
    food_quality_rating: Optional[float] = None
    service_rating: Optional[float] = None
    delivery_rating: Optional[float] = None
    ambiance_rating: Optional[float] = None
    comment: Optional[str] = None
    would_recommend: bool = True
    issues_reported: Optional[str] = None

class OrderReviewCreate(OrderReviewBase):
    pass

class OrderReviewUpdate(BaseModel):
    overall_rating: Optional[float] = None
    food_quality_rating: Optional[float] = None
    service_rating: Optional[float] = None
    delivery_rating: Optional[float] = None
    ambiance_rating: Optional[float] = None
    comment: Optional[str] = None
    would_recommend: Optional[bool] = None
    issues_reported: Optional[str] = None
    is_approved: Optional[bool] = None

class OrderReviewResponse(OrderReviewBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: str
    order_number: str  # ID de la orden formateado

class OrderReviewWithOrderResponse(OrderReviewResponse):
    order_type: str
    order_total: float
    order_date: datetime
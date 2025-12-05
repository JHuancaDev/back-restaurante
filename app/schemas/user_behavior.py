from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBehaviorBase(BaseModel):
    product_id: int
    behavior_type: str  # 'view', 'purchase', 'favorite', 'review'
    rating: Optional[float] = None
    duration_seconds: Optional[int] = None

class UserBehaviorCreate(UserBehaviorBase):
    pass

class UserBehaviorResponse(UserBehaviorBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime

class UserPreferenceBase(BaseModel):
    preference_type: str
    preference_value: str
    preference_strength: float = 1.0

class UserPreferenceResponse(UserPreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
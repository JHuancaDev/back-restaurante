from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TableBase(BaseModel):
    number: int
    capacity: int
    position_x: float
    position_y: float
    is_available: bool = True

class TableCreate(TableBase):
    pass

class TableUpdate(BaseModel):
    number: Optional[int] = None
    capacity: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None

class TableResponse(TableBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

class TablePositionUpdate(BaseModel):
    position_x: float
    position_y: float
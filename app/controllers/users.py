from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import (get_all_users, get_user_by_id,
                                       update_user)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return update_user(db, user_id=current_user.id, user_update=user_update)

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(get_current_admin)])
def read_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_users(db, skip=skip, limit=limit)

@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_admin)])
def update_user_by_admin(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user
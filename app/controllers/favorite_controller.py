from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_user
from app.db.database import get_db
from app.schemas.favorite import FavoriteCreate, FavoriteResponse
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["favorites"])
service = FavoriteService()

@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(
    data: FavoriteCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Añadir un producto a favoritos.
    El usuario solo puede añadir productos a sus propios favoritos.
    """
    return service.add_favorite(db, data, current_user.id)

@router.delete("/{user_id}/{product_id}")
def delete_favorite(
    user_id: int, 
    product_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Eliminar un producto de favoritos.
    El usuario solo puede eliminar de sus propios favoritos.
    """
    return service.remove_favorite(db, user_id, product_id, current_user.id)

@router.get("/{user_id}", response_model=List[FavoriteResponse])
def get_user_favorites(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener todos los favoritos de un usuario.
    El usuario solo puede ver sus propios favoritos.
    """
    return service.get_favorites_by_user(db, user_id, current_user.id)

@router.get("/me/favorites", response_model=List[FavoriteResponse])
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener los favoritos del usuario actual (endpoint conveniente).
    """
    return service.get_favorites_by_user(db, current_user.id, current_user.id)
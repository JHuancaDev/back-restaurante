from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.schemas.review import (ReviewCreate, ReviewResponse, ReviewUpdate,
                                ReviewWithProductResponse)
from app.services.review_service import (approve_review, create_review,
                                         delete_review,
                                         get_product_rating_stats,
                                         get_review_by_id, get_reviews,
                                         get_reviews_by_product,
                                         get_reviews_by_user, update_review)

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Rutas públicas - cualquier usuario puede ver reseñas aprobadas
@router.get("/", response_model=List[ReviewWithProductResponse])
def read_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_id: Optional[int] = Query(None, description="Filtrar por producto"),
    db: Session = Depends(get_db)
):
    """
    Obtener reseñas (solo las aprobadas para usuarios normales).
    """
    if product_id:
        reviews = get_reviews_by_product(db, product_id=product_id, approved_only=True)
    else:
        reviews = get_reviews(db, skip=skip, limit=limit, approved_only=True)
    return reviews

@router.get("/product/{product_id}/stats")
def get_product_stats(product_id: int, db: Session = Depends(get_db)):
    """
    Obtener estadísticas de rating para un producto.
    """
    return get_product_rating_stats(db, product_id=product_id)

@router.get("/{review_id}", response_model=ReviewWithProductResponse)
def read_review(review_id: int, db: Session = Depends(get_db)):
    """
    Obtener una reseña específica por ID (solo si está aprobada).
    """
    db_review = get_review_by_id(db, review_id=review_id)
    if db_review is None or not db_review.is_approved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada"
        )
    return db_review

# Rutas para usuarios autenticados
@router.post("/", response_model=ReviewResponse)
def create_new_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crear una nueva reseña.
    """
    try:
        db_review = create_review(db=db, review=review, user_id=current_user.id)
        
        # 🔥 Asegurar que tenemos los datos necesarios
        review_data = {
            "id": db_review.id,
            "user_id": db_review.user_id,
            "product_id": db_review.product_id,
            "rating": db_review.rating,
            "comment": db_review.comment,
            "is_approved": db_review.is_approved,
            "created_at": db_review.created_at,
            "updated_at": db_review.updated_at,
            "user_name": db_review.user.full_name if db_review.user else "Usuario"
        }
        
        return ReviewResponse(**review_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/user/me", response_model=List[ReviewWithProductResponse])
def read_my_reviews(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener las reseñas del usuario actual.
    """
    return get_reviews_by_user(db, user_id=current_user.id)

@router.put("/{review_id}", response_model=ReviewResponse)
def update_existing_review(
    review_id: int,
    review: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Actualizar una reseña existente (solo el propietario).
    """
    try:
        db_review = update_review(
            db, 
            review_id=review_id, 
            review_update=review, 
            user_id=current_user.id,
            is_admin=False
        )
        if db_review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        return db_review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.delete("/{review_id}")
def delete_existing_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Eliminar una reseña (solo el propietario).
    """
    try:
        result = delete_review(db, review_id=review_id, user_id=current_user.id, is_admin=False)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        return {"message": "Reseña eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

# Rutas de administrador
@router.get("/admin/all", response_model=List[ReviewWithProductResponse])
def read_all_reviews_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    approved_only: bool = Query(False, description="Mostrar solo reseñas aprobadas"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Obtener todas las reseñas (incluyendo no aprobadas - Solo administradores).
    """
    return get_reviews(db, skip=skip, limit=limit, approved_only=approved_only)

@router.post("/{review_id}/approve", response_model=ReviewResponse)
def approve_review_route(
    review_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Aprobar una reseña (Solo administradores).
    """
    db_review = approve_review(db, review_id=review_id)
    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada"
        )
    return db_review
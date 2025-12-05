from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate


def get_reviews(db: Session, skip: int = 0, limit: int = 100, approved_only: bool = True):
    query = db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.product)
    )
    
    if approved_only:
        query = query.filter(Review.is_approved == True)
    
    return query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

def get_review_by_id(db: Session, review_id: int):
    return db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.product)
    ).filter(Review.id == review_id).first()

def get_reviews_by_product(db: Session, product_id: int, approved_only: bool = True):
    query = db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.product)
    ).filter(Review.product_id == product_id)
    
    if approved_only:
        query = query.filter(Review.is_approved == True)
    
    return query.order_by(Review.created_at.desc()).all()

def get_reviews_by_user(db: Session, user_id: int):
    return db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.product)
    ).filter(Review.user_id == user_id).order_by(Review.created_at.desc()).all()

def create_review(db: Session, review: ReviewCreate, user_id: int):
    # Verificar que el producto existe
    product = db.query(Product).filter(Product.id == review.product_id).first()
    if not product:
        raise ValueError("Producto no encontrado")
    
    # Verificar que el usuario no haya revisado este producto antes
    
    # existing_review = db.query(Review).filter(
    #    Review.user_id == user_id,
   #     Review.product_id == review.product_id
   # ).first()
    
   # if existing_review:
   #     raise ValueError("Ya has revisado este producto")
    
    # Validar rating
    if review.rating < 1 or review.rating > 5:
        raise ValueError("El rating debe estar entre 1 y 5")
    
    db_review = Review(**review.dict(), user_id=user_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # 🔥 CORRECCIÓN: Cargar explícitamente las relaciones
    db_review = db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.product)
    ).filter(Review.id == db_review.id).first()
    
    return db_review

def update_review(db: Session, review_id: int, review_update: ReviewUpdate, user_id: int, is_admin: bool = False):
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None
    
    # Solo el usuario que creó la reseña o un admin puede actualizarla
    if not is_admin and db_review.user_id != user_id:
        raise ValueError("No tienes permisos para editar esta reseña")
    
    update_data = review_update.dict(exclude_unset=True)
    
    # Validar rating si se está actualizando
    if 'rating' in update_data and (update_data['rating'] < 1 or update_data['rating'] > 5):
        raise ValueError("El rating debe estar entre 1 y 5")
    
    for field, value in update_data.items():
        setattr(db_review, field, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int, user_id: int, is_admin: bool = False):
    db_review = get_review_by_id(db, review_id)
    if not db_review:
        return None
    
    # Solo el usuario que creó la reseña o un admin puede eliminarla
    if not is_admin and db_review.user_id != user_id:
        raise ValueError("No tienes permisos para eliminar esta reseña")
    
    db.delete(db_review)
    db.commit()
    return db_review

def get_product_rating_stats(db: Session, product_id: int):
    stats = db.query(
        func.count(Review.id).label('total_reviews'),
        func.avg(Review.rating).label('average_rating')
    ).filter(
        Review.product_id == product_id,
        Review.is_approved == True
    ).first()
    
    return {
        'total_reviews': stats.total_reviews or 0,
        'average_rating': round(float(stats.average_rating or 0), 2)
    }

def approve_review(db: Session, review_id: int):
    db_review = get_review_by_id(db, review_id)
    if db_review:
        db_review.is_approved = True
        db.commit()
        db.refresh(db_review)
    return db_review
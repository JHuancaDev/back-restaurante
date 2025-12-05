from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.models.order_review import OrderReview
from app.schemas.order_review import OrderReviewCreate, OrderReviewUpdate


def create_order_review(db: Session, review: OrderReviewCreate, user_id: int):
    # Verificar que la orden existe y pertenece al usuario
    order = db.query(Order).filter(
        Order.id == review.order_id,
        Order.user_id == user_id
    ).first()
    
    if not order:
        raise ValueError("Orden no encontrada o no pertenece al usuario")
    
    # Verificar que no se haya revisado esta orden antes
    existing_review = db.query(OrderReview).filter(
        OrderReview.user_id == user_id,
        OrderReview.order_id == review.order_id
    ).first()
    
    if existing_review:
        raise ValueError("Ya has revisado esta orden")
    
    # Validar ratings
    if review.overall_rating < 1 or review.overall_rating > 5:
        raise ValueError("El rating general debe estar entre 1 y 5")
    
    db_review = OrderReview(**review.dict(), user_id=user_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Cargar relaciones
    db_review = db.query(OrderReview).options(
        joinedload(OrderReview.user),
        joinedload(OrderReview.order)
    ).filter(OrderReview.id == db_review.id).first()
    
    return db_review

def get_order_reviews_by_order(db: Session, order_id: int, approved_only: bool = True):
    query = db.query(OrderReview).options(
        joinedload(OrderReview.user),
        joinedload(OrderReview.order)
    ).filter(OrderReview.order_id == order_id)
    
    if approved_only:
        query = query.filter(OrderReview.is_approved == True)
    
    return query.order_by(OrderReview.created_at.desc()).all()

def get_order_reviews_by_user(db: Session, user_id: int):
    return db.query(OrderReview).options(
        joinedload(OrderReview.user),
        joinedload(OrderReview.order)
    ).filter(OrderReview.user_id == user_id).order_by(OrderReview.created_at.desc()).all()

def get_order_stats(db: Session, order_id: int):
    stats = db.query(
        func.count(OrderReview.id).label('total_reviews'),
        func.avg(OrderReview.overall_rating).label('average_rating'),
        func.avg(OrderReview.food_quality_rating).label('food_quality_avg'),
        func.avg(OrderReview.service_rating).label('service_avg'),
        func.avg(OrderReview.delivery_rating).label('delivery_avg'),
        func.avg(OrderReview.ambiance_rating).label('ambiance_avg')
    ).filter(
        OrderReview.order_id == order_id,
        OrderReview.is_approved == True
    ).first()
    
    return {
        'total_reviews': stats.total_reviews or 0,
        'average_rating': round(float(stats.average_rating or 0), 2),
        'food_quality_avg': round(float(stats.food_quality_avg or 0), 2),
        'service_avg': round(float(stats.service_avg or 0), 2),
        'delivery_avg': round(float(stats.delivery_avg or 0), 2),
        'ambiance_avg': round(float(stats.ambiance_avg or 0), 2)
    }
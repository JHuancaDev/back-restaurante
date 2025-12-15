from sqlalchemy.orm import Session, joinedload
from app.models.extra import Extra, OrderExtra
from app.schemas.extra import ExtraCreate, ExtraUpdate, OrderExtraCreate

def get_extras(db: Session, skip: int = 0, limit: int = 100, category: str = None, available_only: bool = True):
    query = db.query(Extra)
    
    if category:
        query = query.filter(Extra.category == category)
    
    if available_only:
        query = query.filter(Extra.is_available == True)
    
    return query.order_by(Extra.name).offset(skip).limit(limit).all()

def get_extra_by_id(db: Session, extra_id: int):
    return db.query(Extra).filter(Extra.id == extra_id).first()

def create_extra(db: Session, extra: ExtraCreate):
    db_extra = Extra(**extra.dict())
    db.add(db_extra)
    db.commit()
    db.refresh(db_extra)
    return db_extra

def update_extra(db: Session, extra_id: int, extra_update: ExtraUpdate):
    db_extra = get_extra_by_id(db, extra_id)
    if not db_extra:
        return None
    
    update_data = extra_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_extra, field, value)
    
    db.commit()
    db.refresh(db_extra)
    return db_extra

def delete_extra(db: Session, extra_id: int):
    db_extra = get_extra_by_id(db, extra_id)
    if db_extra:
        db.delete(db_extra)
        db.commit()
    return db_extra

def add_extras_to_order(db: Session, order_id: int, extras_data: list):
    """
    Añadir extras a una orden existente
    """
    order_extras_info = []  # Lista de información para respuesta
    
    for extra_data in extras_data:
        extra = get_extra_by_id(db, extra_data.extra_id)
        if not extra or not extra.is_available:
            raise ValueError(f"Extra {extra_data.extra_id} no disponible")
        
        # Verificar stock si aplica
        if extra.stock < extra_data.quantity:
            raise ValueError(f"Stock insuficiente para {extra.name}")
        
        unit_price = 0.0 if extra.is_free else extra.price
        subtotal = unit_price * extra_data.quantity
        
        order_extra = OrderExtra(
            order_id=order_id,
            extra_id=extra_data.extra_id,
            quantity=extra_data.quantity,
            unit_price=unit_price,
            subtotal=subtotal
        )
        db.add(order_extra)
        db.flush()  # Obtener el ID sin hacer commit
        
        # Preparar información para respuesta
        order_extras_info.append({
            "id": order_extra.id,
            "order_id": order_extra.order_id,
            "extra_id": order_extra.extra_id,
            "quantity": order_extra.quantity,
            "unit_price": order_extra.unit_price,
            "subtotal": order_extra.subtotal,
            "extra_name": extra.name,
            "extra_image": extra.image_url,
            "is_free": extra.is_free,
            "created_at": order_extra.created_at
        })
        
        # Actualizar stock
        if extra.stock > 0:
            extra.stock -= extra_data.quantity
    
    db.commit()
    
    return order_extras_info


def get_order_extras(db: Session, order_id: int):
    return db.query(OrderExtra).options(
        joinedload(OrderExtra.extra)
    ).filter(OrderExtra.order_id == order_id).all()

def remove_extra_from_order(db: Session, order_extra_id: int):
    order_extra = db.query(OrderExtra).filter(OrderExtra.id == order_extra_id).first()
    if order_extra:
        # Restaurar stock si aplica
        extra = get_extra_by_id(db, order_extra.extra_id)
        if extra:
            extra.stock += order_extra.quantity
        
        db.delete(order_extra)
        db.commit()
    return order_extra
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None,
    available_only: bool = True
):
    """
    Obtener productos con filtros opcionales.
    """
    query = db.query(Product)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if available_only:
        query = query.filter(Product.is_available == True)
    
    return query.offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: ProductUpdate):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        return None
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product

def update_product_stock(db: Session, product_id: int, quantity: int):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db_product.stock += quantity
        if db_product.stock < 0:
            db_product.stock = 0
        db.commit()
        db.refresh(db_product)
    return db_product

def search_products(
    db: Session,
    query: str,
    category_id: int = None,
    available_only: bool = True,
    skip: int = 0,
    limit: int = 100
):
    """
    Buscar productos por nombre, descripción o SKU.
    """
    db_query = db.query(Product)

    # Filtro de búsqueda en varios campos
    search = f"%{query}%"
    db_query = db_query.filter(
        or_(
            Product.name.ilike(search),
            Product.description.ilike(search)
        )
    )

    # Filtros opcionales
    if category_id:
        db_query = db_query.filter(Product.category_id == category_id)

    if available_only:
        db_query = db_query.filter(Product.is_available == True)

    return db_query.offset(skip).limit(limit).all()
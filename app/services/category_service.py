from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """
    Obtener todas las categorías con paginación.
    """
    return db.query(Category).order_by(Category.name).offset(skip).limit(limit).all()

def get_category_by_id(db: Session, category_id: int):
    """
    Obtener una categoría por su ID.
    """
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_with_products(db: Session, category_id: int):
    """
    Obtener una categoría con sus productos asociados.
    """
    return db.query(Category).options(
        joinedload(Category.products)
    ).filter(Category.id == category_id).first()

def create_category(db: Session, category: CategoryCreate):
    """
    Crear una nueva categoría.
    """
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category_update: CategoryUpdate):
    """
    Actualizar una categoría existente.
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        return None
    
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    """
    Eliminar una categoría.
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

def get_categories_with_product_count(db: Session, skip: int = 0, limit: int = 100):
    """
    Obtener categorías con el conteo de productos.
    """
    categories_with_count = db.query(
        Category,
        func.count(Product.id).label('product_count')
    ).outerjoin(Product).group_by(Category.id).order_by(Category.name).offset(skip).limit(limit).all()
    
    result = []
    for category, product_count in categories_with_count:
        category_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "url_image": category.url_image,
            "created_at": category.created_at,
            "product_count": product_count
        }
        result.append(category_dict)
    
    return result
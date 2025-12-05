from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import (CategoryCreate, CategoryResponse,
                                  CategoryUpdate, CategoryWithCountResponse,
                                  CategoryWithProductsResponse)
from app.services.category_service import (create_category, delete_category,
                                           get_categories,
                                           get_categories_with_product_count,
                                           get_category_by_id,
                                           get_category_with_products,
                                           update_category)
from app.services.image_service import image_service

router = APIRouter(prefix="/categories", tags=["categories"])

# Rutas públicas - cualquier usuario puede ver las categorías
@router.get("/", response_model=List[CategoryResponse])
def read_categories(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las categorías disponibles.
    """
    categories = get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/with-counts/", response_model=List[CategoryWithCountResponse])
def read_categories_with_counts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Obtener categorías con el conteo de productos.
    """
    return get_categories_with_product_count(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=CategoryResponse)
def read_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una categoría específica por ID.
    """
    db_category = get_category_by_id(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return db_category

@router.get("/{category_id}/with-products", response_model=CategoryWithProductsResponse)
def read_category_with_products(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una categoría con sus productos asociados.
    """
    category_with_products = get_category_with_products(db, category_id=category_id)
    if category_with_products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return category_with_products

# Rutas de administrador - requieren autenticación y rol de administrador
# Rutas de administrador con soporte para imágenes
@router.post("/", response_model=CategoryResponse)
async def create_new_category(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Crear una nueva categoría con imagen (Solo administradores).
    """
    try:
        # Verificar si ya existe una categoría con el mismo nombre
        existing_category = db.query(Category).filter(
            func.lower(Category.name) == func.lower(name)
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con este nombre"
            )
        
        # Crear categoría sin imagen primero
        category_data = {
            "name": name,
            "description": description,
            "url_image": None
        }
        
        db_category = create_category(db=db, category=CategoryCreate(**category_data))
        
        # Si hay imagen, subirla a Firebase
        if image:
            image_url = await image_service.upload_and_save_image(
                file=image,
                folder="categories",
                db_model=db_category,
                db=db,
                model_field="url_image"
            )
            db_category.url_image = image_url
        
        return db_category
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear categoría: {str(e)}"
        )

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_existing_category(
    category_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    url_image: Optional[str] = Form(None),  # Para actualizar URL manualmente
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar una categoría existente (Solo administradores).
    """
    try:
        # Verificar si el nombre ya existe en otra categoría
        if name:
            existing_category = db.query(Category).filter(
                func.lower(Category.name) == func.lower(name),
                Category.id != category_id
            ).first()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otra categoría con este nombre"
                )
        
        db_category = get_category_by_id(db, category_id=category_id)
        if db_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        
        # Preparar datos de actualización
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        
        # Si se proporciona una URL de imagen manualmente
        if url_image is not None:
            # Si hay una imagen anterior en Firebase, eliminarla
            await image_service.delete_image_if_exists(
                image_url=db_category.url_image,
                db_model=db_category,
                db=db,
                model_field="url_image"
            )
            update_data["url_image"] = url_image
        
        # Si se sube una nueva imagen
        elif image:
            # Eliminar imagen anterior si existe
            await image_service.delete_image_if_exists(
                image_url=db_category.url_image,
                db_model=db_category,
                db=db,
                model_field="url_image"
            )
            
            # Subir nueva imagen
            new_image_url = await image_service.upload_and_save_image(
                file=image,
                folder="categories",
                db_model=db_category,
                db=db,
                model_field="url_image"
            )
            update_data["url_image"] = new_image_url
        
        # Actualizar categoría
        if update_data:
            category_update = CategoryUpdate(**update_data)
            db_category = update_category(db, category_id=category_id, category_update=category_update)
        
        return db_category
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar categoría: {str(e)}"
        )

@router.delete("/{category_id}")
async def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Eliminar una categoría (Solo administradores).
    Nota: Solo se puede eliminar si no tiene productos asociados.
    """
    # Verificar si la categoría tiene productos asociados
    has_products = db.query(Product).filter(Product.category_id == category_id).first()
    
    if has_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la categoría porque tiene productos asociados"
        )
    
    db_category = get_category_by_id(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Eliminar imagen de Firebase si existe
    await image_service.delete_image_if_exists(
        image_url=db_category.url_image
    )
    
    # Eliminar categoría de la base de datos
    db_category = delete_category(db, category_id=category_id)
    
    return {
        "message": "Categoría eliminada correctamente",
        "deleted_category": {
            "id": db_category.id,
            "name": db_category.name
        }
    }

@router.get("/search/", response_model=List[CategoryResponse])
def search_categories(
    name: str = Query(..., min_length=1, description="Nombre a buscar"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Buscar categorías por nombre.
    """
    categories = db.query(Category).filter(
        func.lower(Category.name).contains(func.lower(name))
    ).offset(skip).limit(limit).all()
    
    return categories
import json
from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.models.product import Product
from app.schemas.product import (ProductCreate, ProductCreateWithImage,
                                 ProductResponse, ProductUpdate)
from app.services.image_service import image_service
from app.services.product_service import (create_product, delete_product,
                                          get_product_by_id, get_products,
                                          search_products, update_product,
                                          update_product_stock)

router = APIRouter(prefix="/products", tags=["products"])

# Rutas públicas
@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    available_only: bool = Query(True, description="Mostrar solo productos disponibles"),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los productos disponibles.
    """
    products = get_products(
        db, 
        skip=skip, 
        limit=limit, 
        category_id=category_id,
        available_only=available_only
    )
    return products


@router.get("/search", response_model=List[ProductResponse])
def search_products_endpoint(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    available_only: bool = Query(True, description="Solo productos disponibles"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Buscar productos por nombre, descripción o SKU.
    """
    return search_products(
        db=db,
        query=q,
        category_id=category_id,
        available_only=available_only,
        skip=skip,
        limit=limit
    )


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Obtener un producto específico por ID.
    """
    db_product = get_product_by_id(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return db_product

# Rutas de administrador
# Rutas de administrador con soporte para imágenes
@router.post("/", response_model=ProductResponse)
async def create_new_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    category_id: int = Form(...),
    stock: int = Form(0),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Crear un nuevo producto con imagen (Solo administradores).
    """
    try:
        # Primero crear el producto sin imagen
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "category_id": category_id,
            "stock": stock
        }
        
        # Crear producto en la base de datos
        product = create_product(db=db, product=ProductCreate(**product_data))
        
        # Si hay imagen, subirla a Firebase y actualizar el producto
        if image:
            image_url = await image_service.upload_and_save_image(
                file=image,
                folder="products",
                db_model=product,
                db=db,
                model_field="image_url"
            )
            product.image_url = image_url
        
        return product
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_existing_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category_id: Optional[int] = Form(None),
    image_url: Optional[str] = Form(None),  # Para actualizar URL manualmente
    image: Optional[UploadFile] = File(None),
    is_available: Optional[bool] = Form(None),
    stock: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar un producto existente (Solo administradores).
    Puede actualizar imagen o URL de imagen.
    """
    try:
        db_product = get_product_by_id(db, product_id=product_id)
        if db_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Preparar datos de actualización
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if price is not None:
            update_data["price"] = price
        if category_id is not None:
            update_data["category_id"] = category_id
        if is_available is not None:
            update_data["is_available"] = is_available
        if stock is not None:
            update_data["stock"] = stock
        
        # Si se proporciona una URL de imagen manualmente
        if image_url is not None:
            # Si hay una imagen anterior en Firebase, eliminarla
            await image_service.delete_image_if_exists(
                image_url=db_product.image_url,
                db_model=db_product,
                db=db,
                model_field="image_url"
            )
            update_data["image_url"] = image_url
        
        # Si se sube una nueva imagen
        elif image:
            # Eliminar imagen anterior si existe
            await image_service.delete_image_if_exists(
                image_url=db_product.image_url,
                db_model=db_product,
                db=db,
                model_field="image_url"
            )
            
            # Subir nueva imagen
            new_image_url = await image_service.upload_and_save_image(
                file=image,
                folder="products",
                db_model=db_product,
                db=db,
                model_field="image_url"
            )
            update_data["image_url"] = new_image_url
        
        # Actualizar producto con los datos restantes
        if update_data:
            product_update = ProductUpdate(**update_data)
            db_product = update_product(db, product_id=product_id, product_update=product_update)
        
        return db_product
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar producto: {str(e)}"
        )

@router.patch("/{product_id}/image")
async def update_product_image_only(
    product_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar solo la imagen de un producto (Solo administradores).
    """
    try:
        db_product = get_product_by_id(db, product_id=product_id)
        if db_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Eliminar imagen anterior si existe
        await image_service.delete_image_if_exists(
            image_url=db_product.image_url,
            db_model=db_product,
            db=db,
            model_field="image_url"
        )
        
        # Subir nueva imagen
        new_image_url = await image_service.upload_and_save_image(
            file=image,
            folder="products",
            db_model=db_product,
            db=db,
            model_field="image_url"
        )
        
        return {
            "message": "Imagen actualizada exitosamente",
            "product_id": product_id,
            "image_url": new_image_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar imagen: {str(e)}"
        )

@router.delete("/{product_id}")
async def delete_existing_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Eliminar un producto (Solo administradores).
    También elimina la imagen asociada de Firebase.
    """
    db_product = get_product_by_id(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Eliminar imagen de Firebase si existe
    await image_service.delete_image_if_exists(
        image_url=db_product.image_url
    )
    
    # Eliminar producto de la base de datos
    db_product = delete_product(db, product_id=product_id)
    
    return {"message": "Producto eliminado correctamente"}

@router.patch("/{product_id}/stock")
def update_stock(
    product_id: int,
    stock_change: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar el stock de un producto (Solo administradores).
    """
    db_product = update_product_stock(db, product_id=product_id, quantity=stock_change)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return {
        "message": "Stock actualizado correctamente",
        "product_id": product_id,
        "new_stock": db_product.stock
    }


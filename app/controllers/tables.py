from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.schemas.table import (TableCreate, TablePositionUpdate, TableResponse,
                               TableUpdate)
from app.services.table_service import (create_table, delete_table,
                                        get_available_tables, get_table_by_id,
                                        get_tables, get_tables_with_status,
                                        update_table, update_table_position)

router = APIRouter(prefix="/tables", tags=["tables"])

# Rutas públicas - cualquier usuario puede ver las mesas disponibles
@router.get("/", response_model=List[TableResponse])
def read_tables(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    available_only: bool = Query(False, description="Mostrar solo mesas disponibles"),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las mesas.
    """
    tables = get_tables(db, skip=skip, limit=limit, available_only=available_only)
    return tables

@router.get("/available", response_model=List[TableResponse])
def read_available_tables(db: Session = Depends(get_db)):
    """
    Obtener mesas disponibles.
    """
    return get_available_tables(db)

@router.get("/{table_id}", response_model=TableResponse)
def read_table(table_id: int, db: Session = Depends(get_db)):
    """
    Obtener una mesa específica por ID.
    """
    db_table = get_table_by_id(db, table_id=table_id)
    if db_table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )
    return db_table

# Rutas de administrador
@router.post("/", response_model=TableResponse)
def create_new_table(
    table: TableCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Crear una nueva mesa (Solo administradores).
    """
    try:
        return create_table(db=db, table=table)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{table_id}", response_model=TableResponse)
def update_existing_table(
    table_id: int,
    table: TableUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar una mesa existente (Solo administradores).
    """
    try:
        db_table = update_table(db, table_id=table_id, table_update=table)
        if db_table is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mesa no encontrada"
            )
        return db_table
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{table_id}/position", response_model=TableResponse)
def update_table_position_route(
    table_id: int,
    position: TablePositionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar la posición de una mesa en el plano (Solo administradores).
    """
    db_table = update_table_position(db, table_id=table_id, position_update=position)
    if db_table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )
    return db_table

@router.delete("/{table_id}")
def delete_existing_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Eliminar una mesa (Soft delete - Solo administradores).
    """
    db_table = delete_table(db, table_id=table_id)
    if db_table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )
    return {"message": "Mesa eliminada correctamente"}


@router.get("/available-for-order", response_model=List[TableResponse])
def read_available_tables_for_order(
    capacity: Optional[int] = Query(None, description="Filtrar por capacidad mínima"),
    db: Session = Depends(get_db)
):
    """
    Obtener mesas disponibles para realizar un pedido.
    Incluye información de capacidad y posición.
    """
    try:
        tables = get_available_tables(db)
        
        # Filtrar por capacidad si se especifica
        if capacity:
            tables = [table for table in tables if table.capacity >= capacity]
            
        return tables
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener mesas disponibles: {str(e)}"
        )

@router.get("/with-status", response_model=List[dict])
def get_tables_with_order_status(db: Session = Depends(get_db)):
    """
    Obtener todas las mesas con su estado actual (disponible/ocupada)
    y información de órdenes activas.
    """
    try:
        return get_tables_with_status(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado de mesas: {str(e)}"
        )
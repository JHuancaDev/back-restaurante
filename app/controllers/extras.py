from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models.extra import OrderExtra
from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import get_db
from app.schemas.extra import (
    ExtraCreate, ExtraResponse, ExtraUpdate, 
    OrderExtraCreate, OrderExtraResponse
)
from app.services.extra_service import (
    get_extras, get_extra_by_id, create_extra,
    update_extra, delete_extra, add_extras_to_order,
    get_order_extras, remove_extra_from_order
)
from app.services.order_service import get_order_by_id
from fastapi import BackgroundTasks 

router = APIRouter(prefix="/extras", tags=["extras"])

# Rutas públicas para ver extras disponibles
@router.get("/", response_model=List[ExtraResponse])
def read_extras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    available_only: bool = Query(True, description="Mostrar solo extras disponibles"),
    free_only: bool = Query(False, description="Mostrar solo extras gratuitos"),
    db: Session = Depends(get_db)
):
    """Obtener todos los extras disponibles."""
    extras = get_extras(db, skip=skip, limit=limit, category=category, available_only=available_only)
    
    if free_only:
        extras = [extra for extra in extras if extra.is_free]
    
    return extras

@router.get("/{extra_id}", response_model=ExtraResponse)
def read_extra(extra_id: int, db: Session = Depends(get_db)):
    """Obtener un extra específico por ID."""
    db_extra = get_extra_by_id(db, extra_id)
    if db_extra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra no encontrado"
        )
    return db_extra

# Rutas de administrador para gestionar extras
@router.post("/", response_model=ExtraResponse, dependencies=[Depends(get_current_admin)])
def create_new_extra(
    extra: ExtraCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo extra (Solo administradores)."""
    return create_extra(db=db, extra=extra)

@router.put("/{extra_id}", response_model=ExtraResponse, dependencies=[Depends(get_current_admin)])
def update_existing_extra(
    extra_id: int,
    extra: ExtraUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar un extra existente (Solo administradores)."""
    db_extra = update_extra(db, extra_id=extra_id, extra_update=extra)
    if db_extra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra no encontrado"
        )
    return db_extra

@router.delete("/{extra_id}", dependencies=[Depends(get_current_admin)])
def delete_existing_extra(
    extra_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un extra (Solo administradores)."""
    db_extra = delete_extra(db, extra_id=extra_id)
    if db_extra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra no encontrado"
        )
    return {"message": "Extra eliminado correctamente"}

# Rutas para gestionar extras en órdenes
# app/controllers/extras.py - MODIFICAR EL MÉTODO add_extras_to_existing_order

@router.post("/order/{order_id}/extras", response_model=List[OrderExtraResponse])
def add_extras_to_existing_order(
    order_id: int,
    extras: List[OrderExtraCreate],
    background_tasks: BackgroundTasks,  # 🔥 AGREGAR ESTE PARÁMETRO
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Añadir extras a una orden existente.
    El usuario solo puede añadir extras a sus propias órdenes.
    """
    # Verificar que la orden existe y pertenece al usuario
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    if current_user.role != "administrador" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar esta orden"
        )
    
    try:
        # 🔥 CORRECCIÓN: added_extras_info es una lista de diccionarios
        added_extras_info = add_extras_to_order(db, order_id, extras)
        
        # 🔥 CORRECCIÓN: Crear respuestas directamente desde los diccionarios
        response_extras = []
        for extra_info in added_extras_info:
            response_extra = OrderExtraResponse(
                id=extra_info["id"],
                order_id=extra_info["order_id"],
                extra_id=extra_info["extra_id"],
                quantity=extra_info["quantity"],
                unit_price=extra_info["unit_price"],
                subtotal=extra_info["subtotal"],
                extra_name=extra_info["extra_name"],
                extra_image=extra_info["extra_image"],
                is_free=extra_info["is_free"],
                created_at=extra_info["created_at"]
            )
            response_extras.append(response_extra)
        
        # Actualizar el total de la orden
        extras_total = sum(extra_info["subtotal"] for extra_info in added_extras_info)
        order.total_amount += extras_total
        db.commit()
        
        # 🔥 CORRECCIÓN: Obtener la orden completa para enviar notificación
        complete_order = get_order_by_id(db, order_id)
        
        # 🔥 CORRECCIÓN: Preparar datos de la orden para notificación
        order_dict = {
            "id": complete_order.id,
            "user_id": complete_order.user_id,
            "user_name": complete_order.user_name,
            "order_type": complete_order.order_type,
            "table_id": complete_order.table_id,
            "table_number": complete_order.table_number,
            "table_capacity": complete_order.table_capacity,
            "delivery_address": complete_order.delivery_address,
            "special_instructions": complete_order.special_instructions,
            "status": complete_order.status,
            "total_amount": float(complete_order.total_amount) if complete_order.total_amount else 0.0,
            "estimated_time": complete_order.estimated_time,
            "is_paid": complete_order.is_paid,
            "created_at": complete_order.created_at.isoformat() if complete_order.created_at else None,
            "updated_at": complete_order.updated_at.isoformat() if complete_order.updated_at else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price) if item.unit_price else 0.0,
                    "subtotal": float(item.subtotal) if item.subtotal else 0.0,
                    "special_instructions": item.special_instructions,
                    "product_name": item.product_name,
                    "product_image": item.product_image
                }
                for item in complete_order.items
            ],
            "extras": [
                {
                    "id": extra.id,
                    "extra_id": extra.extra_id,
                    "quantity": extra.quantity,
                    "unit_price": extra.unit_price,
                    "subtotal": extra.subtotal,
                    "extra_name": extra.extra.name if extra.extra else "Extra",
                    "extra_image": extra.extra.image_url if extra.extra else None
                }
                for extra in complete_order.extras
            ]
        }
        
        # 🔥 CORRECCIÓN: Usar BackgroundTasks en lugar de asyncio.create_task
        background_tasks.add_task(send_order_updated_notification, order_dict)
        
        return response_extras
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
# 🔥 AGREGAR: Función para enviar notificación en segundo plano
def send_order_updated_notification(order_data: dict):
    """
    Función síncrona para enviar notificación de orden actualizada
    """
    try:
        import asyncio
        
        # Crear un nuevo event loop para la tarea en segundo plano
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            from app.websocket.websocket_manager import notify_order_updated
            
            # Ejecutar la notificación
            loop.run_until_complete(notify_order_updated(order_data))
            print(f"✅ Notificación de orden actualizada enviada para orden {order_data.get('id')}")
        except Exception as e:
            print(f"❌ Error en notificación de orden actualizada: {e}")
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ Error en tarea de notificación de orden actualizada: {e}")

@router.get("/order/{order_id}/extras", response_model=List[OrderExtraResponse])
def get_order_extras_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener todos los extras de una orden.
    """
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    if current_user.role != "administrador" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes ver esta orden"
        )
    
    return get_order_extras(db, order_id)

@router.delete("/order-extra/{order_extra_id}")
def remove_extra_from_order_route(
    order_extra_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Eliminar un extra de una orden.
    """
    order_extra = db.query(OrderExtra).filter(OrderExtra.id == order_extra_id).first()
    if not order_extra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extra de orden no encontrado"
        )
    
    order = get_order_by_id(db, order_extra.order_id)
    if current_user.role != "administrador" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar esta orden"
        )
    
    # Restar el subtotal del extra del total de la orden
    order.total_amount -= order_extra.subtotal
    if order.total_amount < 0:
        order.total_amount = 0
    
    remove_extra_from_order(db, order_extra_id)
    
    return {"message": "Extra eliminado de la orden correctamente"}
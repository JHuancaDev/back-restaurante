import json
import logging
from typing import List, Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Query,
                     WebSocket, WebSocketDisconnect, status)
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin, get_current_user
from app.db.database import SessionLocal, get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.order_service import (create_order, delete_order,
                                        get_order_by_id, get_orders,
                                        update_order, update_order_status)
from app.websocket.websocket_manager import manager, notify_new_order

# Agregar logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse)
async def create_new_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crear un nuevo pedido (Delivery o Dine-in).
    """
    try:
        new_order = create_order(db=db, order=order, user_id=current_user.id)
        
        # 🔥 OBTENER LA ORDEN COMPLETA CON TODAS LAS RELACIONES
        complete_order = get_order_by_id(db, new_order.id)
        
        # Convertir a dict asegurando todos los campos
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
            ]
        }
        
        print(f"📊 DATOS COMPLETOS DE ORDEN #{complete_order.id}:")
        print(f"   - user_name: {complete_order.user_name}")
        print(f"   - table_number: {complete_order.table_number}")
        print(f"   - table_capacity: {complete_order.table_capacity}")
        print(f"   - total_amount: {complete_order.total_amount}")
        print(f"   - items count: {len(complete_order.items)}")
        
        # 🔥 CORREGIDO: Usar json.dumps correctamente
        await notify_new_order(order_dict)
        
        print(f"📢 NOTIFICACIÓN ENVIADA: Orden #{complete_order.id}")
        
        return complete_order
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Enviar mensaje de confirmación de conexión
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado al servidor de órdenes en tiempo real"
        }))
        
        
        while True:
            # Esperar mensajes (mantener conexión abierta)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"📥 Mensaje recibido del cliente: {message}")
                
                # Puedes manejar diferentes tipos de mensajes aquí
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except json.JSONDecodeError:
                logger.warning(f"Mensaje no JSON recibido: {data}")
                
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        manager.disconnect(websocket)

@router.get("/my-orders", response_model=List[OrderResponse])
def read_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener los pedidos del usuario actual.
    """
    orders = get_orders(db, skip=skip, limit=limit, user_id=current_user.id)
    
    # 🔥 CORREGIR: Convertir extras para incluir extra_name
    result = []
    for order in orders:
        order_dict = order.__dict__.copy()
        
        # Convertir extras manualmente
        order_extras = []
        for extra in order.extras:
            extra_dict = {
                "id": extra.id,
                "order_id": extra.order_id,
                "extra_id": extra.extra_id,
                "quantity": extra.quantity,
                "unit_price": extra.unit_price,
                "subtotal": extra.subtotal,
                "extra_name": extra.extra.name if extra.extra else "Extra",  # 🔥 ESTO FALTA
                "created_at": extra.created_at
            }
            order_extras.append(extra_dict)
        
        order_dict["extras"] = order_extras
        result.append(order_dict)
    
    return result

@router.get("/{order_id}", response_model=OrderResponse)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener un pedido específico por ID.
    """
    db_order = get_order_by_id(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Usuarios normales solo pueden ver sus propios pedidos
    if current_user.role != "administrador" and db_order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este pedido"
        )
    
    return db_order

# Rutas de administrador
@router.get("/", response_model=List[OrderResponse])
def read_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Obtener todos los pedidos (Solo administradores).
    """
    return get_orders(db, skip=skip, limit=limit)

@router.put("/{order_id}", response_model=OrderResponse)
def update_existing_order(
    order_id: int,
    order: OrderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar un pedido existente (Solo administradores).
    """
    db_order = update_order(db, order_id=order_id, order_update=order)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    return db_order

# En app/controllers/orders.py - CORREGIR el método
# En app/controllers/orders.py - CORREGIR completamente el método
# En app/controllers/orders.py - CORREGIR completamente el método
# app/controllers/orders.py - SI YA TIENES BackgroundTasks PARA update_order_status
@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status_route(
    order_id: int,
    status: str,
    background_tasks: BackgroundTasks,  # 🔥 YA DEBERÍA ESTAR
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar el estado de un pedido (Solo administradores).
    """
    try:
        db_order = update_order_status(db, order_id=order_id, status=status)
        if db_order is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido no encontrado"
            )
        
        # 🔥 CORRECCIÓN: Función para notificación simplificada
        def send_notification():
            try:
                # Crear una nueva sesión de base de datos
                import asyncio
                from app.services.notification_service import notification_service
                
                # Crear un nuevo event loop para la tarea en segundo plano
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Crear una nueva sesión de base de datos
                with SessionLocal() as session:
                    try:
                        # Ejecutar la notificación
                        loop.run_until_complete(
                            notification_service.notify_order_status_update(session, order_id, status)
                        )
                        print(f"✅ Notificación enviada en segundo plano para orden {order_id}")
                    except Exception as e:
                        print(f"❌ Error en notificación: {e}")
                    finally:
                        loop.close()
                        
            except Exception as e:
                print(f"❌ Error en tarea de notificación: {e}")
        
        # Ejecutar en segundo plano
        background_tasks.add_task(send_notification)
        
        return db_order
        
    except Exception as e:
        print(f"❌ Error actualizando estado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando estado: {str(e)}"
        )

@router.delete("/{order_id}")
def delete_existing_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Eliminar un pedido (Solo administradores).
    """
    db_order = delete_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    return {"message": "Pedido eliminado correctamente"}
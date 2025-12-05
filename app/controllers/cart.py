import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_user
from app.db.database import get_db
from app.schemas.cart import (CartItemCreate, CartItemResponse, CartItemUpdate,
                              CartResponse, CartSummaryResponse)
from app.schemas.order import OrderCreate, OrderResponse  # Nuevo import
from app.services.cart_service import (add_item_to_cart, checkout_cart,
                                       clear_cart, get_cart_summary,
                                       get_cart_with_items,
                                       remove_item_from_cart, update_cart_item)
from app.services.table_service import get_available_tables
from app.websocket.websocket_manager import notify_new_order

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=CartResponse)
def get_my_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener el carrito del usuario actual."""
    cart = get_cart_with_items(db, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrito no encontrado"
        )
    return cart

@router.get("/summary", response_model=CartSummaryResponse)
def get_cart_summary_route(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener resumen del carrito."""
    summary = get_cart_summary(db, current_user.id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrito no encontrado"
        )
    return summary

@router.post("/items", response_model=CartResponse)
def add_cart_item(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Agregar item al carrito."""
    try:
        return add_item_to_cart(db, current_user.id, item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item_route(
    item_id: int,
    item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar item del carrito."""
    try:
        return update_cart_item(db, current_user.id, item_id, item_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Eliminar item del carrito."""
    try:
        return remove_item_from_cart(db, current_user.id, item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/clear", response_model=CartResponse)
def clear_my_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Vaciar todo el carrito."""
    return clear_cart(db, current_user.id)

@router.post("/checkout", response_model=dict)
def checkout_cart_old(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Convertir carrito en orden (esto conecta con el sistema de órdenes existente).
    En una implementación completa, esto crearía una orden desde el carrito.
    """
    cart = get_cart_with_items(db, current_user.id)
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrito vacío"
        )
    
    # Aquí iría la lógica para convertir el carrito en una orden
    # Por ahora retornamos un mensaje informativo
    return {
        "message": "Checkout iniciado",
        "cart_id": cart.id,
        "total_items": len(cart.items),
        "total_amount": sum(item.quantity * item.product.price for item in cart.items)
    }

@router.post("/checkout-with-table", response_model=OrderResponse)
async def checkout_cart_with_table(
    order_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Convertir carrito en orden con selección de mesa.
    """
    try:
        # Validar mesa si es dine_in
        if order_data.get('order_type') == 'dine_in' and order_data.get('table_id'):
            available_tables = get_available_tables(db)
            table_ids = [table.id for table in available_tables]
            if order_data['table_id'] not in table_ids:
                raise ValueError("Mesa no disponible")
        
        # Crear la orden desde el carrito
        order = checkout_cart(db, current_user.id, order_data)
        
        # 🔥 OBTENER LA ORDEN COMPLETA CON TODAS LAS RELACIONES
        from app.services.order_service import get_order_by_id
        complete_order = get_order_by_id(db, order.id)
        
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
        
        print(f"📊 DATOS COMPLETOS DE ORDEN CARRITO #{complete_order.id}:")
        print(f"   - user_name: {complete_order.user_name}")
        print(f"   - table_number: {complete_order.table_number}")
        print(f"   - table_capacity: {complete_order.table_capacity}")
        print(f"   - total_amount: {complete_order.total_amount}")
        print(f"   - items count: {len(complete_order.items)}")
        
        # Notificar via WebSocket
        await notify_new_order(order_dict)
        
        print(f"📢 NOTIFICACIÓN CARRITO ENVIADA: Orden #{complete_order.id}")
        
        return complete_order
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar pedido: {str(e)}"
        )


@router.get("/available-tables", response_model=List[Dict[str, Any]])
def get_available_tables_for_checkout(
    capacity: int = None,
    db: Session = Depends(get_db)
):
    """
    Obtener mesas disponibles para checkout.
    """
    try:
        tables = get_available_tables(db)
        
        # Filtrar por capacidad si se especifica
        if capacity:
            tables = [table for table in tables if table.capacity >= capacity]
        
        # Formatear respuesta
        result = []
        for table in tables:
            result.append({
                "id": table.id,
                "number": table.number,
                "capacity": table.capacity,
                "position_x": table.position_x,
                "position_y": table.position_y
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener mesas disponibles: {str(e)}"
        )
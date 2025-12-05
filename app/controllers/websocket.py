# app/controllers/websocket.py
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            # Opcional: puedes manejar mensajes entrantes aquí
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente desconectado")


# app/controllers/client_websocket.py - AGREGAR ESTO
@router.get("/test-websocket/{user_id}")
async def test_websocket_connection(user_id: int):
    """Endpoint para probar manualmente las notificaciones"""
    from app.db.database import SessionLocal
    from app.services.notification_service import notification_service
    from app.websocket.client_manager import client_manager
    
    test_message = {
        "type": "order_status_update",
        "order_id": 999,
        "new_status": "en_preparacion",
        "message": "Esta es una notificación de prueba",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # Crear sesión para la prueba
    with SessionLocal() as db:
        success = await notification_service.notify_order_status_update(
            db, 999, "en_preparacion"
        )
    
    return {
        "user_id": user_id,
        "message_sent": success,
        "test_message": test_message,
        "active_connections": list(client_manager.active_connections.keys())
    }
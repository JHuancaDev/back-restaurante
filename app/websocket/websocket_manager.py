# app/websocket/websocket_manager.py
import asyncio
import json
import logging
from typing import List

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ Cliente WebSocket conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 Cliente WebSocket desconectado. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error enviando mensaje personal: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                logger.debug(f"📤 Mensaje broadcast enviado a conexión activa")
            except Exception as e:
                logger.error(f"Error en broadcast: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

# Instancia global del manager
manager = ConnectionManager()

# Función para enviar notificaciones de nueva orden
async def notify_new_order(order_data: dict):
    try:
        message = {
            "type": "new_order",
            "data": order_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await manager.broadcast(json.dumps(message, default=str))
        logger.info(f"📨 Notificación de nueva orden enviada: Orden #{order_data.get('id')}")
    except Exception as e:
        logger.error(f"Error enviando notificación: {e}")
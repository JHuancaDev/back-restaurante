# app/websocket/client_manager.py - VERSIÓN MEJORADA
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ClientConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Conectar un cliente"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        # Evitar duplicados
        if websocket not in self.active_connections[user_id]:
            self.active_connections[user_id].append(websocket)
            logger.info(f"✅ Cliente {user_id} agregado. Conexiones: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Desconectar un cliente"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"🔌 Cliente {user_id} removido. Restantes: {len(self.active_connections[user_id])}")
            
            # Limpiar si no hay más conexiones
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"🧹 Usuario {user_id} sin conexiones activas")

    async def send_to_user(self, user_id: int, message: dict):
        """Enviar mensaje a un usuario específico"""
        if user_id not in self.active_connections:
            logger.warning(f"⚠️ Usuario {user_id} no tiene conexiones activas")
            return False
            
        success_count = 0
        disconnected = []
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(json.dumps(message))
                success_count += 1
                logger.info(f"📤 Mensaje enviado a usuario {user_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"❌ Error enviando a usuario {user_id}: {e}")
                disconnected.append(connection)
        
        # Limpiar conexiones muertas
        for connection in disconnected:
            self.disconnect(connection, user_id)
        
        logger.info(f"✅ {success_count} mensajes enviados exitosamente a usuario {user_id}")
        return success_count > 0

# Instancia global
client_manager = ClientConnectionManager()
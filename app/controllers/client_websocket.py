# app/controllers/client_websocket.py - VERSIÓN SIMPLIFICADA Y FUNCIONAL
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.client_manager import client_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/client")
async def client_websocket_endpoint(websocket: WebSocket, user_id: int, token: str):
    """
    WebSocket simplificado para notificaciones del cliente
    """
    logger.info(f"🔗 Intentando conectar WebSocket para usuario {user_id}")
    
    try:
        # 1. ACEPTAR la conexión PRIMERO (esto es crítico)
        await websocket.accept()
        logger.info(f"✅ WebSocket aceptado para usuario {user_id}")
        
        # 2. Registrar la conexión en el manager
        await client_manager.connect(websocket, user_id)
        logger.info(f"✅ Cliente {user_id} registrado en manager")
        
        # 3. Enviar mensaje de confirmación INMEDIATAMENTE
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado al sistema de notificaciones",
            "user_id": user_id
        }))
        logger.info(f"✅ Mensaje de confirmación enviado a usuario {user_id}")
        
        # 4. Mantener la conexión activa de forma SIMPLE
        while True:
            try:
                # Esperar cualquier mensaje del cliente
                data = await websocket.receive_text()
                logger.info(f"📨 Mensaje recibido de usuario {user_id}: {data}")
                
                # Procesar ping/pong básico
                if data.strip() == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket desconectado normalmente para usuario {user_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error procesando mensaje para usuario {user_id}: {e}")
                # No romper el loop por errores menores
                continue
                
    except Exception as e:
        logger.error(f"❌ Error crítico en WebSocket usuario {user_id}: {e}")
    finally:
        logger.info(f"🔌 Limpiando conexión del usuario {user_id}")
        client_manager.disconnect(websocket, user_id)
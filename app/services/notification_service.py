# app/services/notification_service.py - VERSIÓN MEJORADA
import logging

from sqlalchemy.orm import Session

from app.services.order_service import get_order_by_id
from app.websocket.client_manager import client_manager

logger = logging.getLogger(__name__)

class NotificationService:
    async def notify_order_ready(self, db: Session, order_id: int):
        """
        Notificar al cliente que su orden está lista
        """
        try:
            order = get_order_by_id(db, order_id)
            if not order:
                logger.error(f"Orden {order_id} no encontrada")
                return False

            notification_data = {
                "type": "order_ready",
                "order_id": order.id,
                "order_type": order.order_type,
                "status": order.status,
                "message": "¡Tu orden está lista!",
                "timestamp": order.updated_at.isoformat() if order.updated_at else None
            }

            success = await client_manager.send_to_user(order.user_id, notification_data)
            
            if success:
                logger.info(f"✅ Notificación enviada al usuario {order.user_id} - Orden #{order.id}")
            else:
                logger.warning(f"⚠️ Usuario {order.user_id} no conectado - Orden #{order.id}")
            
            return success

        except Exception as e:
            logger.error(f"❌ Error notificando orden lista: {e}")
            return False

    async def notify_order_status_update(self, db: Session, order_id: int, new_status: str):
        """
        Notificar actualización de estado de la orden
        """
        try:
            order = get_order_by_id(db, order_id)
            if not order:
                logger.error(f"Orden {order_id} no encontrada")
                return False

            status_messages = {
                "en_preparacion": "Tu orden está en preparación 👨‍🍳",
                "listo": "¡Tu orden está lista! 🎉", 
                "entregado": "Tu orden ha sido entregada 📦",
                "completado": "Orden completada ✅"
            }

            notification_data = {
                "type": "order_status_update",
                "order_id": order.id,
                "new_status": new_status,
                "message": status_messages.get(new_status, f"Estado actualizado: {new_status}"),
                "timestamp": order.updated_at.isoformat() if order.updated_at else None
            }

            success = await client_manager.send_to_user(order.user_id, notification_data)
            
            if success:
                logger.info(f"📢 Notificación de estado enviada - Orden #{order.id} -> {new_status}")
            else:
                logger.warning(f"⚠️ Usuario {order.user_id} no conectado - Orden #{order.id}")
            
            return success

        except Exception as e:
            logger.error(f"❌ Error notificando actualización de estado: {e}")
            return False

notification_service = NotificationService()
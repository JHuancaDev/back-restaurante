# app/controllers/notifications.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.auth import get_current_admin
from app.db.database import get_db
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/order/{order_id}/ready")
async def notify_order_ready(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Notificar al cliente que su orden está lista (Solo administradores)
    """
    try:
        success = await notification_service.notify_order_ready(db, order_id)
        
        if success:
            return {
                "message": "Notificación enviada al cliente",
                "order_id": order_id,
                "delivered": True
            }
        else:
            return {
                "message": "Cliente no conectado, notificación pendiente",
                "order_id": order_id,
                "delivered": False
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando notificación: {str(e)}"
        )

@router.post("/order/{order_id}/status")
async def notify_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Notificar cambio de estado de orden (Solo administradores)
    """
    try:
        success = await notification_service.notify_order_status_update(db, order_id, new_status)
        
        if success:
            return {
                "message": f"Notificación de estado {new_status} enviada",
                "order_id": order_id,
                "delivered": True
            }
        else:
            return {
                "message": "Cliente no conectado, notificación pendiente",
                "order_id": order_id,
                "delivered": False
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando notificación de estado: {str(e)}"
        )
import os
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.services.firebase_service import firebase_service


class ImageService:
    async def upload_and_save_image(
        self,
        file: UploadFile,
        folder: str = "products",
        db_model = None,  # Opcional: modelo SQLAlchemy para guardar URL
        db: Session = None,  # Opcional: sesión de BD
        model_field: str = "image_url"  # Campo donde guardar la URL
    ) -> str:
        """
        Subir imagen a Firebase y opcionalmente guardar URL en base de datos
        """
        try:
            # Validar que sea una imagen
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo debe ser una imagen"
                )
            
            # Subir a Firebase
            image_url = await firebase_service.upload_image(file, folder)
            
            # Si se proporciona un modelo y sesión, guardar la URL
            if db_model and db:
                setattr(db_model, model_field, image_url)
                db.commit()
                db.refresh(db_model)
            
            return image_url
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error procesando imagen: {str(e)}"
            )

    async def delete_image_if_exists(
        self,
        image_url: Optional[str],
        db_model = None,
        db: Session = None,
        model_field: str = "image_url"
    ) -> bool:
        """
        Eliminar imagen de Firebase si existe
        """
        if image_url and "firebasestorage.googleapis.com" in image_url:
            try:
                await firebase_service.delete_image(image_url)
                
                # Si hay un modelo, limpiar el campo
                if db_model and db:
                    setattr(db_model, model_field, None)
                    db.commit()
                    
                return True
            except Exception as e:
                print(f"⚠️ No se pudo eliminar imagen: {e}")
                return False
        return False

# Instancia global
image_service = ImageService()
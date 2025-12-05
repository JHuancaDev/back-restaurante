import os
import uuid
from pathlib import Path
from typing import Optional

import firebase_admin
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status
from firebase_admin import auth, credentials, storage
from firebase_admin.exceptions import FirebaseError

load_dotenv()

class FirebaseService:
    def __init__(self):
        # Inicializar Firebase Admin SDK
        try:
            # Opción 1: Usar variable de entorno con JSON
            firebase_credentials = os.getenv("FIREBASE_CREDENTIALS_JSON")
            if firebase_credentials:
                cred = credentials.Certificate(firebase_credentials)
            else:
                # Opción 2: Archivo de credenciales
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
                cred = credentials.Certificate(cred_path)
            
            firebase_app = firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "back-restaurante.firebasestorage.app")
            })
            self.bucket = storage.bucket()
            print("✅ Firebase Admin SDK inicializado correctamente con Storage")
        except Exception as e:
            print(f"❌ Error inicializando Firebase: {e}")
            raise

    async def upload_image(
        self, 
        file: UploadFile, 
        folder: str = "products",
        filename: Optional[str] = None
    ) -> str:
        """
        Subir imagen a Firebase Storage y retornar URL pública
        """
        try:
            # Generar nombre único para el archivo
            if not filename:
                file_extension = Path(file.filename).suffix if file.filename else '.jpg'
                filename = f"{uuid.uuid4()}{file_extension}"
            
            # Definir ruta en Firebase Storage
            blob_path = f"{folder}/{filename}"
            blob = self.bucket.blob(blob_path)
            
            # Subir archivo
            content = await file.read()
            blob.upload_from_string(
                content, 
                content_type=file.content_type or 'image/jpeg'
            )
            
            # Hacer el archivo público y obtener URL
            blob.make_public()
            public_url = blob.public_url
            
            print(f"✅ Imagen subida exitosamente: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"❌ Error subiendo imagen a Firebase: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error subiendo imagen: {str(e)}"
            )

    async def delete_image(self, image_url: str) -> bool:
        """
        Eliminar imagen de Firebase Storage
        """
        try:
            # Extraer el path del blob desde la URL
            from urllib.parse import urlparse
            
            parsed_url = urlparse(image_url)
            # El path del blob es todo después del bucket name
            path_parts = parsed_url.path.split('/')
            if len(path_parts) >= 3:
                blob_path = '/'.join(path_parts[2:])  # Saltar el bucket name
                blob = self.bucket.blob(blob_path)
                blob.delete()
                print(f"✅ Imagen eliminada: {image_url}")
                return True
            return False
            
        except Exception as e:
            print(f"⚠️ Error eliminando imagen: {e}")
            return False

    async def verify_id_token(self, id_token: str) -> dict:
        """
        Verificar token de Firebase ID
        """
        try:
            print(f"🔵 Verificando token de Firebase: {id_token[:50]}...")
            decoded_token = auth.verify_id_token(id_token)
            print(f"✅ Token verificado - UID: {decoded_token['uid']}, Email: {decoded_token.get('email')}")
            return decoded_token
        except ValueError as e:
            print(f"❌ Error de valor: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token inválido: {str(e)}"
            )
        except FirebaseError as e:
            print(f"❌ Error de Firebase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Error de autenticación: {str(e)}"
            )

    async def get_user_info(self, id_token: str) -> dict:
        """
        Obtener información del usuario desde Firebase
        """
        try:
            print(f"🔵 Obteniendo información del usuario con token: {id_token[:50]}...")
            
            decoded_token = await self.verify_id_token(id_token)
            user_id = decoded_token['uid']
            
            user = auth.get_user(user_id)
            
            user_info = {
                "uid": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "phone_number": user.phone_number,
                "provider_id": user.provider_id
            }
            
            print(f"✅ Información del usuario obtenida: {user_info['email']}")
            return user_info
            
        except Exception as e:
            print(f"❌ Error obteniendo información del usuario: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Error obteniendo información del usuario: {str(e)}"
            )

# Instancia global
firebase_service = FirebaseService()
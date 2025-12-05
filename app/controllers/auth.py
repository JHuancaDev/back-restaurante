from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (AuthResponse, GoogleLoginRequest, GoogleUserInfo,
                              Token)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import (authenticate_user, create_access_token,
                               verify_token)
from app.services.firebase_service import firebase_service
from app.services.user_service import (create_google_user, create_user,
                                       get_user_by_email,
                                       get_user_by_firebase_uid, user_exists)

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.role != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    return current_user

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado"
        )
    return create_user(db=db, user=user)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=10080)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/google", response_model=AuthResponse)
async def google_login(
    google_data: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login o registro con Google
    """
    try:
        # 1. Verificar token con Firebase
        user_info = await firebase_service.get_user_info(google_data.id_token)
        
        # 2. Buscar usuario por Firebase UID o email
        user = get_user_by_firebase_uid(db, user_info["uid"])
        is_new_user = False
        
        if not user:
            # Buscar por email por si ya existe cuenta con ese email
            user = get_user_by_email(db, user_info["email"])
            
            if user:
                # Usuario existe pero no tiene Firebase UID, actualizar
                user.firebase_uid = user_info["uid"]
                user.auth_provider = "google"
                user.email_verified = user_info.get("email_verified", False)
                if user_info.get("photo_url"):
                    user.photo_url = user_info["photo_url"]
                db.commit()
            else:
                # Crear nuevo usuario
                user = create_google_user(db, user_info)
                is_new_user = True
        
        # 3. Generar JWT token
        access_token_expires = timedelta(minutes=10080)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}, 
            expires_delta=access_token_expires
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user.to_dict(),
            is_new_user=is_new_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en autenticación con Google: {str(e)}"
        )

@router.post("/google/link")
async def link_google_account(
    google_data: GoogleLoginRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vincular cuenta de Google a usuario existente
    """
    try:
        # Verificar token con Firebase
        user_info = await firebase_service.get_user_info(google_data.id_token)
        
        # Verificar que el email coincida
        if user_info["email"] != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email de Google no coincide con tu cuenta"
            )
        
        # Verificar que no esté ya vinculado a otra cuenta
        existing_user = get_user_by_firebase_uid(db, user_info["uid"])
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta cuenta de Google ya está vinculada a otro usuario"
            )
        
        # Vincular cuenta
        current_user.firebase_uid = user_info["uid"]
        current_user.auth_provider = "google"
        current_user.email_verified = user_info.get("email_verified", False)
        if user_info.get("photo_url"):
            current_user.photo_url = user_info["photo_url"]
        
        db.commit()
        
        return {
            "message": "Cuenta de Google vinculada exitosamente",
            "user": current_user.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error vinculando cuenta de Google: {str(e)}"
        )
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import get_password_hash


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_firebase_uid(db: Session, firebase_uid: str):
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_google_user(db: Session, user_data: dict):
    """
    Crear usuario desde Google Sign-In
    """
    db_user = User(
        email=user_data["email"],
        password=None,  # No password para usuarios de Google
        full_name=user_data.get("display_name", user_data["email"].split('@')[0]),
        firebase_uid=user_data["uid"],
        auth_provider="google",
        email_verified=user_data.get("email_verified", False),
        photo_url=user_data.get("photo_url"),
        phone_number=user_data.get("phone_number"),
        role="usuario"  # Por defecto usuario normal
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def user_exists(db: Session, email: str, firebase_uid: str = None) -> bool:
    """
    Verificar si un usuario ya existe por email o firebase_uid
    """
    query = db.query(User).filter(User.email == email)
    if firebase_uid:
        query = query.filter(User.firebase_uid == firebase_uid)
    
    return query.first() is not None
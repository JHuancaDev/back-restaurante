from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="usuario")  # "usuario" o "administrador"
    is_active = Column(Boolean, default=True)

    # Nuevos campos para autenticación social
    firebase_uid = Column(String(255), unique=True, nullable=True)  # UID de Firebase
    auth_provider = Column(String(50), default="email")  # "email", "google", "apple", etc.
    email_verified = Column(Boolean, default=False)
    photo_url = Column(String(500), nullable=True)
    phone_number = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "auth_provider": self.auth_provider,
            "email_verified": self.email_verified,
            "photo_url": self.photo_url,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
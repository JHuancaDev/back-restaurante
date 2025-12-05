from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Nuevos esquemas para Google Sign-In
class GoogleLoginRequest(BaseModel):
    id_token: str

class GoogleUserInfo(BaseModel):
    uid: str
    email: str
    email_verified: bool
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    phone_number: Optional[str] = None
    provider_id: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    is_new_user: bool = False
from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, Literal
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """User creation model"""
    password: str
    email: EmailStr  # Email is required for registered users


class GuestCreate(BaseModel):
    """Guest user creation model"""
    uuid: UUID4


class MigrateGuestUser(BaseModel):
    """Model for migrating guest user to registered"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login model"""
    email: str
    password: str


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    user_type: Literal['guest', 'registered']
    created_at: datetime
    
    class Config:
        from_attributes = True


class User(BaseModel):
    """Full user model (internal use)"""
    id: int
    username: str
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    user_type: Literal['guest', 'registered']
    guest_uuid: Optional[UUID4] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

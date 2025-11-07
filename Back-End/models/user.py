from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserLogin(BaseModel):
    """User login model"""
    email: str
    password: str


class UserResponse(UserBase):
    """User response model"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class User(UserBase):
    """Full user model (internal use)"""
    id: int
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime


class URLBase(BaseModel):
    """Base URL model"""
    original_url: str
    
    @field_validator('original_url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class URLCreate(URLBase):
    """URL creation model"""
    is_private: bool = False


class URLUpdate(BaseModel):
    """URL update model"""
    original_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_private: Optional[bool] = None
    
    @field_validator('original_url')
    @classmethod
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class URLResponse(URLBase):
    """URL response model"""
    id: int
    short_code: str
    clicks: int
    is_active: bool
    is_private: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class URL(URLBase):
    """Full URL model (internal use)"""
    id: int
    short_code: str
    user_id: int
    clicks: int
    is_active: bool
    is_private: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

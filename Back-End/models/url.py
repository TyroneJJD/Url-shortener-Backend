from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, List
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


class URLBulkItem(BaseModel):
    """Single URL item for bulk creation"""
    url: str
    is_private: bool = False
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class URLBulkCreate(BaseModel):
    """Bulk URL creation model"""
    urls: List[URLBulkItem]
    
    @field_validator('urls')
    @classmethod
    def validate_urls_list(cls, v):
        if not v:
            raise ValueError('URLs list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 URLs at once')
        return v


class URLAccessHistory(BaseModel):
    """URL access history model"""
    user_email: str
    user_type: str
    accessed_at: datetime
    
    class Config:
        from_attributes = True


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
    access_history: Optional[List[URLAccessHistory]] = None
    
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
    access_history: Optional[List[dict]] = None
    
    class Config:
        from_attributes = True
        extra = 'allow'  # Permite atributos adicionales dinámicos


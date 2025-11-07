from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Token model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[int] = None
    username: Optional[str] = None

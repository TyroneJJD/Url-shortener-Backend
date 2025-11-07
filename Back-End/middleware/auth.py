from fastapi import Request, HTTPException, status
from typing import Optional
from models import User
from utils import decode_access_token
from services import auth_service


async def get_current_user_from_cookie(request: Request) -> User:
    """Get current user from HTTP-only cookie"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode token
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = await auth_service.get_user_by_id(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_optional_user_from_cookie(request: Request) -> Optional[User]:
    """Get current user from cookie if available, None otherwise"""
    try:
        return await get_current_user_from_cookie(request)
    except HTTPException:
        return None

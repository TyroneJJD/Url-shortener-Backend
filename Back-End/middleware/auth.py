from fastapi import Request, HTTPException, status, Response
from typing import Optional
from models import User
from utils import decode_access_token, create_access_token
from services import auth_service
from config import settings
from datetime import timedelta


async def get_current_user_from_cookie(request: Request, response: Response) -> User:
    """
    Get current user from HTTP-only cookie.
    Auto-refreshes token on each request (sliding session).
    """
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
    
    # Auto-refresh token (sliding session)
    new_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(
        key="access_token",
        value=new_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return user


async def get_optional_user_from_cookie(request: Request, response: Response) -> Optional[User]:
    """Get current user from cookie if available, None otherwise"""
    try:
        return await get_current_user_from_cookie(request, response)
    except HTTPException:
        return None

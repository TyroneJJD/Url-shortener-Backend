from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from models import UserLogin, UserCreate, UserResponse, User
from services import auth_service
from middleware import get_current_user_from_cookie
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(login_data: UserLogin, response: Response):
    """
    Login endpoint - Public
    Sets HTTP-only cookie with access token
    """
    user = await auth_service.authenticate_user(login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = auth_service.create_token(user)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,  # True in production (HTTPS)
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "message": "Login successful",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }


@router.post("/register")
async def register(user_data: UserCreate):
    """
    Register a new user - Public
    """
    user = await auth_service.create_user(user_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    return {
        "message": "User created successfully",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }


@router.post("/refresh")
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Refresh access token - Requires Cookie
    Generates a new token and updates the cookie
    """
    # Create new access token
    access_token = auth_service.create_token(current_user)
    
    # Update HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "message": "Token refreshed successfully",
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at
        )
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - Removes cookie
    """
    response.delete_cookie(key="access_token")
    
    return {"message": "Logout successful"}

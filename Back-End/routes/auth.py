from fastapi import APIRouter, HTTPException, status, Response, Depends
from models import UserLogin, UserCreate, UserResponse, User, GuestCreate, MigrateGuestUser
from services import auth_service
from services import guest_service
from config import settings
from middleware.auth import get_current_user_from_cookie

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
            user_type=user.user_type,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }


@router.post("/guest")
async def create_guest_session(guest_data: GuestCreate, response: Response):
    """
    Create guest user session - Public
    Sets HTTP-only cookie with guest access token (7 days)
    """
    user = await guest_service.create_guest_user(guest_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create guest session"
        )
    
    # Create User object from dict
    user_obj = User(**user, hashed_password=None)
    
    # Create access token (7 days for guests)
    access_token = auth_service.create_token(user_obj, expire_minutes=7 * 24 * 60)
    
    # Set HTTP-only cookie (7 days)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {
        "message": "Guest session created",
        "user": UserResponse(
            id=user['id'],
            username=user['username'],
            email=user.get('email'),
            user_type=user['user_type'],
            is_active=user['is_active'],
            created_at=user['created_at']
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
            user_type=user.user_type,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }


@router.post("/migrate")
async def migrate_guest_to_registered(
    migration_data: MigrateGuestUser,
    response: Response,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Migrate guest user to registered user - Requires Guest Cookie Auth
    Converts guest account to full registered account
    Removes expiration from all URLs
    """
    # Verify user is a guest
    if current_user.user_type != 'guest':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only guest users can be migrated"
        )
    
    user = await guest_service.migrate_guest_to_registered(current_user.id, migration_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create User object from dict
    user_obj = User(**user, hashed_password=None)
    
    # Create new access token (30 minutes for registered users)
    access_token = auth_service.create_token(user_obj)
    
    # Update cookie with new token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "message": "Account migrated successfully",
        "user": UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            user_type=user['user_type'],
            is_active=user['is_active'],
            created_at=user['created_at']
        )
    }


@router.get("/me")
async def get_current_user(
    response: Response,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get current authenticated user - Requires Cookie Auth
    Validates HTTP-only cookie and returns user data
    Automatically refreshes the session (sliding session)
    """
    return {
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            user_type=current_user.user_type,
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

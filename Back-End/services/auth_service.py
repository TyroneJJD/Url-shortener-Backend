from typing import Optional
from datetime import timedelta
from database import db
from models import User, UserCreate, UserLogin
from utils import verify_password, get_password_hash, create_access_token
from config import settings


class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> Optional[User]:
        """Create a new user"""
        async with db.pool.acquire() as conn:
            # Check if user already exists
            existing = await conn.fetchrow(
                'SELECT id FROM users WHERE username = $1 OR email = $2',
                user_data.username, user_data.email
            )
            
            if existing:
                return None
            
            # Hash password and create user
            hashed_password = get_password_hash(user_data.password)
            
            row = await conn.fetchrow('''
                INSERT INTO users (username, email, hashed_password)
                VALUES ($1, $2, $3)
                RETURNING id, username, email, hashed_password, is_active, created_at, updated_at
            ''', user_data.username, user_data.email, hashed_password)
            
            return User(**dict(row))
    
    @staticmethod
    async def authenticate_user(login_data: UserLogin) -> Optional[User]:
        """Authenticate a user"""
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM users WHERE email = $1 AND is_active = TRUE',
                login_data.email
            )
            
            if not row:
                return None
            
            user = User(**dict(row))
            
            if not verify_password(login_data.password, user.hashed_password):
                return None
            
            return user
    
    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM users WHERE id = $1 AND is_active = TRUE',
                user_id
            )
            
            if not row:
                return None
            
            return User(**dict(row))
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create access token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        return access_token


auth_service = AuthService()

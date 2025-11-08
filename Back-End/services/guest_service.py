from database import db
from models import GuestCreate, MigrateGuestUser
from utils.security import get_password_hash
from typing import Optional
from uuid import UUID


async def create_guest_user(guest_data: GuestCreate) -> Optional[dict]:
    """
    Create a guest user with UUID from frontend
    Returns user data if successful
    """
    async with db.pool.acquire() as conn:
    
        # Check if UUID already exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE guest_uuid = $1",
            guest_data.uuid
        )
        
        if existing:
            # Return existing guest user
            user = await conn.fetchrow(
                """
                SELECT id, username, email, user_type, guest_uuid, is_active, created_at, updated_at
                FROM users 
                WHERE id = $1
                """,
                existing['id']
            )
            return dict(user)
        
        # Create new guest user
        # Username format: guest_<first 8 chars of UUID>
        username = f"guest_{str(guest_data.uuid)[:8]}"
        
        user = await conn.fetchrow(
            """
            INSERT INTO users (username, user_type, guest_uuid, email, hashed_password)
            VALUES ($1, 'guest', $2, NULL, NULL)
            RETURNING id, username, email, user_type, guest_uuid, is_active, created_at, updated_at
            """,
            username,
            guest_data.uuid
        )
        
        return dict(user) if user else None


async def get_guest_by_uuid(guest_uuid: UUID) -> Optional[dict]:
    """
    Get guest user by UUID
    """
    async with db.pool.acquire() as conn:
    
        user = await conn.fetchrow(
            """
            SELECT id, username, email, user_type, guest_uuid, is_active, created_at, updated_at
            FROM users 
            WHERE guest_uuid = $1 AND user_type = 'guest'
            """,
            guest_uuid
        )
        
        return dict(user) if user else None


async def get_guest_url_count(user_id: int) -> int:
    """
    Get count of active URLs for a guest user
    """
    
    async with db.pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) 
            FROM urls 
            WHERE user_id = $1 AND is_active = TRUE
            """,
            user_id
        )
        
        return result or 0


async def can_create_url(user_id: int, user_type: str) -> bool:
    """
    Check if user can create a new URL
    - Guest users: max 5 URLs
    - Registered users: unlimited
    """
    if user_type == 'registered':
        return True
    
    # Guest user - check limit
    url_count = await get_guest_url_count(user_id)
    return url_count < 5


async def migrate_guest_to_registered(user_id: int, migration_data: MigrateGuestUser) -> Optional[dict]:
    """
    Migrate guest user to registered user
    - Updates user_type to 'registered'
    - Adds email and password
    - Removes guest_uuid
    - Removes expires_at from all user's URLs
    """
    
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            # Check if email already exists
            existing_email = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                migration_data.email
            )
            
            if existing_email:
                return None  # Email already registered
            
            # Check if username already exists (excluding current user)
            existing_username = await conn.fetchrow(
                "SELECT id FROM users WHERE username = $1 AND id != $2",
                migration_data.username,
                user_id
            )
            
            if existing_username:
                return None  # Username already taken
            
            # Update user to registered type
            hashed_pwd = get_password_hash(migration_data.password)
            
            user = await conn.fetchrow(
                """
                UPDATE users
                SET 
                    user_type = 'registered',
                    username = $1,
                    email = $2,
                    hashed_password = $3,
                    guest_uuid = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $4 AND user_type = 'guest'
                RETURNING id, username, email, user_type, is_active, created_at, updated_at
                """,
                migration_data.username,
                migration_data.email,
                hashed_pwd,
                user_id
            )
            
            if not user:
                return None
            
            # Remove expires_at from all user's URLs (make them permanent)
            await conn.execute(
                """
                UPDATE urls
                SET expires_at = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                user_id
            )
            
            return dict(user)


async def cleanup_expired_urls() -> int:
    """
    Delete expired URLs (for guest users)
    Returns count of deleted URLs
    """
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM urls
            WHERE expires_at IS NOT NULL 
            AND expires_at < CURRENT_TIMESTAMP
            AND is_active = TRUE
            """
        )
        
        # Extract count from result string like "DELETE 5"
        deleted_count = int(result.split()[-1]) if result else 0
        return deleted_count

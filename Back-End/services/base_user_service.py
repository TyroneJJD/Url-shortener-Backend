from abc import ABC, abstractmethod
from database import db
from typing import Optional


class BaseUserService(ABC):
    """
    Base class for user services with common URL management functionality
    """
    
    @property
    @abstractmethod
    def max_urls(self) -> Optional[int]:
        """
        Maximum number of URLs a user can create
        Returns None for unlimited
        """
        pass
    
    @property
    @abstractmethod
    def user_type(self) -> str:
        """
        User type identifier ('guest' or 'registered')
        """
        pass
    
    async def get_url_count(self, user_id: int) -> int:
        """
        Get count of active URLs for a user
        """
        async with db.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM urls 
                WHERE user_id = $1
                """,
                user_id
            )
            
            return result or 0
    
    async def can_create_url(self, user_id: int, user_type: str = None) -> bool:
        """
        Check if user can create a new URL based on their limits
        Args:
            user_id: User ID
            user_type: User type (optional, will use self.user_type if not provided)
        Returns:
            True if user can create more URLs, False otherwise
        """
        # Use provided user_type or fall back to instance user_type
        check_type = user_type or self.user_type
        
        # If user type doesn't match this service, delegate appropriately
        if check_type != self.user_type:
            return True  # Let the correct service handle it
        
        # If unlimited URLs (max_urls is None)
        if self.max_urls is None:
            return True
        
        # Check against limit
        url_count = await self.get_url_count(user_id)
        return url_count < self.max_urls
    
    async def get_remaining_urls(self, user_id: int) -> Optional[int]:
        """
        Get remaining URL slots for user
        Returns None if unlimited
        """
        if self.max_urls is None:
            return None
        
        url_count = await self.get_url_count(user_id)
        remaining = self.max_urls - url_count
        return max(0, remaining)

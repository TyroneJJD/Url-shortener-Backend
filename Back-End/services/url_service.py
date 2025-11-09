from typing import Optional, List
from datetime import datetime, timedelta
from database import db
from models import URL, URLCreate, URLUpdate
from utils import generate_short_code


class URLService:
    """URL shortening service"""
    
    @staticmethod
    async def create_url(url_data: URLCreate, user_id: int, user_type: str = 'registered') -> Optional[URL]:
        """Create a shortened URL"""
        # Generate short code automatically
        short_code = await generate_short_code()
        
        # Calculate expiration for guest users (7 days)
        expires_at = None
        if user_type == 'guest':
            expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create URL
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO urls (short_code, original_url, user_id, is_private, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, short_code, original_url, user_id, clicks, is_active, 
                          is_private, created_at, updated_at, expires_at
            ''', short_code, url_data.original_url, user_id, url_data.is_private, expires_at)
            
            return URL(**dict(row))
    
    @staticmethod
    async def get_url_by_short_code(short_code: str) -> Optional[URL]:
        """Get URL by short code"""
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM urls 
                WHERE short_code = $1 
                AND is_active = TRUE
            ''', short_code)
            
            if not row:
                return None
            
            return URL(**dict(row))
    
    @staticmethod
    async def increment_clicks(short_code: str) -> None:
        """Increment click count for a URL"""
        async with db.pool.acquire() as conn:
            await conn.execute(
                'UPDATE urls SET clicks = clicks + 1, updated_at = NOW() WHERE short_code = $1',
                short_code
            )
    
    @staticmethod
    async def get_user_urls(user_id: int, offset: int = 0, with_history: bool = False):
        """Get URLs created by a user with pagination and optional access history
        Returns tuple: (total_count, urls_list)
        """
        LIMIT = 20 # Default pagination limit
        async with db.pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval(
                'SELECT COUNT(*) FROM urls WHERE user_id = $1',
                user_id
            )
            
            # Get paginated URLs
            rows = await conn.fetch(
                '''SELECT * FROM urls 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3''',
                user_id, LIMIT, offset
            )
            
            urls = [URL(**dict(row)) for row in rows]
            
            # If with_history is True, fetch access history for each URL
            if with_history:
                for url in urls:
                    history_rows = await conn.fetch(
                        '''SELECT user_email, user_type, accessed_at 
                        FROM url_access_history 
                        WHERE url_id = $1 
                        ORDER BY accessed_at DESC''',
                        url.id
                    )
                    # Add access_history as attribute
                    url.access_history = [dict(row) for row in history_rows]
            
            return total, urls
    
    @staticmethod
    async def get_url_by_id(url_id: int, user_id: int) -> Optional[URL]:
        """Get URL by ID (only if it belongs to the user)"""
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM urls WHERE id = $1 AND user_id = $2',
                url_id, user_id
            )
            
            if not row:
                return None
            
            return URL(**dict(row))
    
    @staticmethod
    async def update_url(url_id: int, user_id: int, url_data: URLUpdate) -> Optional[URL]:
        """Update a URL"""
        async with db.pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            values = []
            param_count = 1
            
            if url_data.original_url is not None:
                updates.append(f'original_url = ${param_count}')
                values.append(url_data.original_url)
                param_count += 1
            
            if url_data.is_active is not None:
                updates.append(f'is_active = ${param_count}')
                values.append(url_data.is_active)
                param_count += 1
            
            if url_data.is_private is not None:
                updates.append(f'is_private = ${param_count}')
                values.append(url_data.is_private)
                param_count += 1
            
            if not updates:
                # No updates provided, just return current URL
                return await URLService.get_url_by_id(url_id, user_id)
            
            updates.append(f'updated_at = NOW()')
            values.extend([url_id, user_id])
            
            query = f'''
                UPDATE urls 
                SET {', '.join(updates)}
                WHERE id = ${param_count} AND user_id = ${param_count + 1}
                RETURNING id, short_code, original_url, user_id, clicks, is_active,
                          is_private, created_at, updated_at
            '''
            
            row = await conn.fetchrow(query, *values)
            
            if not row:
                return None
            
            return URL(**dict(row))
    
    @staticmethod
    async def delete_url(url_id: int, user_id: int) -> bool:
        """Delete a URL (hard delete)"""
        async with db.pool.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM urls WHERE id = $1 AND user_id = $2',
                url_id, user_id
            )
            
            return result == 'DELETE 1'
    
    @staticmethod
    async def record_url_access(url_id: int, user_email: str, user_type: str) -> None:
        """Record URL access in history"""
        async with db.pool.acquire() as conn:
            await conn.execute(
                '''INSERT INTO url_access_history (url_id, user_email, user_type)
                VALUES ($1, $2, $3)''',
                url_id, user_email, user_type
            )
    
    @staticmethod
    async def create_urls_bulk(urls_data: List[tuple], user_id: int, user_type: str = 'registered') -> List[URL]:
        """Create multiple URLs at once"""
        from datetime import datetime, timedelta
        
        # Calculate expiration for guest users (7 days)
        expires_at = None
        if user_type == 'guest':
            expires_at = datetime.utcnow() + timedelta(days=7)
        
        created_urls = []
        async with db.pool.acquire() as conn:
            for original_url, is_private in urls_data:
                # Generate unique short code
                short_code = await generate_short_code()
                
                row = await conn.fetchrow('''
                    INSERT INTO urls (short_code, original_url, user_id, is_private, expires_at)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, short_code, original_url, user_id, clicks, is_active, 
                              is_private, created_at, updated_at, expires_at
                ''', short_code, original_url, user_id, is_private, expires_at)
                
                created_urls.append(URL(**dict(row)))
        
        return created_urls


url_service = URLService()

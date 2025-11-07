import asyncpg
from typing import Optional
from config import settings


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10
        )
        await self.init_db()
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def init_db(self):
        """Initialize database tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # URLs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    short_code VARCHAR(20) UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    clicks INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_private BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index for fast lookups
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_short_code 
                ON urls(short_code) WHERE is_active = TRUE
            ''')
    
    async def get_connection(self):
        """Get a database connection from the pool"""
        return await self.pool.acquire()


# Global database instance
db = Database()

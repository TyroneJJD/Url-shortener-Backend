import asyncpg
from typing import Optional
from pathlib import Path
from config import settings


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                timeout=10
            )
            await self.init_db()
            print(f"✅ Database connected")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def init_db(self):
        """Initialize database tables from schema file"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        async with self.pool.acquire() as conn:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                await conn.execute(schema_sql)
    
    async def get_connection(self):
        """Get a database connection from the pool"""
        return await self.pool.acquire()


# Global database instance
db = Database()

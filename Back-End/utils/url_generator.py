import random
import string
from database import db


async def generate_short_code(length: int = 7) -> str:
    """
    Generate a unique short code for URLs.
    Uses base62 encoding (a-z, A-Z, 0-9) for compact URLs.
    Default length of 7 gives us 62^7 = ~3.5 trillion possible combinations.
    """
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9 (62 characters)
    
    max_attempts = 10
    for _ in range(max_attempts):
        short_code = ''.join(random.choices(characters, k=length))
        
        # Check if code already exists
        async with db.pool.acquire() as conn:
            exists = await conn.fetchval(
                'SELECT EXISTS(SELECT 1 FROM urls WHERE short_code = $1)',
                short_code
            )
            
            if not exists:
                return short_code
    
    # If we couldn't generate a unique code, try with longer length
    return await generate_short_code(length + 1)

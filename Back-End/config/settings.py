from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3002"

    #CORS
    CORS_ORIGINS: str = "http://localhost:3002"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

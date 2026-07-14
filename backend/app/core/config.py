from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EPC-Intel"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./epc_intel.db"
    
    # Auth
    JWT_SECRET: str = "super_secret_key_change_in_production"
    JWT_REFRESH_SECRET: str = "super_secret_refresh_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Storage (MinIO default)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "epcintel"
    
    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI / LLM
    GEMINI_API_KEY: str = "" # Set in .env
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = "" # Set in .env for Google Sign-In
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EPC-Intel"
    API_V1_STR: str = "/api/v1"
    
    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "epc_intel"
    
    # Auth
    JWT_SECRET: str = "super_secret_key_change_in_production"
    JWT_REFRESH_SECRET: str = "super_secret_refresh_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI / LLM
    GEMINI_API_KEY: str = "" # Set in .env
    OPENROUTER_API_KEY: str = "" # Set in .env
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = "" # Set in .env for Google Sign-In
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

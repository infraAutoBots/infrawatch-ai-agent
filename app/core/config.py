import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8001, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Google Gemini
    google_api_key: str = Field(default="AIzaSyA662j8DgIJLzWRdXPYfFwM16XR1nksleQ", env="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    
    # InfraWatch Backend
    infrawatch_api_url: str = Field(default="http://localhost:8000", env="INFRAWATCH_API_URL")
    infrawatch_api_token: Optional[str] = Field(default=None, env="INFRAWATCH_API_TOKEN")
    
    # Vector Database
    vector_db_path: str = Field(default="./vector_db", env="VECTOR_DB_PATH")
    chroma_db_path: str = Field(default="./chroma_db", env="CHROMA_DB_PATH")
    
    # Database
    database_url: str = Field(default="sqlite:///./ai_agent.db", env="DATABASE_URL")
    
    # RAG Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    top_p: float = Field(default=0.9, env="TOP_P")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/ai_agent.log", env="LOG_FILE")
    
    # Cache
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()


def get_settings() -> Settings:
    """Retorna as configurações da aplicação"""
    return settings

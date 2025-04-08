from pydantic_settings import BaseSettings
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator, PostgresDsn
from pydantic_core.core_schema import ValidationInfo
from pydantic import computed_field
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "a_very_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ALGORITHM: str = "HS256"

    # --- Database Configuration --- 
    # PostgreSQL Settings (prioritized)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "healthtracker_prod"

    # Assembled PostgreSQL DSN (Data Source Name)
    #SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    #@field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    #@classmethod
    #def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> AnyHttpUrl:
    #    if isinstance(v, str):
    #        return v
    #    
    #    # Explicitly get DB name and remove leading slash if present
    #    db_name = info.data.get("POSTGRES_DB") or ""
    #    db_path = db_name.lstrip('/') # Remove leading slash if present
    #    print(info, "SDASDASDS")
    #    return PostgresDsn.build(
    #        scheme="postgresql+psycopg2",
    #        username=info.data.get("POSTGRES_USER"),
    #        password=info.data.get("POSTGRES_PASSWORD"),
    #        host=info.data.get("POSTGRES_SERVER"),
    #        port=int(info.data.get("POSTGRES_PORT", 5432)),
    #        path=f"/{db_path}" # Ensure only one leading slash
    #    )

    # --- Use Computed Field Instead ---
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Assemble the SQLAlchemy database URI from validated settings components.
        """
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # --- Google API Key --- 
    GOOGLE_API_KEY: str = "YOUR_GOOGLE_API_KEY"

    # --- CORS --- 
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Instantiate settings
settings = Settings()
logger.info(f"Loaded GOOGLE_API_KEY: {'[MASKED]' if settings.GOOGLE_API_KEY != 'YOUR_GOOGLE_API_KEY' else settings.GOOGLE_API_KEY}") 
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
# This is useful for development environments
# In production, environment variables are usually set directly

# Construct the path to the .env file relative to this config file's directory
# config.py is in backend/app/core/, .env is in backend/
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google AI settings
    GOOGLE_API_KEY: str

    class Config:
        # This allows reading settings from the environment variables
        # Pydantic V2 uses 'case_sensitive' instead of 'env_file_encoding'
        # If using Pydantic V1, use: env_file = '.env', env_file_encoding = 'utf-8'
        case_sensitive = True

# Instantiate settings
settings = Settings() 
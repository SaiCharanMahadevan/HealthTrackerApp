import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.db.base import Base
from app.core.config import settings # Import settings

# --- Logging Configuration --- 
logging.basicConfig(
    level=logging.DEBUG, # Set the logging level (e.g., DEBUG, INFO, WARNING)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("backend.log"), # Log to a file
        logging.StreamHandler() # Also log to console (optional, remove if only file needed)
    ]
)

logger = logging.getLogger(__name__)

logger.info("Starting Health Tracker application...")

# Create database tables (This is simple for development, consider Alembic for migrations)
# Base.metadata.create_all(bind=engine) # Comment out or remove after initial setup/use migrations

app = FastAPI(title="Health Tracker API", version="0.1.0")

# --- CORS Configuration --- 
# The list of allowed origins is now loaded from settings via environment variables

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True, # Allows cookies/auth headers
    allow_methods=["*"],    # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allows all headers
)
# --- End CORS Configuration ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Health Tracker API"}


# Placeholder for future routers (auth, entries, etc.)
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")

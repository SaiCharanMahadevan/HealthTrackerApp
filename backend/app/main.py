from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
# Import Base and engine for table creation
from app.db.base import Base # Assuming models are imported here or in base_class
from app.db.session import engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- DIAGNOSTIC PRINT --- 
# Print the database URI the app is configured to use
print("-" * 80)
print(f"INFO: Attempting to use database URI: {settings.SQLALCHEMY_DATABASE_URI}")
print("-" * 80)
# --- END DIAGNOSTIC PRINT ---

# --- Create database tables --- 
# This should run once on startup if tables don't exist.
# Ensure your models (User, HealthEntry) are imported via app.db.base
print("INFO: Attempting to create database tables (if they don't exist)...")
try:
    Base.metadata.create_all(bind=engine)
    print("INFO: Database tables checked/created successfully.")
except Exception as e:
    print(f"ERROR: Failed during table creation: {e}")
    # Depending on the error, you might want the app to exit or continue
# --- End Create Tables --- 

# Mount static files directory for uploads
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR) 
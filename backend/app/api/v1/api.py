from fastapi import APIRouter

from app.api.v1.endpoints import auth, entries, reports

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# Include the entries router
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# Include other endpoint routers here later (e.g., for entries)
# from app.api.v1.endpoints import entries
# api_router.include_router(entries.router, prefix="/entries", tags=["entries"]) 
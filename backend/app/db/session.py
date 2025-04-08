from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the SQLAlchemy engine
# Use the correct setting name from config.py
# Remove connect_args as it's specific to SQLite
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI) # Convert Dsn to string for engine
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
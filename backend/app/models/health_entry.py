import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class HealthEntry(Base):
    __tablename__ = "health_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_text = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User") # Basic relationship to User model

    # Structured data fields filled by LLM parsing
    entry_type = Column(String, index=True, nullable=True) # e.g., 'food', 'weight', 'steps', 'unknown'
    value = Column(Float, nullable=True) # For weight or steps
    unit = Column(String, nullable=True) # e.g., 'kg', 'lbs', 'steps'
    parsed_data = Column(JSON, nullable=True) # Store raw JSON from LLM (e.g., food items list)

    # We will add more structured fields later (e.g., type, value, units, parsed_food_data)
    # entry_type = Column(String, index=True)
    # value = Column(Float)
    # units = Column(String)
    # parsed_data = Column(JSON) 
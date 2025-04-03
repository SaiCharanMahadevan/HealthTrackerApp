import datetime
from pydantic import BaseModel
from typing import Any, Dict, Optional, List # Import Optional, List


# Shared properties
class HealthEntryBase(BaseModel):
    entry_text: str
    timestamp: Optional[datetime.datetime] = None # Use Optional


# Properties to receive via API on creation
class HealthEntryCreate(HealthEntryBase):
    entry_text: str
    # owner_id, entry_type, value, unit, parsed_data are set by the backend


# Properties shared by models stored in DB
class HealthEntryInDBBase(HealthEntryBase):
    id: int
    owner_id: int
    timestamp: datetime.datetime
    # Add optional structured fields that might be in DB
    entry_type: Optional[str] = None 
    value: Optional[float] = None
    unit: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None # Expecting a dict-like structure

    class Config:
        orm_mode = True # Pydantic V1
        # from_attributes = True # Pydantic V2


# Properties to return to client (includes parsed data)
class HealthEntry(HealthEntryInDBBase):
    pass # Inherits all fields from HealthEntryInDBBase


# Properties stored in DB (if needed, often same as HealthEntryInDBBase)
# class HealthEntryInDB(HealthEntryInDBBase):
#     pass 
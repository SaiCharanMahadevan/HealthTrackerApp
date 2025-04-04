import datetime as dt # Use alias to avoid confusion
from pydantic import BaseModel, Json
from typing import Any, Dict, Optional, List # Import Optional, List


# Shared properties
class HealthEntryBase(BaseModel):
    entry_text: str
    # Parsed fields are not in base, they are derived


# Properties to receive via API on creation
class HealthEntryCreate(HealthEntryBase):
    pass # Only needs entry_text from user


# Properties to receive on item update
class HealthEntryUpdate(BaseModel): # Not inheriting Base, only receive text
    entry_text: str


# Properties shared by models stored in DB
class HealthEntryInDBBase(HealthEntryBase):
    id: int
    owner_id: int
    timestamp: dt.datetime
    # Add optional structured fields that might be in DB
    entry_type: Optional[str] = None 
    value: Optional[float] = None
    unit: Optional[str] = None
    parsed_data: Optional[dict] = None # Store parsed JSON details

    class Config:
        from_attributes = True # Replaces orm_mode
        # from_attributes = True # Pydantic V2


# Properties to return to client (includes parsed data)
class HealthEntry(HealthEntryInDBBase):
    pass # Inherits all fields from HealthEntryInDBBase


# Properties stored in DB (if needed, often same as HealthEntryInDBBase)
class HealthEntryInDB(HealthEntryInDBBase):
    pass 
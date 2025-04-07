import datetime as dt # Use alias to avoid confusion
from pydantic import BaseModel, Json
from typing import Any, Dict, Optional, List # Import Optional, List


# Shared properties
class HealthEntryBase(BaseModel):
    entry_text: str
    target_date_str: Optional[str] = None # Add optional target date
    # Parsed fields are not in base, they are derived


# Properties to receive via API on creation
class HealthEntryCreate(HealthEntryBase):
    pass # Only needs entry_text and target_date_str from user


# Properties to receive on item update
class HealthEntryUpdate(BaseModel): # Not inheriting Base, only receive text
    entry_text: Optional[str] = None
    # Do not allow changing timestamp/type/value directly via generic update
    # Specific update logic might be needed for parsed data, etc.


# Properties shared by models stored in DB
class HealthEntryInDBBase(HealthEntryBase):
    id: int
    owner_id: int
    timestamp: dt.datetime
    # Add optional structured fields that might be in DB
    entry_type: Optional[str] = None 
    value: Optional[float] = None
    unit: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None # Store parsed JSON details

    class Config:
        orm_mode = True # Changed from from_attributes=True for compatibility
        # from_attributes = True # Pydantic V2


# Properties to return to client (includes parsed data)
class HealthEntry(HealthEntryInDBBase):
    pass # Inherits all fields from HealthEntryInDBBase


# Properties stored in DB (if needed, often same as HealthEntryInDBBase)
class HealthEntryInDB(HealthEntryInDBBase):
    pass 
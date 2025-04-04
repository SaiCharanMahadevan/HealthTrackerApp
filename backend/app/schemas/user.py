from pydantic import BaseModel, EmailStr
from typing import Optional


# Shared properties
class UserBase(BaseModel):
    email: EmailStr


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update - REMOVING THIS
# class UserUpdate(UserBase):
#     password: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True  # Pydantic V1
        from_attributes = True  # Pydantic V2


# Properties to return to client
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str 
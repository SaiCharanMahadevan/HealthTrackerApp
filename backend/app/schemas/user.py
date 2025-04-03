from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: EmailStr


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update (optional, can add later)
# class UserUpdate(UserBase):
#     password: str | None = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True  # Pydantic V1
        # from_attributes = True # Pydantic V2


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str 
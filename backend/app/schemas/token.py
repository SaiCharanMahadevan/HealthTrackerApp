from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None # Subject (usually user identifier, e.g., email or ID)
    exp: Optional[int] = None   # Expiry timestamp (added automatically by create_access_token) 
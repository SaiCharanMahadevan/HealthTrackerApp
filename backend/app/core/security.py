from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.token import TokenPayload # We'll create this schema next

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Function to decode token (will be used in dependencies for protected routes)
# def decode_token(token: str) -> TokenPayload | None:
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         token_data = TokenPayload(**payload)
#         if token_data.exp < datetime.now(timezone.utc):
#              # Token expired, handle appropriately (e.g., raise exception)
#              # For now, returning None or raising might be options
#              return None # Or raise HTTPException(status_code=401, detail="Token has expired")
#         return token_data
#     except JWTError:
#         # Invalid token, handle appropriately
#         return None # Or raise HTTPException(status_code=401, detail="Could not validate credentials") 
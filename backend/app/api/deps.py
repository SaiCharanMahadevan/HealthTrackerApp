from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

# OAuth2PasswordBearer retrieves the token from the Authorization header
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login" # The URL endpoint that provides the token
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Pydantic V1 uses .from_orm(), V2 might use model_validate
        token_data = schemas.TokenPayload.parse_obj(payload)
        # token_data = schemas.TokenPayload.model_validate(payload) # Pydantic V2
    except (JWTError, ValidationError):
        raise credentials_exception

    user = crud.user.get_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app import crud, models, schemas
from app.api import deps
from app.core.security import create_access_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    logger.info(f"Received login request. Form data username: '{form_data.username}', Form data password length: {len(form_data.password) if form_data.password else 0}")
    logger.info(f"Login attempt for user: {form_data.username}")
    user = crud.user.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect email or password for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning(f"Login failed: Inactive user {form_data.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(
        subject=user.email
    )
    logger.info(f"Login successful, token generated for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
):
    """
    Create new user.
    """
    logger.info(f"Signup attempt for email: {user_in.email}")
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        logger.warning(f"Signup failed: Email {user_in.email} already exists.")
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud.user.create(db=db, obj_in=user_in)
    logger.info(f"Signup successful for user ID: {user.id}, email: {user.email}")
    return user


@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get current user.
    """
    logger.info(f"Fetching current user details for user ID: {current_user.id}")
    return current_user 
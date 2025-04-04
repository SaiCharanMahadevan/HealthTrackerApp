from sqlalchemy.orm import Session
from typing import Any, Union, Optional, Dict
import logging

from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema

logger = logging.getLogger(__name__)

class CRUDUser(CRUDBase[User, UserCreate, UserCreate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        logger.info(f"Attempting to retrieve user by email: {email}")
        user = db.query(User).filter(User.email == email).first()
        if user:
            logger.info(f"User found with email: {email}, ID: {user.id}")
        else:
            logger.info(f"User not found with email: {email}")
        return user

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        logger.info(f"Creating new user with email: {obj_in.email}")
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"User created successfully with ID: {db_obj.id}, email: {obj_in.email}")
        return db_obj

user = CRUDUser(User) 
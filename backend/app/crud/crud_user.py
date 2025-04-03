from sqlalchemy.orm import Session
from typing import Any, Union, Optional

from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate


class CRUDUser(CRUDBase[User, UserCreate, UserCreate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Create a dictionary from the Pydantic model, excluding the plain password
        db_obj_data = obj_in.dict(exclude={"password"})
        # Get the hashed password
        hashed_password = get_password_hash(obj_in.password)
        # Create the SQLAlchemy model instance
        db_obj = self.model(**db_obj_data, hashed_password=hashed_password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Optional: Update method if needed later
    # def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate | dict[str, any]) -> User:
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)
    #     if "password" in update_data and update_data["password"]:
    #         hashed_password = get_password_hash(update_data["password"])
    #         del update_data["password"]
    #         update_data["hashed_password"] = hashed_password
    #     return super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User) 
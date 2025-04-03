from sqlalchemy.orm import Session
# Import Optional and List from typing for compatibility with Python < 3.10
from typing import Optional, List, Dict, Any

from app.crud.base import CRUDBase
from app.models.health_entry import HealthEntry
from app.schemas.health_entry import HealthEntryCreate


class CRUDHealthEntry(CRUDBase[HealthEntry, HealthEntryCreate, HealthEntryCreate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: HealthEntryCreate,
        owner_id: int,
        parsed_result: Optional[Dict[str, Any]] = None
    ) -> HealthEntry:
        """Create a new health entry, potentially including parsed data."""
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data, owner_id=owner_id)

        # If parsed data is provided, populate the structured fields
        if parsed_result:
            db_obj.entry_type = parsed_result.get('type')
            db_obj.parsed_data = parsed_result # Store the full JSON
            # Store top-level value/unit if applicable (for weight/steps)
            if db_obj.entry_type in ['weight', 'steps']:
                db_obj.value = parsed_result.get('value')
                db_obj.unit = parsed_result.get('unit')

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[HealthEntry]:
        """Retrieve multiple health entries belonging to a specific owner."""
        return (
            db.query(self.model)
            .filter(HealthEntry.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


health_entry = CRUDHealthEntry(HealthEntry) 
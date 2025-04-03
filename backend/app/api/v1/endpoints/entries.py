from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.api import deps
from app.services.llm_parser import parse_health_entry_text

router = APIRouter()


@router.post("/", response_model=schemas.HealthEntry, status_code=201)
def create_health_entry(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    entry_in: schemas.HealthEntryCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    # background_tasks: BackgroundTasks # Inject BackgroundTasks if using
):
    """
    Create new health entry, parse with LLM (synchronously for now),
    and store structured data.
    """
    # 1. Initial save (optional, could save after parsing too)
    # entry = crud.health_entry.create_with_owner(db=db, obj_in=entry_in, owner_id=current_user.id)

    # 2. Parse text with LLM (synchronous call)
    print(f"Parsing text: '{entry_in.entry_text}'")
    parsed_result = parse_health_entry_text(entry_in.entry_text)
    print(f"Parsed result: {parsed_result}")

    # 3. Save entry with parsed data
    entry = crud.health_entry.create_with_owner(
        db=db, 
        obj_in=entry_in, 
        owner_id=current_user.id,
        parsed_result=parsed_result # Pass parsed data to CRUD
    )

    # --- Alternative: Using BackgroundTasks ---
    # entry = crud.health_entry.create_with_owner(db=db, obj_in=entry_in, owner_id=current_user.id)
    # background_tasks.add_task(process_entry_with_llm, db, entry.id)
    # return entry # Return immediately, LLM runs in background
    # --- End BackgroundTasks --- 

    # If parsing failed, the entry is still saved but without structured data
    # The response model will show nulls for those fields
    return entry


@router.get("/", response_model=List[schemas.HealthEntry])
def read_health_entries(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve health entries for the current user.
    """
    entries = crud.health_entry.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return entries

# Add endpoints for getting specific entry, updating, deleting later if needed 
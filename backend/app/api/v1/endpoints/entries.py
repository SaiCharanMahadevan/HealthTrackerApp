from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Any, List
import logging # Import logging

from app import crud, models, schemas
from app.api import deps

logger = logging.getLogger(__name__) # Get logger

router = APIRouter()


@router.post("/", response_model=schemas.HealthEntry, status_code=201)
def create_entry(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    entry_in: schemas.HealthEntryCreate, # Contains entry_text and target_date_str
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Create new health entry for the current user.
    Parsing and timestamp logic handled by CRUD layer.
    """
    logger.info(f"API: User {current_user.id} attempting to create entry with text: '{entry_in.entry_text[:50]}...', date: {entry_in.target_date_str}")
    
    # Call CRUD function, which now handles parsing and timestamp generation
    entry = crud.health_entry.create_with_owner(
        db=db, 
        obj_in=entry_in, # Pass the input schema directly
        owner_id=current_user.id
        # No parsed_result needed here anymore
    )
    # Logging is now handled within create_with_owner
    
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
    logger.info(f"User {current_user.id} reading entries, skip: {skip}, limit: {limit}")
    entries = crud.health_entry.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    logger.info(f"Returning {len(entries)} entries for user {current_user.id}")
    return entries

@router.put("/{entry_id}", response_model=schemas.HealthEntry)
def update_entry(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    entry_id: int,
    entry_in: schemas.HealthEntryUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Update a health entry. Requires new entry_text and re-parses with LLM.
    Only the owner can update their entry.
    """
    logger.info(f"User {current_user.id} attempting to update entry {entry_id}")
    entry = crud.health_entry.get(db=db, id=entry_id)
    if not entry:
        logger.warning(f"Update failed: Entry {entry_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Health entry not found")
    if entry.owner_id != current_user.id:
        logger.warning(f"Auth failure: User {current_user.id} cannot update entry {entry_id} owned by {entry.owner_id}")
        raise HTTPException(status_code=403, detail="Not authorized to update this entry")
    
    updated_entry = crud.health_entry.update(db=db, db_obj=entry, obj_in=entry_in)
    logger.info(f"Entry {entry_id} updated successfully by user {current_user.id}")
    return updated_entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    entry_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Delete a health entry.
    Only the owner can delete their entry.
    """
    logger.info(f"User {current_user.id} attempting to delete entry {entry_id}")
    # The crud.health_entry.remove method now includes ownership check and raises 403
    deleted_entry = crud.health_entry.remove(db=db, id=entry_id, user_id=current_user.id)
    if not deleted_entry:
         # If remove returns None, it means the entry wasn't found initially
        raise HTTPException(status_code=404, detail="Health entry not found")
    
    logger.info(f"Entry {entry_id} deleted successfully by user {current_user.id}")
    return 

# Add endpoints for getting specific entry, updating, deleting later if needed 
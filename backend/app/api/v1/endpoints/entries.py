from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional
import logging # Import logging

from app import crud, models, schemas
from app.api import deps
from app.services import image_storage # Import image storage service

logger = logging.getLogger(__name__) # Get logger

router = APIRouter()


@router.post("/", response_model=schemas.HealthEntry, status_code=201)
async def create_entry(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    # Use Form for text fields when accepting files
    entry_text: Optional[str] = Form(None),
    target_date_str: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None), # Accept optional image upload
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new health entry for the current user, potentially with an image.
    Handles text/image parsing and optional image storage.
    """
    logger.info(f"API: User {current_user.id} creating entry. Text provided: {bool(entry_text)}, Image provided: {bool(image)}, Date: {target_date_str}")
    
    if not entry_text and not image:
        raise HTTPException(status_code=400, detail="Either entry text or an image must be provided.")

    # 1. Handle Image Upload (if provided)
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    if image:
        image_data = await image.read() # Read image bytes for LLM
        # Attempt to save the image (after reading bytes)
        # Important: Re-seek if reading again image.file.seek(0) 
        image_url = image_storage.save_upload_file(image)
        if not image_url:
             logger.warning(f"Could not save uploaded image for user {current_user.id}")
             # Decide if this is a hard failure or just proceed without saved image URL
             # raise HTTPException(status_code=500, detail="Failed to store uploaded image.")

    # 2. Create entry object for CRUD (even if image failed to save, we might have URL)
    # Note: We pass text/date direct to CRUD now, it handles parsing
    entry_create_schema = schemas.HealthEntryCreate(
        entry_text=entry_text,
        target_date_str=target_date_str
        # image_url is handled separately below if needed, not part of create schema
    )

    # 3. Call CRUD function (which calls LLM with text and/or image_data)
    entry = crud.health_entry.create_with_owner(
        db=db, 
        obj_in=entry_create_schema, 
        owner_id=current_user.id,
        image_data=image_data # Pass image bytes to CRUD
    )

    # 4. Update entry with image URL if saved successfully
    if entry and image_url:
        try:
            entry.image_url = image_url # Update the model instance
            db.add(entry) # Stage the change
            db.commit() # Commit the change
            db.refresh(entry) # Refresh to get updated state
            logger.info(f"Updated entry {entry.id} with image_url: {image_url}")
        except Exception as e:
             logger.error(f"Failed to update entry {entry.id} with image URL {image_url}: {e}", exc_info=True)
             # Handle failure - maybe log, but entry is already created

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
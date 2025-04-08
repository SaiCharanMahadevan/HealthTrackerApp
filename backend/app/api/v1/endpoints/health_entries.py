from typing import List, Optional # Ensure Optional is imported
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import logging

# Assuming these imports exist based on context
from app import models, schemas, crud
from app.api import deps
from app.core import config # Import config
from app.services import llm_parser, nutrition_fetcher # Assuming these services exist

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.HealthEntry)
async def create_health_entry(
    *,
    db: Session = Depends(deps.get_db),
    entry_text: str = Form(...),
    # Make image Optional, default to None if not provided
    image: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(deps.get_current_active_user),
    settings: config.Settings = Depends(deps.get_settings) # Added settings dependency
):
    logger.info(f"Received health entry creation request for user {current_user.id}")
    logger.debug(f"Entry text: '{entry_text}'")
    logger.debug(f"Image provided: {'Yes' if image and image.filename else 'No'}")

    parsed_data = {}
    image_bytes_for_llm = None

    # --- LLM Processing ---
    # Check if a valid image was uploaded
    if image and image.filename and image.content_type and image.content_type.startswith('image/'):
        logger.info("Image provided, attempting multi-modal LLM processing.")
        try:
            image_bytes_for_llm = await image.read()
            # Important: Reset stream position if image object is used elsewhere or needs re-reading
            await image.seek(0)
            # Ensure you have a multi-modal processing function
            # Make sure this function exists and accepts these arguments
            parsed_data = llm_parser.process_entry_with_llm_multimodal(
                entry_text=entry_text,
                image_bytes=image_bytes_for_llm,
                api_key=settings.GOOGLE_API_KEY
            )
            logger.info("Multi-modal LLM processing successful.")
        except Exception as e:
            logger.error(f"Multi-modal LLM processing failed: {e}", exc_info=True)
            # Fallback to text-only processing upon image processing error
            logger.warning("Falling back to text-only LLM processing due to image processing error.")
            try:
                # Make sure this text-only function exists
                parsed_data = llm_parser.process_entry_with_llm_text(
                    entry_text=entry_text,
                    api_key=settings.GOOGLE_API_KEY
                )
                logger.info("Text-only LLM processing successful after fallback.")
            except Exception as text_e:
                 logger.error(f"Text-only LLM processing failed after fallback: {text_e}", exc_info=True)
                 raise HTTPException(status_code=500, detail=f"Failed to process entry text after image error: {text_e}")

    else:
        if image and image.filename:
             logger.warning(f"File provided ('{image.filename}') but it's not a valid image type ('{image.content_type}'). Proceeding with text-only.")
        else:
             logger.info("No valid image provided, using text-only LLM processing.")
        # Use the existing text-only processing function
        try:
            # Make sure this text-only function exists
            parsed_data = llm_parser.process_entry_with_llm_text(
                entry_text=entry_text,
                api_key=settings.GOOGLE_API_KEY
            )
            logger.info("Text-only LLM processing successful.")
        except Exception as e:
            logger.error(f"Text-only LLM processing failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process entry text: {e}")

    # --- Nutrition Enrichment (if applicable) ---
    # Check if parsed_data indicates a food entry and has items
    if parsed_data and parsed_data.get("entry_type") == "food" and "items" in parsed_data:
        logger.info("Food entry detected, attempting nutrition enrichment.")
        items_to_enrich = parsed_data.get("items", [])
        enriched_items = []
        if isinstance(items_to_enrich, list): # Ensure items is a list
            for item in items_to_enrich:
                # Ensure item is a dict and has a name
                if isinstance(item, dict) and "name" in item:
                    item_name = item.get("name")
                    if item_name:
                        try:
                            # Make sure this nutrition function exists
                            nutrition_info = nutrition_fetcher.get_nutrition_info(item_name)
                            if nutrition_info:
                                # Merge nutrition info into the item dict
                                item.update(nutrition_info)
                                logger.debug(f"Enriched '{item_name}' with nutrition data.")
                            else:
                                logger.warning(f"Could not find nutrition info for '{item_name}'.")
                        except Exception as enrich_e:
                            logger.error(f"Error enriching nutrition data for '{item_name}': {enrich_e}", exc_info=True)
                enriched_items.append(item) # Add item back (enriched or not, or if format was wrong)
            parsed_data["items"] = enriched_items # Update parsed_data with enriched items
        else:
            logger.warning("Parsed data for food entry 'items' key was not a list. Skipping enrichment.")


    # --- Create DB Entry ---
    try:
        # Ensure parsed_data is a dict before passing to schema
        if not isinstance(parsed_data, dict):
             logger.error(f"LLM parsing resulted in non-dict type: {type(parsed_data)}. Storing as empty dict.")
             parsed_data = {}

        health_entry_in = schemas.HealthEntryCreate(
            entry_text=entry_text,
            parsed_data=parsed_data # Use the potentially enriched data
        )
        health_entry = crud.health_entry.create_with_owner(
            db=db, obj_in=health_entry_in, owner_id=current_user.id
        )
        logger.info(f"Successfully created health entry {health_entry.id} for user {current_user.id}")
        return health_entry
    except Exception as e:
        logger.error(f"Database error creating health entry for user {current_user.id}: {e}", exc_info=True)
        # Consider more specific error handling if possible (e.g., validation errors)
        raise HTTPException(status_code=500, detail="Failed to save health entry to database.")

# Add other endpoints if they exist in this file (e.g., read_health_entries)
# ... 
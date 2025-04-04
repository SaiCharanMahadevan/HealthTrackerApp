from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import date, timedelta, datetime
# Import Optional and List from typing for compatibility with Python < 3.10
from typing import Optional, List, Dict, Any, Union
import json # Import json for parsing if needed
import logging # Import logging

from app.crud.base import CRUDBase
from app.models.health_entry import HealthEntry
from app.schemas.health_entry import HealthEntryCreate, HealthEntryUpdate
from app.schemas.report import WeeklySummary, TrendDataPoint, TrendReport # Import new schemas
from app.services.llm_parser import parse_health_entry_text # Import parser

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def _recalculate_food_totals(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculates totals based on items list if type is food."""
    if not isinstance(parsed_data, dict) or 'items' not in parsed_data or not isinstance(parsed_data['items'], list):
        logger.warning("Cannot recalculate totals: Invalid items structure in parsed_data")
        return parsed_data # Return original if structure is wrong
    
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for item in parsed_data['items']:
        if not isinstance(item, dict): continue # Skip invalid items
        try:
            # Check if amount is specified directly
            if 'specified_amount' in item:
                # Use nutrition values directly as they are for the total amount
                # Quantity is assumed to be 1 in this case (as per new prompt)
                total_calories += float(item.get('calories', 0))
                total_protein += float(item.get('protein_g', 0))
                total_carbs += float(item.get('carbs_g', 0))
                total_fat += float(item.get('fat_g', 0))
            else:
                # Otherwise, assume nutrition is per item and multiply by quantity
                qty = float(item.get('quantity', 1))
                total_calories += qty * float(item.get('calories', 0))
                total_protein += qty * float(item.get('protein_g', 0))
                total_carbs += qty * float(item.get('carbs_g', 0))
                total_fat += qty * float(item.get('fat_g', 0))
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not process item during recalculation: {item}. Error: {e}")
            continue # Skip item if values aren't numeric
    
    # Overwrite totals in the dictionary
    parsed_data['total_calories'] = round(total_calories)
    parsed_data['total_protein_g'] = round(total_protein, 1)
    parsed_data['total_carbs_g'] = round(total_carbs, 1)
    parsed_data['total_fat_g'] = round(total_fat, 1)
    
    logger.info(f"Recalculated food totals: Cals={parsed_data['total_calories']}, P={parsed_data['total_protein_g']}")
    return parsed_data

class CRUDHealthEntry(CRUDBase[HealthEntry, HealthEntryCreate, HealthEntryUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: HealthEntryCreate,
        owner_id: int,
        parsed_result: Dict[str, Any] # Expect dict from parser
    ) -> HealthEntry:
        logger.info(f"Creating health entry for owner {owner_id} with text: '{obj_in.entry_text[:50]}...'")
        
        # --- Handle Parser Result --- 
        entry_type = parsed_result.get("type", "unknown")
        value = None
        unit = None
        final_parsed_data_to_save = None
        
        if entry_type == "error":
            logger.error(f"LLM parser returned error for user {owner_id}, text: '{obj_in.entry_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            entry_type = "unknown" # Save as unknown if parser had an error
            # Keep value/unit as None, save original LLM output if available
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
        elif entry_type == "unknown":
            logger.warning(f"LLM parser returned 'unknown' for user {owner_id}, text: '{obj_in.entry_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            # Keep value/unit as None, save original LLM output if available
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
        else: # Valid type found (food, weight, steps) - extract data
            value = parsed_result.get("value")
            unit = parsed_result.get("unit")
            if entry_type == 'food':
                food_data = parsed_result.get('parsed_data')
                # --- Recalculate totals --- 
                recalculated_food_data = _recalculate_food_totals(food_data)
                final_parsed_data_to_save = recalculated_food_data
            else:
                final_parsed_data_to_save = parsed_result

        # --- Create DB Object --- 
        db_obj = HealthEntry(
            entry_text=obj_in.entry_text, # Get text from input schema
            owner_id=owner_id,
            entry_type=entry_type,
            value=value,
            unit=unit,
            parsed_data=final_parsed_data_to_save # Store potentially complex structure or fallback
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Health entry created with id {db_obj.id}, type '{db_obj.entry_type}'")
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[HealthEntry]:
        """Retrieve multiple health entries belonging to a specific owner."""
        logger.info(f"Getting health entries for owner {owner_id}, skip: {skip}, limit: {limit}")
        entries = (
            db.query(self.model)
            .filter(HealthEntry.owner_id == owner_id)
            .order_by(HealthEntry.timestamp.desc()) # Keep order consistent
            .offset(skip)
            .limit(limit)
            .all()
        )
        logger.info(f"Found {len(entries)} health entries for owner {owner_id}")
        return entries

    def update(
        self,
        db: Session,
        *,
        db_obj: HealthEntry,
        obj_in: Union[HealthEntryUpdate, dict[str, Any]]
    ) -> HealthEntry:
        if isinstance(obj_in, dict):
            new_text = obj_in.get("entry_text")
        else:
            new_text = obj_in.entry_text

        if new_text is None:
             logger.warning(f"Update called for Entry ID {db_obj.id} without new text. No update performed.")
             return db_obj # Return original object if no text provided

        # --- Re-parse the updated text --- 
        logger.info(f"Updating Entry ID: {db_obj.id}. Parsing new text: '{new_text[:50]}...'") 
        parsed_result = parse_health_entry_text(new_text)
        logger.info(f"Parser result for Entry ID {db_obj.id}: {parsed_result}")

        # --- Handle Parser Result --- 
        entry_type = parsed_result.get("type", "unknown")
        value = None
        unit = None
        final_parsed_data_to_save = None
        
        if entry_type == "error":
            logger.error(f"LLM parser returned error during update for Entry ID {db_obj.id}, text: '{new_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            entry_type = "unknown"
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
        elif entry_type == "unknown":
            logger.warning(f"LLM parser returned 'unknown' during update for Entry ID {db_obj.id}, text: '{new_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
        else: # Valid type
            value = parsed_result.get("value")
            unit = parsed_result.get("unit")
            if entry_type == 'food':
                food_data = parsed_result.get('parsed_data')
                # --- Recalculate totals --- 
                recalculated_food_data = _recalculate_food_totals(food_data)
                final_parsed_data_to_save = recalculated_food_data
            else:
                final_parsed_data_to_save = parsed_result

        # --- Prepare update data dictionary --- 
        update_data = {
            "entry_text": new_text,
            "entry_type": entry_type,
            "value": value,
            "unit": unit,
            "parsed_data": final_parsed_data_to_save,
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Saving update data for Entry ID {db_obj.id}: {{entry_type='{update_data['entry_type']}', value='{update_data['value']}'}} ...")
        
        # Use the base class update method
        updated_entry = super().update(db, db_obj=db_obj, obj_in=update_data)
        logger.info(f"Update complete for Entry ID: {db_obj.id}")
        return updated_entry

    def remove(self, db: Session, *, id: int, user_id: int) -> Optional[HealthEntry]:
        logger.info(f"Attempting to remove HealthEntry {id} for user {user_id}")
        # First, get the object to ensure it exists and belongs to the user
        obj = db.query(self.model).get(id)
        if not obj:
            logger.warning(f"Removal failed: HealthEntry {id} not found.")
            return None # Or raise HTTPException(status_code=404, detail="Entry not found")
        if obj.owner_id != user_id:
            logger.warning(f"Auth failure: User {user_id} attempted to remove HealthEntry {id} owned by {obj.owner_id}.")
            # Raise forbidden error even if found, to prevent leaking info
            raise HTTPException(status_code=403, detail="Not authorized to delete this entry") 
            
        db.delete(obj)
        db.commit()
        logger.info(f"Successfully removed HealthEntry {id} for user {user_id}")
        return obj # Return the deleted object (optional)

    # --- Reporting Functions --- 
    
    def get_weekly_summary(
        self, db: Session, *, user_id: int, target_date: date
    ) -> WeeklySummary:
        logger.info(f"Generating weekly summary for user {user_id}, week of {target_date}")
        # Determine start (Monday) and end (Sunday) of the target week
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Query for entries within the date range
        query = db.query(HealthEntry).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= datetime.combine(start_of_week, datetime.min.time()),
            HealthEntry.timestamp <= datetime.combine(end_of_week, datetime.max.time())
        )

        # --- Aggregations --- 
        # Note: These require the 'parsed_data' field to be accurately populated by the LLM
        # and assumes it contains keys like 'total_calories', 'total_protein_g', etc.
        # We'll use JSON functions if the DB supports them, or process in Python.
        # For simplicity with SQLite (which has limited JSON support built-in), 
        # we might fetch relevant entries and aggregate in Python.
        # However, let's try using SQL aggregations where possible.

        # Weight Average (using 'value' for 'weight' type)
        avg_weight = db.query(func.avg(HealthEntry.value)).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= datetime.combine(start_of_week, datetime.min.time()),
            HealthEntry.timestamp <= datetime.combine(end_of_week, datetime.max.time()),
            HealthEntry.entry_type == 'weight'
        ).scalar()

        # Steps Aggregations (using 'value' for 'steps' type)
        steps_aggregates = db.query(
            func.sum(HealthEntry.value).label('total_steps'),
            func.avg(HealthEntry.value).label('avg_daily_steps')
        ).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= datetime.combine(start_of_week, datetime.min.time()),
            HealthEntry.timestamp <= datetime.combine(end_of_week, datetime.max.time()),
            HealthEntry.entry_type == 'steps'
        ).first()

        # Food Aggregations (Requires processing parsed_data - complex in pure SQL)
        # Fetch food entries and process in Python
        food_entries = query.filter(HealthEntry.entry_type == 'food').all()
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        food_day_count = set()
        valid_food_entries = 0

        for entry in food_entries:
            if isinstance(entry.parsed_data, dict): # Check if parsed_data is a dict
                try:
                    # Safely access keys
                    calories = float(entry.parsed_data.get('total_calories', 0))
                    protein = float(entry.parsed_data.get('total_protein_g', 0))
                    carbs = float(entry.parsed_data.get('total_carbs_g', 0))
                    fat = float(entry.parsed_data.get('total_fat_g', 0))
                    
                    total_calories += calories
                    total_protein += protein
                    total_carbs += carbs
                    total_fat += fat
                    food_day_count.add(entry.timestamp.date())
                    valid_food_entries += 1
                except (ValueError, TypeError):
                    # Handle cases where data isn't a number
                    pass # Skip this entry for aggregation

        num_food_days = len(food_day_count) if len(food_day_count) > 0 else 1 # Avoid division by zero
        
        summary = WeeklySummary(
            week_start_date=start_of_week,
            week_end_date=end_of_week,
            avg_daily_calories=(total_calories / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_protein_g=(total_protein / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_carbs_g=(total_carbs / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_fat_g=(total_fat / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_weight_kg=avg_weight,
            avg_daily_steps=steps_aggregates.avg_daily_steps if steps_aggregates else None,
            total_steps=int(steps_aggregates.total_steps) if steps_aggregates and steps_aggregates.total_steps is not None else None,
        )
        logger.info(f"Weekly summary generated for user {user_id}, week {start_of_week} to {end_of_week}")
        return summary

    def get_trends(
        self, db: Session, *, user_id: int, start_date: date, end_date: date
    ) -> TrendReport:
        logger.info(f"Generating trends report for user {user_id}, from {start_date} to {end_date}")
        # Weight Trends
        weight_data = db.query(HealthEntry.timestamp, HealthEntry.value).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= datetime.combine(start_date, datetime.min.time()),
            HealthEntry.timestamp <= datetime.combine(end_date, datetime.max.time()),
            HealthEntry.entry_type == 'weight'
        ).order_by(HealthEntry.timestamp.asc()).all()

        weight_trends = [TrendDataPoint(timestamp=ts, value=val) for ts, val in weight_data if val is not None]

        # Steps Trends (daily totals)
        # Group by date and sum steps
        steps_data_daily = db.query(
            func.date(HealthEntry.timestamp).label('entry_date'), 
            func.sum(HealthEntry.value).label('total_steps')
        ).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= datetime.combine(start_date, datetime.min.time()),
            HealthEntry.timestamp <= datetime.combine(end_date, datetime.max.time()),
            HealthEntry.entry_type == 'steps'
        ).group_by('entry_date').order_by('entry_date').all()

        # Convert date string from query to datetime.date object before combining
        steps_trends = [TrendDataPoint(timestamp=datetime.combine(date.fromisoformat(day), datetime.min.time()), value=total) for day, total in steps_data_daily if total is not None]

        report = TrendReport(
            start_date=start_date,
            end_date=end_date,
            weight_trends=weight_trends,
            steps_trends=steps_trends
        )
        logger.info(f"Trends report generated for user {user_id}, found {len(weight_trends)} weight points, {len(steps_trends)} steps points")
        return report


health_entry = CRUDHealthEntry(HealthEntry) 
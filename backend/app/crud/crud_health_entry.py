from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException
from datetime import date, timedelta, datetime, time, timezone
# Import Optional and List from typing for compatibility with Python < 3.10
from typing import Optional, List, Dict, Any, Union
import json # Import json for parsing if needed
import logging # Import logging

from app.crud.base import CRUDBase
from app.models.health_entry import HealthEntry
from app.schemas.health_entry import HealthEntryCreate, HealthEntryUpdate
from app.schemas.report import WeeklySummary, TrendDataPoint, TrendReport, DailySummary # Import new schemas
from app.services.llm_parser import parse_health_entry_text # Import parser
from app.services.food_data_service import get_nutrition_from_off # Import OFF service

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
        logger.info(f"Processing create for owner {owner_id}, text: '{obj_in.entry_text[:50]}...'")
        entry_type = parsed_result.get("type", "unknown")
        value = None
        unit = None
        final_parsed_data_to_save = parsed_result # Start with original parsed data

        if entry_type == "error" or entry_type == "unknown":
            logger.error(f"LLM parser returned error for user {owner_id}, text: '{obj_in.entry_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            entry_type = "unknown"
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
        
        elif entry_type == 'food':
            food_data = parsed_result.get('parsed_data')
            if isinstance(food_data, dict) and 'items' in food_data and isinstance(food_data['items'], list):
                processed_items = []
                for item in food_data['items']:
                    if not isinstance(item, dict): continue
                    item_name = item.get('item')
                    item['nutrition_source'] = 'LLM Estimate' # Default source
                    
                    if item_name:
                        # --- Attempt OFF Lookup --- 
                        off_data = get_nutrition_from_off(item_name)
                        if off_data:
                            logger.info(f"Using OFF data for item: {item_name}")
                            item['nutrition_source'] = off_data['source']
                            # Scaling logic (Initial simple version: only handles grams)
                            scaling_factor = None
                            amount = item.get('specified_amount')
                            amount_unit = item.get('specified_unit')
                            if amount is not None and amount_unit and amount_unit.lower() == 'g':
                                try:
                                    scaling_factor = float(amount) / 100.0
                                except (ValueError, TypeError):
                                    logger.warning(f"Could not determine scaling factor for {amount}{amount_unit} of {item_name}")
                            
                            if scaling_factor is not None:
                                try:
                                    # Overwrite LLM estimates with scaled OFF data
                                    item['calories'] = round(off_data['calories_100g'] * scaling_factor)
                                    item['protein_g'] = round(off_data['protein_100g'] * scaling_factor, 1)
                                    item['carbs_g'] = round(off_data['carbs_100g'] * scaling_factor, 1)
                                    item['fat_g'] = round(off_data['fat_100g'] * scaling_factor, 1)
                                    logger.info(f"Applied scaled OFF data for {item_name}")
                                except Exception as e:
                                    logger.error(f"Error applying scaled OFF data for {item_name}: {e}", exc_info=False)
                                    # Fallback: Keep LLM estimates if scaling fails
                            else:
                                logger.info(f"Could not scale OFF data for {item_name}, using LLM estimates.")
                        else:
                            logger.info(f"No usable OFF data found for {item_name}, using LLM estimates.")
                    processed_items.append(item) # Add item (potentially updated)
                
                food_data['items'] = processed_items # Update items list
                # --- Recalculate totals using potentially updated items --- 
                recalculated_food_data = _recalculate_food_totals(food_data)
                final_parsed_data_to_save = recalculated_food_data
            else:
                # Handle case where parsed_data is missing items etc.
                logger.warning(f"Invalid food data structure from LLM for text: '{obj_in.entry_text[:50]}...'")
                entry_type = "unknown" # Fallback to unknown
                final_parsed_data_to_save = food_data # Save what we got
                
        else: # weight, steps - handled by base fields
            value = parsed_result.get("value")
            unit = parsed_result.get("unit")
            final_parsed_data_to_save = parsed_result # Save original parser result

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
        final_parsed_data_to_save = parsed_result # Start with original

        if entry_type == "error" or entry_type == "unknown":
            logger.error(f"LLM parser returned error during update for Entry ID {db_obj.id}, text: '{new_text[:50]}...' - Detail: {parsed_result.get('error_detail')}")
            entry_type = "unknown"
            final_parsed_data_to_save = parsed_result.get('original_llm_output') or parsed_result
       
        elif entry_type == 'food':
            food_data = parsed_result.get('parsed_data')
            if isinstance(food_data, dict) and 'items' in food_data and isinstance(food_data['items'], list):
                processed_items = []
                for item in food_data['items']:
                    if not isinstance(item, dict): continue
                    item_name = item.get('item')
                    item['nutrition_source'] = 'LLM Estimate' 
                    if item_name:
                        off_data = get_nutrition_from_off(item_name)
                        if off_data:
                            item['nutrition_source'] = off_data['source']
                            scaling_factor = None
                            amount = item.get('specified_amount')
                            amount_unit = item.get('specified_unit')
                            if amount is not None and amount_unit and amount_unit.lower() == 'g':
                                try: scaling_factor = float(amount) / 100.0
                                except: pass
                            if scaling_factor is not None:
                                try:
                                    item['calories'] = round(off_data['calories_100g'] * scaling_factor)
                                    item['protein_g'] = round(off_data['protein_100g'] * scaling_factor, 1)
                                    item['carbs_g'] = round(off_data['carbs_100g'] * scaling_factor, 1)
                                    item['fat_g'] = round(off_data['fat_100g'] * scaling_factor, 1)
                                except Exception as e: pass
                        processed_items.append(item)
                food_data['items'] = processed_items
                recalculated_food_data = _recalculate_food_totals(food_data)
                final_parsed_data_to_save = recalculated_food_data
            else:
                logger.warning(f"Invalid food data structure during update for Entry ID {db_obj.id}")
                entry_type = "unknown"
                final_parsed_data_to_save = food_data
                
        else: # weight, steps
            value = parsed_result.get("value")
            unit = parsed_result.get("unit")
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
    
    def _get_utc_bounds_for_local_date(self, target_date: date, tz_offset_minutes: int) -> tuple[datetime, datetime]:
        """Calculates the UTC start and end datetimes corresponding to a full local day."""
        # Offset from UTC. Note: getTimezoneOffset() is opposite sign of common TZ notation (SGT=+8, offset=-480)
        offset_delta = timedelta(minutes=-tz_offset_minutes) # Reverse sign for calculation
        
        # Local day start: YYYY-MM-DD 00:00:00 in local time
        local_start_naive = datetime.combine(target_date, time.min)
        # Convert to UTC by subtracting the offset
        utc_start = local_start_naive - offset_delta

        # Local day end is the start of the *next* local day
        local_end_naive = datetime.combine(target_date + timedelta(days=1), time.min)
        # Convert to UTC by subtracting the offset
        utc_end = local_end_naive - offset_delta
        
        logger.debug(f"Local date: {target_date}, Offset mins: {tz_offset_minutes} ({offset_delta})")
        logger.debug(f"Calculated UTC Bounds: {utc_start} to {utc_end}")
        # Return UTC start (inclusive) and UTC end (exclusive for the next day's start)
        return utc_start, utc_end
        

    def get_weekly_summary(
        self, db: Session, *, user_id: int, target_date: date, tz_offset_minutes: int = 0
    ) -> WeeklySummary:
        logger.info(f"CRUD: Weekly summary user {user_id}, week of {target_date}, offset {tz_offset_minutes}")
        # Determine start (Monday) and end (Sunday) of the target week based on LOCAL date
        start_of_week_local = target_date - timedelta(days=target_date.weekday())
        end_of_week_local = start_of_week_local + timedelta(days=6)
        
        # Get UTC boundaries for the start and end days of the week
        utc_week_start, _ = self._get_utc_bounds_for_local_date(start_of_week_local, tz_offset_minutes)
        _, utc_week_end = self._get_utc_bounds_for_local_date(end_of_week_local, tz_offset_minutes)
        
        logger.debug(f"Querying weekly summary between UTC {utc_week_start} and {utc_week_end}")

        # Query for entries within the adjusted UTC date range
        query = db.query(HealthEntry).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_week_start, # Use calculated UTC start
            HealthEntry.timestamp < utc_week_end      # Use calculated UTC end (exclusive)
        )
        
        # --- Aggregations --- (Logic mostly unchanged, but applied to the correct UTC range)
        # Weight Average
        avg_weight = db.query(func.avg(HealthEntry.value)).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_week_start,
            HealthEntry.timestamp < utc_week_end,
            HealthEntry.entry_type == 'weight',
            HealthEntry.unit.ilike('kg%') # Keep corrected filter
        ).scalar()

        # Steps Aggregations
        steps_aggregates = db.query(
            func.sum(HealthEntry.value).label('total_steps'),
            func.avg(HealthEntry.value).label('avg_daily_steps') # Note: This avg might be slightly off if days have varying entries
        ).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_week_start,
            HealthEntry.timestamp < utc_week_end,
            HealthEntry.entry_type == 'steps' # Keep corrected filter
        ).first()

        # Food Aggregations (Fetch entries based on new UTC range)
        food_entries = query.filter(HealthEntry.entry_type == 'food').all()
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        food_day_count = set() # Recalculate based on actual timestamps
        valid_food_entries = 0
        for entry in food_entries:
            if isinstance(entry.parsed_data, dict):
                try:
                    calories = float(entry.parsed_data.get('total_calories', 0))
                    protein = float(entry.parsed_data.get('total_protein_g', 0))
                    carbs = float(entry.parsed_data.get('total_carbs_g', 0))
                    fat = float(entry.parsed_data.get('total_fat_g', 0))
                    
                    total_calories += calories
                    total_protein += protein
                    total_carbs += carbs
                    total_fat += fat
                    
                    # Determine local date for counting unique food days
                    entry_local_time = entry.timestamp + timedelta(minutes=-tz_offset_minutes)
                    food_day_count.add(entry_local_time.date())
                    valid_food_entries += 1
                except (ValueError, TypeError): pass

        num_food_days = len(food_day_count) if len(food_day_count) > 0 else 1

        summary = WeeklySummary(
            week_start_date=start_of_week_local,
            week_end_date=end_of_week_local,
            avg_daily_calories=(total_calories / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_protein_g=(total_protein / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_carbs_g=(total_carbs / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_daily_fat_g=(total_fat / num_food_days) if num_food_days > 0 and valid_food_entries > 0 else None,
            avg_weight_kg=avg_weight,
            avg_daily_steps=steps_aggregates.avg_daily_steps if steps_aggregates else None, # This average might need rethinking for accuracy
            total_steps=int(steps_aggregates.total_steps) if steps_aggregates and steps_aggregates.total_steps is not None else None,
        )
        logger.info(f"Weekly summary generated for user {user_id}, local week {start_of_week_local} to {end_of_week_local}")
        return summary

    def get_trends(
        self, db: Session, *, user_id: int, start_date: date, end_date: date, tz_offset_minutes: int = 0
    ) -> TrendReport:
        logger.info(f"CRUD: Trends report user {user_id}, {start_date} to {end_date}, offset {tz_offset_minutes}")
        
        # Get UTC boundaries for the start and end local dates
        utc_start, _ = self._get_utc_bounds_for_local_date(start_date, tz_offset_minutes)
        _, utc_end = self._get_utc_bounds_for_local_date(end_date, tz_offset_minutes)
        
        logger.debug(f"Querying trends between UTC {utc_start} and {utc_end}")

        # Weight Trends (Query within adjusted UTC range)
        weight_data = db.query(HealthEntry.timestamp, HealthEntry.value).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_start,
            HealthEntry.timestamp < utc_end,
            HealthEntry.entry_type == 'weight',
            HealthEntry.unit.ilike('kg%')
        ).order_by(HealthEntry.timestamp.asc()).all()
        weight_trends = [TrendDataPoint(timestamp=ts, value=val) for ts, val in weight_data if val is not None]

        # Steps Trends (Daily totals - Grouping needs care with timezone)
        # Option 1: Group by UTC date - might split local days
        # Option 2: Fetch all step entries and group in Python by local date (Safer)
        
        step_entries = db.query(HealthEntry.timestamp, HealthEntry.value).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_start,
            HealthEntry.timestamp < utc_end,
            HealthEntry.entry_type == 'steps'
        ).order_by(HealthEntry.timestamp.asc()).all()

        # Group steps by local date in Python
        daily_steps = {}
        offset_delta = timedelta(minutes=-tz_offset_minutes)
        for ts_utc, val in step_entries:
            if val is None: continue
            local_date = (ts_utc + offset_delta).date()
            daily_steps[local_date] = daily_steps.get(local_date, 0) + float(val)
            
        # Convert grouped data to TrendDataPoints (using start of local day as timestamp)
        steps_trends = [
            TrendDataPoint(timestamp=datetime.combine(day, time.min), value=total) 
            for day, total in sorted(daily_steps.items())
        ]
        
        report = TrendReport(
            start_date=start_date,
            end_date=end_date,
            weight_trends=weight_trends,
            steps_trends=steps_trends
        )
        logger.info(f"Trends report generated for user {user_id}")
        return report

    def get_daily_summary(
        self, db: Session, *, user_id: int, target_date: date, tz_offset_minutes: int = 0
    ) -> DailySummary:
        """Generates a daily summary for a given user and date, adjusted for local timezone."""
        
        # Calculate UTC bounds for the requested local date
        utc_start, utc_end = self._get_utc_bounds_for_local_date(target_date, tz_offset_minutes)
        
        logger.info(f"CRUD: Daily summary user {user_id}, local date {target_date}, offset {tz_offset_minutes}")
        # Base query using calculated UTC bounds
        entries = db.query(HealthEntry).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_start, 
            HealthEntry.timestamp < utc_end # Use exclusive end for day boundary
        ).all()
        
        logger.debug(f"Found {len(entries)} total entries for the adjusted UTC range.")

        # Calculate total calories from food entries
        total_calories = 0
        food_entries = [e for e in entries if e.entry_type == 'food']
        logger.debug(f"Found {len(food_entries)} food entries.")
        for entry in food_entries:
            logger.debug(f"Processing food entry {entry.id}: Text='{entry.entry_text}', Parsed='{entry.parsed_data}'")
            if entry.parsed_data and isinstance(entry.parsed_data, dict):
                calories = entry.parsed_data.get('total_calories', 0)
                if calories is None: calories = 0
                try:
                     total_calories += float(calories)
                     logger.debug(f"  Added {calories} kcal. Running total: {total_calories}")
                except (ValueError, TypeError):
                     logger.warning(f"  Could not parse calories ('{calories}') as float for entry {entry.id}.")
            else:
                logger.debug(f"  Skipping calorie calculation for entry {entry.id}: No valid parsed_data dictionary.")

        # Calculate total steps using SQL aggregation
        total_steps_query = db.query(func.sum(HealthEntry.value)).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_start,
            HealthEntry.timestamp < utc_end,
            HealthEntry.entry_type == 'steps' 
        ).scalar()
        total_steps = total_steps_query if total_steps_query is not None else 0
        logger.debug(f"SQL query result for total steps: {total_steps_query}. Using value: {total_steps}")

        # Get the last recorded weight for the day
        last_weight_entry = db.query(HealthEntry.value).filter(
            HealthEntry.owner_id == user_id,
            HealthEntry.timestamp >= utc_start,
            HealthEntry.timestamp < utc_end,
            HealthEntry.entry_type == 'weight', 
            HealthEntry.unit.ilike('kg%') 
        ).order_by(desc(HealthEntry.timestamp)).first()
        last_weight_kg = last_weight_entry[0] if last_weight_entry else None
        logger.debug(f"SQL query result for last weight: {last_weight_entry}. Using value: {last_weight_kg}")

        # Create summary object (using the original target_date for the label)
        summary_data = DailySummary(
            date=target_date, 
            total_calories=total_calories,
            total_steps=total_steps,
            last_weight_kg=last_weight_kg
        )
        logger.info(f"Generated Daily Summary (Local Date {target_date}): {summary_data}")
        return summary_data

health_entry = CRUDHealthEntry(HealthEntry) 
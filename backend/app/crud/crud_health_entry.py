from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta, datetime
# Import Optional and List from typing for compatibility with Python < 3.10
from typing import Optional, List, Dict, Any

from app.crud.base import CRUDBase
from app.models.health_entry import HealthEntry
from app.schemas.health_entry import HealthEntryCreate
from app.schemas.report import WeeklySummary, TrendDataPoint, TrendReport # Import new schemas


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
            .order_by(HealthEntry.timestamp.desc()) # Keep order consistent
            .offset(skip)
            .limit(limit)
            .all()
        )

    # --- Reporting Functions --- 
    
    def get_weekly_summary(
        self, db: Session, *, user_id: int, target_date: date
    ) -> WeeklySummary:
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
        return summary

    def get_trends(
        self, db: Session, *, user_id: int, start_date: date, end_date: date
    ) -> TrendReport:
        
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
        return report


health_entry = CRUDHealthEntry(HealthEntry) 
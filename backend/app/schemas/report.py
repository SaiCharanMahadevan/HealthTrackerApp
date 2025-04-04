from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

# --- Weekly Summary Schemas ---

class WeeklySummaryBase(BaseModel):
    week_start_date: date
    week_end_date: date
    avg_daily_calories: Optional[float] = None
    avg_daily_protein_g: Optional[float] = None
    avg_daily_carbs_g: Optional[float] = None
    avg_daily_fat_g: Optional[float] = None
    avg_weight_kg: Optional[float] = None
    avg_daily_steps: Optional[float] = None
    total_steps: Optional[int] = None

class WeeklySummary(WeeklySummaryBase):
    pass # No extra fields needed for response currently


# --- Trend Schemas ---

class TrendDataPoint(BaseModel):
    timestamp: datetime # Or just date? Let's use datetime for flexibility
    value: float

class TrendReportBase(BaseModel):
    start_date: date
    end_date: date
    weight_trends: List[TrendDataPoint] = []
    steps_trends: List[TrendDataPoint] = []
    # Add calorie/macro trends later if needed

class TrendReport(TrendReportBase):
    pass # No extra fields needed for response currently 
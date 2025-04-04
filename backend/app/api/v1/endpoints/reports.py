from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/summary/weekly", response_model=schemas.report.WeeklySummary)
def read_weekly_summary(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    target_date_str: Optional[str] = Query(None, description="Optional date in YYYY-MM-DD format. Defaults to today."),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve the weekly health summary for the week containing the target_date.
    Defaults to the current week if target_date is not provided.
    """
    target_date = date.today()
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    summary = crud.health_entry.get_weekly_summary(
        db=db, user_id=current_user.id, target_date=target_date
    )
    return summary

@router.get("/trends", response_model=schemas.report.TrendReport)
def read_trends(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    start_date_str: Optional[str] = Query(None, description="Optional start date (YYYY-MM-DD). Defaults to 30 days ago."),
    end_date_str: Optional[str] = Query(None, description="Optional end date (YYYY-MM-DD). Defaults to today."),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve time-series trend data for weight and steps within a date range.
    Defaults to the last 30 days.
    """
    end_date = date.today()
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

    start_date = end_date - timedelta(days=29) # Default to 30 days including end_date
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")

    trends = crud.health_entry.get_trends(
        db=db, user_id=current_user.id, start_date=start_date, end_date=end_date
    )
    return trends 
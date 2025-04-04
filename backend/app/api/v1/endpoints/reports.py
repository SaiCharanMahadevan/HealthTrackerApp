from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional, Any
import logging

from app import crud, models, schemas
from app.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/summary/weekly", response_model=schemas.report.WeeklySummary)
def read_weekly_summary(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    target_date_str: Optional[str] = Query(None, description="Target date (YYYY-MM-DD) within the week. Defaults to today."),
    tz_offset_minutes: int = Query(0, description="Client timezone offset from UTC in minutes (e.g., SGT is -480)"),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    logger.info(f"User {current_user.id} requesting weekly summary for target date: {target_date_str or 'Default (today)'}")
    target_date = date.today()
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            logger.warning(f"Invalid date format received from user {current_user.id}: '{target_date_str}'")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    summary = crud.health_entry.get_weekly_summary(
        db=db, user_id=current_user.id, target_date=target_date, tz_offset_minutes=tz_offset_minutes
    )
    logger.info(f"Returning weekly summary for user {current_user.id}, week: {summary.week_start_date} to {summary.week_end_date}")
    return summary

@router.get("/summary/daily", response_model=schemas.report.DailySummary)
def read_daily_summary(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    target_date_str: Optional[str] = Query(None, description="Target date (YYYY-MM-DD). Defaults to today."),
    tz_offset_minutes: int = Query(0, description="Client timezone offset from UTC in minutes (e.g., SGT is -480)"),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Retrieve the daily health summary for the target_date.
    Defaults to the current day if target_date is not provided.
    """
    logger.info(f"User {current_user.id} requesting daily summary for target date: {target_date_str or 'Default (today)'}")
    target_date = date.today()
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            logger.warning(f"Invalid date format received for daily summary from user {current_user.id}: '{target_date_str}'")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    summary = crud.health_entry.get_daily_summary(
        db=db, user_id=current_user.id, target_date=target_date, tz_offset_minutes=tz_offset_minutes
    )
    # Note: Logging happens within the CRUD function now
    return summary

@router.get("/trends", response_model=schemas.report.TrendReport)
def read_trends(
    *, # Enforce keyword arguments
    db: Session = Depends(deps.get_db),
    start_date_str: Optional[str] = Query(None, description="Optional start date (YYYY-MM-DD). Defaults to 30 days ago."),
    end_date_str: Optional[str] = Query(None, description="Optional end date (YYYY-MM-DD). Defaults to today."),
    tz_offset_minutes: int = Query(0, description="Client timezone offset from UTC in minutes (e.g., SGT is -480)"),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    logger.info(f"User {current_user.id} requesting trends from {start_date_str or 'Default (30 days ago)'} to {end_date_str or 'Default (today)'}")
    end_date = date.today()
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            logger.warning(f"Invalid end_date format received from user {current_user.id}: '{end_date_str}'")
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

    start_date = end_date - timedelta(days=29) # Default to 30 days including end_date
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            logger.warning(f"Invalid start_date format received from user {current_user.id}: '{start_date_str}'")
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    if start_date > end_date:
        logger.warning(f"Invalid date range from user {current_user.id}: start {start_date} > end {end_date}")
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")

    trends = crud.health_entry.get_trends(
        db=db, user_id=current_user.id, start_date=start_date, end_date=end_date, tz_offset_minutes=tz_offset_minutes
    )
    logger.info(f"Returning trends report for user {current_user.id} from {start_date} to {end_date}")
    return trends 
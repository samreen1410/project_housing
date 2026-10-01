"""
Exposes the current TransLink monthly zone plans so the frontend can let
people pick their actual plan instead of only entering a custom number.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TransitFare
from app.schemas import TransitPlanOut

router = APIRouter(prefix="/transit-fares", tags=["transit-fares"])


@router.get("/", response_model=list[TransitPlanOut])
def get_transit_plans(db: Session = Depends(get_db)):
    latest_per_zone = (
        db.query(
            TransitFare.zone_count,
            func.max(TransitFare.effective_date).label("latest_date"),
        )
        .filter(TransitFare.fare_type == "adult")
        .group_by(TransitFare.zone_count)
        .subquery()
    )
    rows = (
        db.query(TransitFare)
        .join(
            latest_per_zone,
            (TransitFare.zone_count == latest_per_zone.c.zone_count)
            & (TransitFare.effective_date == latest_per_zone.c.latest_date),
        )
        .filter(TransitFare.fare_type == "adult")
        .order_by(TransitFare.zone_count)
        .all()
    )
    return [TransitPlanOut(zone_count=r.zone_count, monthly_pass_cost=r.monthly_pass_cost) for r in rows]

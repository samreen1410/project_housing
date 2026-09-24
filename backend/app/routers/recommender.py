"""
Neighbourhood Recommender: instead of checking one city at a time, this
takes a person's budget/situation once and ranks every city that has rent
data against it — highest surplus first. Reuses the exact same estimation
logic as the Calculator (see app/services/estimator.py) so the numbers
are always consistent between the two features.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region, RentData
from app.schemas import RecommendationRequest, RecommendationMatch
from app.services.calculator import calculate_affordability
from app.services.estimator import resolve_groceries, resolve_transportation

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/matches", response_model=list[RecommendationMatch])
def get_matches(request: RecommendationRequest, db: Session = Depends(get_db)):
    notes: list[str] = []  # shared placeholder-data notes, not surfaced per-city here
    monthly_groceries_estimate = resolve_groceries(db, request.custom_groceries, notes)
    monthly_transportation_cost = resolve_transportation(
        db, request.transportation_mode, request.custom_transportation_cost, notes
    )

    matches = []
    regions = db.query(Region).all()

    for region in regions:
        rent_entry = (
            db.query(RentData)
            .filter(
                RentData.region_id == region.id,
                RentData.bedroom_type == request.bedroom_type,
            )
            .order_by(RentData.imported_at.desc())
            .first()
        )
        if rent_entry is None:
            continue  # skip cities with no rent data for this bedroom type

        result = calculate_affordability(
            monthly_income=request.monthly_income,
            avg_rent=rent_entry.avg_rent,
            monthly_groceries_estimate=monthly_groceries_estimate,
            monthly_transportation_cost=monthly_transportation_cost,
            monthly_extra_expenses=request.monthly_extra_expenses,
        )

        matches.append(RecommendationMatch(
            region_id=region.id,
            region_name=region.name,
            estimated_rent=result.estimated_rent,
            estimated_groceries=result.estimated_groceries,
            estimated_transportation=result.estimated_transportation,
            total_monthly_expenses=result.total_monthly_expenses,
            monthly_surplus=result.monthly_surplus,
            is_currently_affordable=result.is_currently_affordable,
        ))

    # Best fit first — highest surplus at the top.
    matches.sort(key=lambda m: m.monthly_surplus, reverse=True)
    return matches

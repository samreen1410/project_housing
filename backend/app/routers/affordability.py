from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region, RentData
from app.schemas import (
    AffordabilityRequest, AffordabilityResponse,
    EstimatePreviewRequest, EstimatePreviewResponse,
)
from app.services.calculator import calculate_affordability
from app.services.estimator import resolve_groceries, resolve_transportation

router = APIRouter(prefix="/affordability", tags=["affordability"])


def _get_rent_entry(db: Session, region_id: int, bedroom_type: str) -> RentData | None:
    return (
        db.query(RentData)
        .filter(RentData.region_id == region_id, RentData.bedroom_type == bedroom_type)
        .order_by(RentData.imported_at.desc())
        .first()
    )


@router.post("/preview", response_model=EstimatePreviewResponse)
def preview(request: EstimatePreviewRequest, db: Session = Depends(get_db)):
    """
    A lightweight, income-free lookup used for live, as-you-type estimates
    on the Calculator — no form submission required. Reuses the exact same
    estimation logic as the real calculation, so the preview numbers are
    always consistent with the final result.
    """
    region = db.query(Region).filter(Region.id == request.region_id).first()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    rent_entry = _get_rent_entry(db, region.id, request.bedroom_type)
    if rent_entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached rent data for {region.name} / {request.bedroom_type}.",
        )

    notes: list[str] = []
    groceries = resolve_groceries(db, request.custom_groceries, notes)
    transportation = resolve_transportation(
        db, request.transportation_mode, request.custom_transportation_cost, notes
    )

    return EstimatePreviewResponse(
        region_name=region.name,
        estimated_rent=rent_entry.avg_rent,
        estimated_groceries=groceries,
        estimated_transportation=transportation,
        groceries_is_estimate=request.custom_groceries is None,
        transportation_is_estimate=request.custom_transportation_cost is None,
    )


@router.post("/calculate", response_model=AffordabilityResponse)
def calculate(request: AffordabilityRequest, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == request.region_id).first()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    rent_entry = _get_rent_entry(db, region.id, request.bedroom_type)
    if rent_entry is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No cached rent data for {region.name} / "
                f"{request.bedroom_type}. Run the CMHC import first."
            ),
        )

    notes: list[str] = []
    monthly_groceries_estimate = resolve_groceries(db, request.custom_groceries, notes)
    monthly_transportation_cost = resolve_transportation(
        db, request.transportation_mode, request.custom_transportation_cost, notes
    )

    result = calculate_affordability(
        monthly_income=request.monthly_income,
        avg_rent=rent_entry.avg_rent,
        monthly_groceries_estimate=monthly_groceries_estimate,
        monthly_transportation_cost=monthly_transportation_cost,
        monthly_extra_expenses=request.monthly_extra_expenses,
        current_savings=request.current_savings,
        savings_goal=request.savings_goal,
    )
    result.notes = notes + result.notes

    return AffordabilityResponse(
        region_name=region.name,
        estimated_rent=result.estimated_rent,
        estimated_groceries=result.estimated_groceries,
        estimated_transportation=result.estimated_transportation,
        transportation_mode=request.transportation_mode,
        groceries_is_estimate=request.custom_groceries is None,
        transportation_is_estimate=request.custom_transportation_cost is None,
        total_monthly_expenses=result.total_monthly_expenses,
        monthly_surplus=result.monthly_surplus,
        months_to_goal=result.months_to_goal,
        is_currently_affordable=result.is_currently_affordable,
        notes=result.notes,
    )

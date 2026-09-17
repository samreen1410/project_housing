from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region, RentData, TransitFare
from app.schemas import AffordabilityRequest, AffordabilityResponse
from app.services.calculator import calculate_affordability

router = APIRouter(prefix="/affordability", tags=["affordability"])


@router.post("/calculate", response_model=AffordabilityResponse)
def calculate(request: AffordabilityRequest, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == request.region_id).first()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

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
        raise HTTPException(
            status_code=404,
            detail=(
                f"No cached rent data for {region.name} / "
                f"{request.bedroom_type}. Run the CMHC import first."
            ),
        )

    # Placeholder until grocery_data has real cached rows wired to a basket.
    monthly_groceries_estimate = 450.0

    transit_fare = (
        db.query(TransitFare)
        .filter(TransitFare.fare_type == "adult")
        .order_by(TransitFare.effective_date.desc())
        .first()
    )
    monthly_transit_cost = transit_fare.monthly_pass_cost if transit_fare else 0.0

    result = calculate_affordability(
        monthly_income=request.monthly_income,
        avg_rent=rent_entry.avg_rent,
        monthly_groceries_estimate=monthly_groceries_estimate,
        monthly_transit_cost=monthly_transit_cost,
        monthly_extra_expenses=request.monthly_extra_expenses,
        current_savings=request.current_savings,
        savings_goal=request.savings_goal,
    )

    return AffordabilityResponse(
        region_name=region.name,
        estimated_rent=result.estimated_rent,
        estimated_groceries=result.estimated_groceries,
        estimated_transit=result.estimated_transit,
        total_monthly_expenses=result.total_monthly_expenses,
        monthly_surplus=result.monthly_surplus,
        months_to_goal=result.months_to_goal,
        is_currently_affordable=result.is_currently_affordable,
        notes=result.notes,
    )

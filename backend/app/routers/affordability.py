from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region, RentData, TransitFare, GroceryData
from app.schemas import AffordabilityRequest, AffordabilityResponse
from app.services.calculator import calculate_affordability, estimate_monthly_groceries

router = APIRouter(prefix="/affordability", tags=["affordability"])


def _get_latest_grocery_prices(db: Session) -> dict[str, float]:
    """
    Returns the most recently fetched price for each grocery item in the
    cache — one row per item_name, not the full history.
    """
    latest_per_item = (
        db.query(
            GroceryData.item_name,
            func.max(GroceryData.fetched_at).label("latest_fetch"),
        )
        .group_by(GroceryData.item_name)
        .subquery()
    )
    rows = (
        db.query(GroceryData)
        .join(
            latest_per_item,
            (GroceryData.item_name == latest_per_item.c.item_name)
            & (GroceryData.fetched_at == latest_per_item.c.latest_fetch),
            )
        .all()
    )
    return {row.item_name: row.avg_price for row in rows}


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

    grocery_prices = _get_latest_grocery_prices(db)
    if grocery_prices:
        monthly_groceries_estimate = estimate_monthly_groceries(grocery_prices)
    else:
        # No cached grocery data yet — fall back to a placeholder so the
        # endpoint still works, but flag it clearly in the response notes.
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

    if not grocery_prices:
        result.notes.append(
            "Grocery estimate is a placeholder — run POST "
            "/admin/refresh-groceries to pull real cached prices."
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
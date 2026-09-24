"""
Shared cost-estimation helpers used by both the Affordability Calculator
and the Neighbourhood Recommender, so the two features can't drift apart
by each having their own copy of this logic.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import TransitFare, CarCost, GroceryData
from app.services.calculator import estimate_monthly_groceries


def get_latest_grocery_prices(db: Session) -> dict[str, float]:
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


def resolve_groceries(
    db: Session, custom_groceries: float | None, notes: list[str]
) -> float:
    if custom_groceries is not None:
        return custom_groceries

    grocery_prices = get_latest_grocery_prices(db)
    if grocery_prices:
        return estimate_monthly_groceries(grocery_prices)

    notes.append(
        "Grocery estimate is a placeholder — run POST "
        "/admin/refresh-groceries to pull real cached prices, or enter "
        "your own grocery spending."
    )
    return 450.0


def resolve_transportation(
    db: Session,
    transportation_mode: str,
    custom_transportation_cost: float | None,
    notes: list[str],
) -> float:
    if custom_transportation_cost is not None:
        return custom_transportation_cost

    if transportation_mode == "none":
        return 0.0

    if transportation_mode == "car":
        car_cost = db.query(CarCost).order_by(CarCost.effective_date.desc()).first()
        if car_cost is None:
            notes.append("No car cost reference found — defaulting to $0. Run seed_data.py.")
            return 0.0
        return car_cost.monthly_cost

    # default: transit
    transit_fare = (
        db.query(TransitFare)
        .filter(TransitFare.fare_type == "adult")
        .order_by(TransitFare.effective_date.desc())
        .first()
    )
    return transit_fare.monthly_pass_cost if transit_fare else 0.0

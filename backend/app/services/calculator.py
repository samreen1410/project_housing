"""
The affordability projection algorithm.

This is deliberately separated from the API layer (routers/) so it's
independently testable and so the "deep" logic isn't buried in request
handling code.

v1 here does a straightforward but real projection: given income, fixed
costs pulled from cached rent/grocery/transit data, and a savings goal,
it computes monthly surplus and a months-to-goal estimate.

Natural next steps to make this genuinely more sophisticated later:
- Compound growth on savings (if she puts surplus into an interest-bearing
  account) instead of flat linear accumulation
- A Monte Carlo simulation that varies rent/grocery inflation slightly
  each month to show a *range* of likely outcomes instead of one number
- Weighted city comparison/ranking across multiple regions
"""
from dataclasses import dataclass, field


@dataclass
class AffordabilityResult:
    estimated_rent: float
    estimated_groceries: float
    estimated_transit: float
    total_monthly_expenses: float
    monthly_surplus: float
    months_to_goal: float | None
    is_currently_affordable: bool
    notes: list[str] = field(default_factory=list)


def calculate_affordability(
        monthly_income: float,
        avg_rent: float,
        monthly_groceries_estimate: float,
        monthly_transit_cost: float,
        monthly_extra_expenses: float = 0.0,
        current_savings: float = 0.0,
        savings_goal: float | None = None,
) -> AffordabilityResult:
    notes = []

    total_expenses = (
            avg_rent + monthly_groceries_estimate + monthly_transit_cost
            + monthly_extra_expenses
    )
    surplus = monthly_income - total_expenses

    is_affordable = surplus >= 0
    if not is_affordable:
        notes.append(
            "Estimated expenses exceed income for this region — this "
            "budget is currently in deficit, not just tight."
        )
    elif surplus < monthly_income * 0.1:
        notes.append(
            "Surplus is under 10% of income — technically affordable but "
            "little room for savings or unexpected costs."
        )

    months_to_goal = None
    if savings_goal is not None:
        remaining = savings_goal - current_savings
        if remaining <= 0:
            months_to_goal = 0.0
        elif surplus <= 0:
            months_to_goal = None
            notes.append(
                "Savings goal is unreachable at current income/expenses — "
                "there's no monthly surplus to save."
            )
        else:
            months_to_goal = remaining / surplus

    return AffordabilityResult(
        estimated_rent=round(avg_rent, 2),
        estimated_groceries=round(monthly_groceries_estimate, 2),
        estimated_transit=round(monthly_transit_cost, 2),
        total_monthly_expenses=round(total_expenses, 2),
        monthly_surplus=round(surplus, 2),
        months_to_goal=round(months_to_goal, 1) if months_to_goal is not None else None,
        is_currently_affordable=is_affordable,
        notes=notes,
    )


def estimate_monthly_groceries(item_prices: dict[str, float]) -> float:
    """
    Turns a basket of cached StatsCan item prices into a rough monthly
    estimate for one person.

    IMPORTANT ASSUMPTION, worth revisiting later: the basket (milk, bread,
    eggs, meat, produce, pantry staples — see GROCERY_ITEM_VECTORS) is
    priced per package/kg, not per day, so there's no exact "how often do
    you buy this" data here. This treats the summed basket as roughly two
    weeks' worth of staples for one person and doubles it for a monthly
    figure. That's a simplification, not a precise model — a more accurate
    version later would weight each item by realistic purchase frequency
    (e.g. milk bought weekly, rice bought monthly).
    """
    if not item_prices:
        return 0.0
    basket_total = sum(item_prices.values())
    return round(basket_total * 2, 2)
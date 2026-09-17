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


def estimate_monthly_groceries(daily_food_items_avg: dict[str, float]) -> float:
    """
    Very rough v1: sums a basket of per-unit grocery prices and scales to a
    monthly estimate. Replace with a proper weighted basket (matching
    StatsCan's CPI basket weights) once you have more items cached —
    right now this is a placeholder pending real cached grocery_data rows.
    """
    # Rough placeholder multiplier — refine once real data is flowing.
    basket_total = sum(daily_food_items_avg.values())
    return basket_total * 4.3  # ~4.3 weeks/month

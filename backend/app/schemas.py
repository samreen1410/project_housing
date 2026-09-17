"""
Pydantic schemas — these define what your API accepts and returns.
Keeping these separate from the SQLAlchemy models (models.py) is intentional:
it lets your API's public shape evolve independently from your DB schema.
"""
from pydantic import BaseModel
from typing import Optional


class RegionOut(BaseModel):
    id: int
    name: str
    province: str
    parent_region_id: Optional[int] = None

    class Config:
        from_attributes = True


class RentDataOut(BaseModel):
    bedroom_type: str
    avg_rent: float
    vacancy_rate: Optional[float] = None
    survey_period: str

    class Config:
        from_attributes = True


class AffordabilityRequest(BaseModel):
    region_id: int
    bedroom_type: str = "1 Bedroom"
    monthly_income: float
    current_savings: float = 0.0
    savings_goal: Optional[float] = None
    monthly_extra_expenses: float = 0.0  # phone, subscriptions, etc.


class AffordabilityResponse(BaseModel):
    region_name: str
    estimated_rent: float
    estimated_groceries: float
    estimated_transit: float
    total_monthly_expenses: float
    monthly_surplus: float
    months_to_goal: Optional[float] = None
    is_currently_affordable: bool
    notes: list[str] = []

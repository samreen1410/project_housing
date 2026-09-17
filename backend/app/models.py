"""
SQLAlchemy ORM models.

Design notes:
- `regions` supports a self-referencing parent (e.g. Burnaby's parent is
  Metro Vancouver) so you can expand geographically without changing the
  schema.
- `rent_data` and `grocery_data` are CACHE tables: they store the last
  known values pulled from CMHC (via CSV import) and StatsCan (via live
  API), each stamped with when it was refreshed. Your calculator always
  reads from these tables, never calls the external sources directly —
  that's the caching layer we discussed.
- `transit_fares` is a static reference table you maintain by hand,
  since TransLink doesn't expose fare pricing through an API.
- `user_scenarios` is for later, once you add auth and "save my budget"
  functionality.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # e.g. "Vancouver"
    province = Column(String, default="BC")
    cmhc_geo_uid = Column(String, nullable=True)  # CMHC's census geo code
    parent_region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)

    parent = relationship("Region", remote_side=[id])
    rent_entries = relationship("RentData", back_populates="region")


class RentData(Base):
    """Cached rent figures, sourced from CMHC CSV exports."""
    __tablename__ = "rent_data"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    bedroom_type = Column(String, nullable=False)  # "Bachelor", "1 Bedroom", etc.
    avg_rent = Column(Float, nullable=False)
    vacancy_rate = Column(Float, nullable=True)
    survey_period = Column(String, nullable=False)  # e.g. "October 2025"
    imported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    region = relationship("Region", back_populates="rent_entries")


class GroceryData(Base):
    """Cached grocery price figures, sourced live from StatsCan WDS API."""
    __tablename__ = "grocery_data"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)  # e.g. "Milk, 2L"
    avg_price = Column(Float, nullable=False)
    reference_month = Column(String, nullable=False)  # e.g. "2026-08"
    province = Column(String, default="BC")  # StatsCan granularity is provincial
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TransitFare(Base):
    """Static reference table — update manually when TransLink changes fares."""
    __tablename__ = "transit_fares"

    id = Column(Integer, primary_key=True, index=True)
    zone_count = Column(Integer, nullable=False)  # 1, 2, or 3
    fare_type = Column(String, nullable=False)  # "adult", "concession"
    single_fare_cost = Column(Float, nullable=False)
    monthly_pass_cost = Column(Float, nullable=False)
    effective_date = Column(String, nullable=False)  # when this fare took effect


class UserScenario(Base):
    """A saved 'what-if' budget scenario. Wire up once auth is added."""
    __tablename__ = "user_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True)  # placeholder until auth exists
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    monthly_income = Column(Float, nullable=False)
    current_savings = Column(Float, default=0.0)
    savings_goal = Column(Float, nullable=True)
    custom_expenses_json = Column(Text, nullable=True)  # flexible extra costs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    region = relationship("Region")

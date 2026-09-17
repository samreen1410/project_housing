"""
Run this once after setting up the database to populate:
- Greater Vancouver regions (city-level, as decided)
- Current TransLink fare table (static — update this manually when
  TransLink changes fares: https://www.translink.ca/transit-fares)

Usage: python seed_data.py
"""
from app.database import SessionLocal, Base, engine
from app.models import Region, TransitFare

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# City-level regions in Metro Vancouver. cmhc_geo_uid left blank —
# fill these in from the CMHC portal when you export your first CSV
# (the portal shows the geo UID for whatever area you select).
REGIONS = [
    "Vancouver", "Burnaby", "Surrey", "Richmond",
    "Coquitlam", "New Westminster", "North Vancouver", "West Vancouver",
]

for name in REGIONS:
    exists = db.query(Region).filter(Region.name == name).first()
    if not exists:
        db.add(Region(name=name, province="BC"))

# NOTE: these fare numbers are placeholders for scaffolding purposes —
# replace with the actual current TransLink fares before relying on them:
# https://www.translink.ca/transit-fares
TRANSIT_FARES = [
    {"zone_count": 1, "fare_type": "adult", "single_fare_cost": 3.15,
     "monthly_pass_cost": 108.00, "effective_date": "2026-01-01"},
    {"zone_count": 2, "fare_type": "adult", "single_fare_cost": 4.55,
     "monthly_pass_cost": 145.00, "effective_date": "2026-01-01"},
    {"zone_count": 3, "fare_type": "adult", "single_fare_cost": 6.20,
     "monthly_pass_cost": 197.00, "effective_date": "2026-01-01"},
]

for fare in TRANSIT_FARES:
    exists = db.query(TransitFare).filter(
        TransitFare.zone_count == fare["zone_count"],
        TransitFare.fare_type == fare["fare_type"],
        TransitFare.effective_date == fare["effective_date"],
    ).first()
    if not exists:
        db.add(TransitFare(**fare))

db.commit()
db.close()
print("Seed complete.")

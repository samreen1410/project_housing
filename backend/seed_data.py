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

# Real current TransLink fares, effective July 1, 2026 (the annual July 1
# fare increase already applied). Source: translink.ca/transit-fares.
# Note: these are Compass Card "stored value" fares, not cash fares —
# stored value is the standard rate most riders actually pay.
TRANSIT_FARES = [
    {"zone_count": 1, "fare_type": "adult", "single_fare_cost": 2.85,
     "monthly_pass_cost": 117.20, "effective_date": "2026-07-01"},
    {"zone_count": 2, "fare_type": "adult", "single_fare_cost": 4.20,
     "monthly_pass_cost": 156.70, "effective_date": "2026-07-01"},
    {"zone_count": 3, "fare_type": "adult", "single_fare_cost": 5.40,
     "monthly_pass_cost": 211.65, "effective_date": "2026-07-01"},
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
"""
Seeds the Greater Vancouver regions and the reference tables:
- Current TransLink fare table (static: update this manually when
  TransLink changes fares: https://www.translink.ca/transit-fares)
- The average monthly cost of owning a car in BC

Safe to run as many times as you like: every insert checks whether the row
already exists first. The backend now calls run_seed() by itself every time
it starts (see app/main.py), because a free hosting plan can wipe the local
database whenever the server restarts.

You can still run it by hand:  python seed_data.py
"""
from app.database import SessionLocal, Base, engine
from app.models import Region, TransitFare, CarCost

# City-level regions in Metro Vancouver. cmhc_geo_uid left blank:
# fill these in from the CMHC portal when you export your first CSV
# (the portal shows the geo UID for whatever area you select).
REGIONS = [
    "Vancouver", "Burnaby", "Surrey", "Richmond",
    "Coquitlam", "New Westminster", "North Vancouver", "West Vancouver",
]

# Real current TransLink fares, effective July 1, 2026 (the annual July 1
# fare increase already applied). Source: translink.ca/transit-fares.
# Note: these are Compass Card "stored value" fares, not cash fares.
# Stored value is the standard rate most riders actually pay.
TRANSIT_FARES = [
    {"zone_count": 1, "fare_type": "adult", "single_fare_cost": 2.85,
     "monthly_pass_cost": 117.20, "effective_date": "2026-07-01"},
    {"zone_count": 2, "fare_type": "adult", "single_fare_cost": 4.20,
     "monthly_pass_cost": 156.70, "effective_date": "2026-07-01"},
    {"zone_count": 3, "fare_type": "adult", "single_fare_cost": 5.40,
     "monthly_pass_cost": 211.65, "effective_date": "2026-07-01"},
]

# Average monthly cost of car ownership in BC (insurance + gas +
# maintenance, blended), from the Canada Car Ownership Index 2026,
# which reported $4,432/year for BC. This does NOT include a car
# payment/loan, since that varies hugely by person; someone financing a
# vehicle should override this with their own number in the calculator.
CAR_COST = {
    "monthly_cost": round(4432 / 12, 2),
    "source_note": "Canada Car Ownership Index 2026 (BC annual avg, excl. loan payments)",
    "effective_date": "2026-01-01",
}


def run_seed(db):
    """Adds anything that is missing. Never creates duplicates."""
    for name in REGIONS:
        exists = db.query(Region).filter(Region.name == name).first()
        if not exists:
            db.add(Region(name=name, province="BC"))

    for fare in TRANSIT_FARES:
        exists = db.query(TransitFare).filter(
            TransitFare.zone_count == fare["zone_count"],
            TransitFare.fare_type == fare["fare_type"],
            TransitFare.effective_date == fare["effective_date"],
            ).first()
        if not exists:
            db.add(TransitFare(**fare))

    exists = db.query(CarCost).filter(
        CarCost.effective_date == CAR_COST["effective_date"]
    ).first()
    if not exists:
        db.add(CarCost(**CAR_COST))

    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    run_seed(db)
    db.close()
    print("Seed complete.")
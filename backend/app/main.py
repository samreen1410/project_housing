import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.models import RentData, GroceryData
from app.routers import regions, affordability, admin, rent, recommender, transit
from app.services import cmhc_import, statcan_client
from seed_data import run_seed

# Creates tables on startup if they don't exist yet. Fine for development;
# once you have real data you care about, switch to Alembic migrations
# instead so schema changes don't risk wiping data.
Base.metadata.create_all(bind=engine)

# The CMHC export that gets loaded automatically when the rent table is empty.
RENT_CSV_FILENAME = "vancouver_average_rent.csv"


def _load_grocery_prices():
    """
    Pulls current grocery prices from StatsCan and stores them. This runs in
    the background (see below) because it makes a dozen web requests, and the
    site should be able to answer visitors while it works.
    """
    db = SessionLocal()
    try:
        for row in statcan_client.refresh_grocery_cache():
            db.add(GroceryData(**row))
        db.commit()
        print("Startup: grocery prices loaded from StatsCan.")
    except Exception as err:
        db.rollback()
        print(f"Startup: could not load grocery prices ({err}). "
              "Estimates use a placeholder until the next restart.")
    finally:
        db.close()


def fill_database_if_needed():
    """
    Runs every time the server starts, and only adds what is missing, so it is
    safe on a database that already has data and on one that is brand new.
    This matters on free hosting, where the database file can be wiped
    whenever the server restarts.
    """
    needs_groceries = False
    db = SessionLocal()
    try:
        run_seed(db)  # cities, TransLink fares, car cost

        if db.query(RentData).count() == 0:
            try:
                count = cmhc_import.import_rent_csv(db, RENT_CSV_FILENAME)
                print(f"Startup: imported {count} rent rows from {RENT_CSV_FILENAME}.")
            except Exception as err:
                db.rollback()
                print(f"Startup: could not import rent data ({err}).")

        needs_groceries = db.query(GroceryData).count() == 0
    except Exception as err:
        db.rollback()
        print(f"Startup: seeding problem ({err}).")
    finally:
        db.close()

    if needs_groceries:
        threading.Thread(target=_load_grocery_prices, daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    fill_database_if_needed()
    yield


app = FastAPI(
    title="Vancouver Affordability API",
    description="Cost-of-living and affordability projections for Greater Vancouver",
    version="0.1.0",
    lifespan=lifespan,
)

# Allows your plain HTML/CSS/JS frontend (running on a different port/origin
# during local dev, or on its own web address once deployed) to call this API.
# "*" is fine here: the data is public, there are no logins or cookies, and
# the admin endpoints are switched off online (see below).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(regions.router)
app.include_router(affordability.router)
app.include_router(rent.router)
app.include_router(recommender.router)
app.include_router(transit.router)

# The admin endpoints (refresh groceries, import a CSV) have no password, so
# they are only switched on when you run the server on your own computer.
# Render sets RENDER=true on its servers, which keeps them off the internet.
if os.getenv("RENDER") != "true":
    app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
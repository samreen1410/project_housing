from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import regions, affordability, admin

# Creates tables on startup if they don't exist yet. Fine for development;
# once you have real data you care about, switch to Alembic migrations
# instead so schema changes don't risk wiping data.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vancouver Affordability API",
    description="Cost-of-living and affordability projections for Greater Vancouver",
    version="0.1.0",
)

# Allows your plain HTML/CSS/JS frontend (running on a different port/origin
# during local dev) to call this API. Tighten allow_origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(regions.router)
app.include_router(affordability.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

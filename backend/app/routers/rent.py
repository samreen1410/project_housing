"""
Endpoints for browsing rent data directly — this is what the Rent Explorer
frontend page calls. Separate from the affordability router, since this is
about looking at rent on its own, with no income/calculation involved.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region, RentData
from app.schemas import RegionRentOut, RentDataOut

router = APIRouter(prefix="/rent-data", tags=["rent-data"])


def _latest_rent_rows_for_region(db: Session, region_id: int) -> list[RentData]:
    """
    Returns the most recently imported rent row for each bedroom type in
    one region (in case a future CMHC import adds a newer survey period
    without replacing the old rows).
    """
    latest_per_bedroom = (
        db.query(
            RentData.bedroom_type,
            func.max(RentData.imported_at).label("latest_import"),
        )
        .filter(RentData.region_id == region_id)
        .group_by(RentData.bedroom_type)
        .subquery()
    )
    return (
        db.query(RentData)
        .join(
            latest_per_bedroom,
            (RentData.bedroom_type == latest_per_bedroom.c.bedroom_type)
            & (RentData.imported_at == latest_per_bedroom.c.latest_import),
        )
        .filter(RentData.region_id == region_id)
        .all()
    )


@router.get("/{region_id}", response_model=RegionRentOut)
def get_rent_for_region(region_id: int, db: Session = Depends(get_db)):
    """Full rent breakdown (all bedroom types) for one city."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if region is None:
        return RegionRentOut(region_id=region_id, region_name="Unknown", rents=[])

    rows = _latest_rent_rows_for_region(db, region_id)
    return RegionRentOut(
        region_id=region.id,
        region_name=region.name,
        rents=[RentDataOut.model_validate(r) for r in rows],
    )


@router.get("/", response_model=list[RegionRentOut])
def get_rent_for_all_regions(db: Session = Depends(get_db)):
    """Rent breakdown for every city — used for cross-city comparisons."""
    regions = db.query(Region).all()
    results = []
    for region in regions:
        rows = _latest_rent_rows_for_region(db, region.id)
        if not rows:
            continue  # skip cities with no rent data imported yet
        results.append(RegionRentOut(
            region_id=region.id,
            region_name=region.name,
            rents=[RentDataOut.model_validate(r) for r in rows],
        ))
    return results

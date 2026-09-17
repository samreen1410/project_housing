from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GroceryData
from app.services import statcan_client, cmhc_import

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/refresh-groceries")
def refresh_groceries(db: Session = Depends(get_db)):
    """
    Pulls fresh grocery prices from the StatsCan WDS API and stores them.
    Requires GROCERY_ITEM_VECTORS in statcan_client.py to be filled in
    with real vector IDs first.
    """
    if not statcan_client.GROCERY_ITEM_VECTORS:
        raise HTTPException(
            status_code=400,
            detail=(
                "No grocery item vectors configured yet. Look up vector IDs "
                "via get_cube_metadata() and add them to "
                "GROCERY_ITEM_VECTORS in statcan_client.py."
            ),
        )
    fresh_data = statcan_client.refresh_grocery_cache()
    for row in fresh_data:
        db.add(GroceryData(**row))
    db.commit()
    return {"imported": len(fresh_data)}


@router.post("/import-rent-csv")
def import_rent(csv_filename: str, db: Session = Depends(get_db)):
    """
    Imports rent data from a CSV you've manually downloaded from the CMHC
    portal into the /data folder. Pass just the filename, e.g.
    'vancouver_rent_fall_2026.csv'.
    """
    try:
        count = cmhc_import.import_rent_csv(db, csv_filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"imported": count}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Region
from app.schemas import RegionOut

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("/", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)):
    return db.query(Region).all()

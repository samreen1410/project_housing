"""
CMHC rent data importer.

CMHC has no documented public API, so this pulls rent data from a CSV you
export yourself from the Housing Market Information Portal:
https://www03.cmhc-schl.gc.ca/hmip-pimh/

ACTUAL export format (confirmed from a real download — "Average Rent by
Bedroom Type by Zone"):

    Row 1: title, e.g. "Vancouver - Average Rent by Bedroom Type by Zone"
    Row 2: survey period, e.g. "October 2025 Row / Apartment"
    Row 3: column headers — each bedroom type spans 2 columns
           (value, reliability-letter): Studio, 1 Bedroom, 2 Bedroom,
           3 Bedroom +, Total
    Rows 4+: one row per ZONE (mostly Vancouver neighborhoods, but other
           Metro Vancouver cities appear as their own single row), until
           a blank line / "Notes" section at the end

Important caveats about this particular export, since it's zone-level
(sub-city) rather than clean one-row-per-city:
- Vancouver's own city-level number is the row literally named "Vancouver"
  near the bottom (the overall total), NOT any of its neighborhood zones
- Burnaby is split into "North Burnaby" / "Southeast Burnaby" here — there
  is no single combined Burnaby row in this export
- There's no "Coquitlam" row — "Tri-Cities" (Coquitlam + Port Coquitlam +
  Port Moody combined) is the closest available proxy
- "North Vancouver" appears as "North Vancouver CY" (city) and
  "North Vancouver DM" (district) — CY is used here
- This export has no vacancy rate column (that's a separate CMHC table)
- "**" in a cell means the data was suppressed for reliability/privacy —
  those are skipped, not treated as zero

ZONE_TO_REGION below maps the exact zone names in the CSV to the
city-level Region names already seeded in the database. If CMHC renames
a zone or you export a different area, update this mapping.
"""
import csv
from pathlib import Path
from sqlalchemy.orm import Session

from app.models import Region, RentData

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

BEDROOM_COLUMNS = [
    ("Studio", 1),
    ("1 Bedroom", 3),
    ("2 Bedroom", 5),
    ("3 Bedroom +", 7),
    ("Total", 9),
]

ZONE_TO_REGION = {
    "Vancouver": "Vancouver",
    "Surrey": "Surrey",
    "Richmond": "Richmond",
    "New Westminster": "New Westminster",
    "West Vancouver": "West Vancouver",
    "North Vancouver CY": "North Vancouver",
    "Tri-Cities": "Coquitlam",  # closest available proxy, see docstring
}

SUPPRESSED_MARKERS = {"**", "", "F"}


def import_rent_csv(db: Session, csv_filename: str) -> int:
    """
    Reads a CMHC "Average Rent by Bedroom Type by Zone" export CSV and
    inserts rows into rent_data for the zones mapped in ZONE_TO_REGION.
    Returns the number of rent_data rows inserted.
    """
    csv_path = DATA_DIR / csv_filename
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Expected CSV at {csv_path} — download it from the CMHC portal "
            f"first (see docstring at top of this file)."
        )

    # CMHC's export isn't plain UTF-8 (it uses Windows-style punctuation
    # like en-dashes), so cp1252 avoids decode errors on those characters.
    with open(csv_path, newline="", encoding="cp1252", errors="replace") as f:
        rows = list(csv.reader(f))

    survey_period = _extract_survey_period(rows)
    imported = 0

    # Data rows start after the title, survey-period, and header rows.
    for row in rows[3:]:
        if not row or not row[0].strip():
            break  # blank line marks the end of the data section
        zone_name = row[0].strip()
        if zone_name.lower().startswith("notes"):
            break
        if zone_name not in ZONE_TO_REGION:
            continue  # a zone we're not mapping to a city-level region

        region_name = ZONE_TO_REGION[zone_name]
        region = db.query(Region).filter(Region.name == region_name).first()
        if region is None:
            region = Region(name=region_name)
            db.add(region)
            db.flush()  # get region.id without a full commit

        for bedroom_type, col_idx in BEDROOM_COLUMNS:
            if col_idx >= len(row):
                continue
            raw_value = row[col_idx].strip()
            if raw_value in SUPPRESSED_MARKERS:
                continue

            avg_rent = _parse_currency(raw_value)
            if avg_rent is None:
                continue

            db.add(RentData(
                region_id=region.id,
                bedroom_type=bedroom_type,
                avg_rent=avg_rent,
                vacancy_rate=None,  # not present in this export
                survey_period=survey_period,
            ))
            imported += 1

    db.commit()
    return imported


def _extract_survey_period(rows: list[list[str]]) -> str:
    """
    Row 2 looks like 'October 2025 Row / Apartment' — we just want
    'October 2025'.
    """
    if len(rows) < 2 or not rows[1]:
        return "Unknown"
    raw = rows[1][0].strip()
    return raw.split(" Row")[0].strip()


def _parse_currency(value: str) -> float | None:
    cleaned = value.replace(",", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
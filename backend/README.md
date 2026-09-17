# Vancouver Affordability API

Backend for the Greater Vancouver cost-of-living / affordability tool.

## Data sources

| Category | Source | Method |
|---|---|---|
| Rent | CMHC Housing Market Information Portal | Manual CSV export → import script (CMHC has no public API) |
| Groceries | StatsCan Web Data Service (WDS) | Live API, documented and free |
| Transit | TransLink published fare schedule | Static table you maintain manually |

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r packages.txt
python seed_data.py           # creates DB + seeds regions/transit fares
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive API docs (FastAPI
generates this automatically — it's a genuinely useful thing to point to
in interviews/portfolio too).

## Getting real rent data in

1. Go to https://www03.cmhc-schl.gc.ca/hmip-pimh/
2. Select a region (start with City of Vancouver), then Rental Market
   Survey → Average Rent by Bedroom Type
3. Export to CSV, save it into `/data`
4. Check the CSV's actual column headers and adjust `CSV_COLUMN_MAP` in
   `app` if they don't match the guessed names
5. Call `POST /admin/import-rent-csv?csv_filename=your_file.csv` (or use
   the /docs page to trigger it)

## Getting real grocery data flowing

1. Look up StatsCan table 18-10-0002-01 metadata to find vector IDs for
   the specific items you want (milk, bread, rice, etc.) for British
   Columbia. `get_cube_metadata("18100002")` in `statcan_client.py` will
   get you the raw metadata to browse.
2. Fill in `GROCERY_ITEM_VECTORS` in `app`
3. Call `POST /admin/refresh-groceries`

## What's still placeholder / needs real numbers

- `GROCERY_ITEM_VECTORS` is empty — needs real StatsCan vector IDs
- `TRANSIT_FARES` in `seed_data.py` has placeholder fare amounts — replace
  with actual current TransLink pricing
- `monthly_groceries_estimate` in `affordability.py` is hardcoded at $450
  until grocery_data has enough real cached items to build a proper basket
  calculation
- `CSV_COLUMN_MAP` in `cmhc_import.py` is a best guess at CMHC's export
  column names — verify against an actual downloaded file

## Project structure

```
app/
├── main.py              # FastAPI app + startup
├── database.py          # DB session/engine setup
├── models.py            # SQLAlchemy tables
├── schemas.py           # Pydantic request/response shapes
├── routers/
│   ├── regions.py       # GET /regions
│   ├── affordability.py # POST /affordability/calculate
│   └── admin.py         # POST /admin/refresh-groceries, /admin/import-rent-csv
└── services/
    ├── statcan_client.py  # StatsCan WDS API calls
    ├── cmhc_import.py     # CMHC CSV import
    └── calculator.py      # Core affordability algorithm
```

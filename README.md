# Metro Vancouver Housing Tool

A full stack web app that helps people figure out the real cost of living in
Metro Vancouver. It pulls real rent, grocery, and transit data into one
place so comparing cities, checking what you can afford, or finding a city
that fits your budget does not depend on outdated listings or guesswork.

**Live site: [samreen1410.github.io/project_housing](https://samreen1410.github.io/project_housing/)**

The backend runs on a free hosting plan that sleeps when nobody is using it,
so the first visit after a quiet spell can take up to a minute to load the
data. A small banner on the page explains the wait.

Built as a personal portfolio project by a UBC Science student who has
lived in Metro Vancouver for about five years and ran into exactly this
problem firsthand.

## What it does

The tool is three connected features, all built on the same underlying
data:

**Rent Explorer**
Browse average rent by city and unit type. Compare one unit type across
every city on a chart or a map, or compare every unit type and every city
at once. Charts support zooming, panning, hovering to highlight matching
rows, and clicking through to related views.

**Affordability Calculator**
Enter your city, unit type, and income, then optionally tell it how you
get around and what you spend on groceries, or let it estimate those from
real data. Shows a live preview as you type, a full cost breakdown, and a
plain language explanation of exactly how the result was calculated.

**Neighbourhood Recommender**
Enter your budget and situation once, and it ranks every city it has data
for by how much of your budget would be left over each month. Click any
city for a full breakdown of why it is or is not a fit.

## Data sources

| Source | Used for | How it is kept current |
|---|---|---|
| [CMHC Rental Market Survey](https://www03.cmhc-schl.gc.ca/hmip-pimh/) | Average rent by city and bedroom type | Downloaded as a CSV and imported by hand roughly every six months, when CMHC releases new survey data |
| [Statistics Canada](https://www.statcan.gc.ca/en/developers/wds) retail price data | Monthly grocery cost estimates for British Columbia | Pulled live from StatsCan's public API and cached |
| [TransLink](https://www.translink.ca/transit-fares) fare schedule | Transit cost estimates by zone | Entered by hand and updated whenever fares change, since TransLink has no public fares API |
| Canada Car Ownership Index | Average car ownership cost estimate | A single reference figure, updated occasionally |

Known limitations worth knowing about:
- Burnaby appears as two separate zones in the CMHC export rather than one
  combined city figure.
- Coquitlam is approximated using the combined Tri Cities figure (Coquitlam,
  Port Coquitlam, and Port Moody together), since CMHC does not report it
  separately.
- The grocery estimate is a basket of common items treated as roughly two
  weeks of shopping for one person and doubled for a monthly figure. It is
  a starting point, not a precise personal budget, which is why the
  Calculator lets you enter your own number instead.
- Vacancy rate data is not currently populated, since the CMHC export in
  use only covers average rent.

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy, SQLite
**Frontend:** Plain HTML, CSS, and JavaScript, no framework. Chart.js for
data visualization, Leaflet for the Rent Explorer's map, and an embedded
Google Map on the home page.

## Project structure

```
backend/
├── app/
│   ├── main.py                  FastAPI app and router registration
│   ├── database.py              Database connection and session setup
│   ├── models.py                SQLAlchemy models
│   ├── schemas.py                Pydantic request and response schemas
│   ├── routers/
│   │   ├── regions.py           City list
│   │   ├── rent.py              Rent data by city
│   │   ├── affordability.py     Calculator logic and live preview
│   │   ├── recommender.py       Neighbourhood ranking logic
│   │   ├── transit.py           Real TransLink zone plans
│   │   └── admin.py             Data refresh and import endpoints
│   └── services/
│       ├── cmhc_import.py       CMHC CSV importer
│       ├── statcan_client.py    StatsCan API client
│       ├── calculator.py        Core affordability math
│       └── estimator.py         Shared cost estimation logic
├── discover_vectors.py          One time helper for finding StatsCan vector IDs
├── seed_data.py                 Seeds cities, transit fares, and car cost reference
├── packages.txt                 Python dependencies
├── data/                        Drop CMHC CSV exports here
└── frontend/
    ├── index.html               Home page
    ├── explorer.html             Rent Explorer
    ├── calculator.html           Affordability Calculator
    ├── recommender.html          Neighbourhood Recommender
    ├── images/                  Photos used in the home page photo reel
    └── shared/                  Shared CSS and JS used by every page
```

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r packages.txt
python seed_data.py           # creates the database and seeds reference data
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`. Interactive API docs are
available at `http://127.0.0.1:8000/docs`.

Then open `frontend/index.html` directly in a browser. No build step or
server is needed for the frontend, since it is plain HTML, CSS, and JS.

### Loading real rent data

CMHC has no public API, so rent data is imported from a CSV you download
yourself:

1. Go to the [CMHC Housing Market Information
   Portal](https://www03.cmhc-schl.gc.ca/hmip-pimh/), select Metro
   Vancouver, and export the Average Rent by Bedroom Type by Zone report
   as a CSV.
2. Save it into `backend/data/`.
3. Call `POST /admin/import-rent-csv?csv_filename=your_file.csv`, either
   through `/docs` or with curl.

### Loading real grocery data

Grocery prices come live from the StatsCan API once a few setup steps are
done:

1. Run `python discover_vectors.py` to find the StatsCan vector IDs for
   the grocery items you want, for British Columbia.
2. Add them to `GROCERY_ITEM_VECTORS` in
   `app/services/statcan_client.py`.
3. Call `POST /admin/refresh-groceries` to pull and cache the real prices.

## Why this exists

Metro Vancouver is not one housing market but several, and the cost of
living can vary a lot from one city to the next. Figuring out what is
actually affordable usually means digging through several different
sources and a lot of guesswork. This project pulls that into one place,
using real public data instead.

## Acknowledgments

Built with the help of Claude (Anthropic), used throughout as a
collaborative coding partner for the backend, the frontend, and the data
pipeline. All of the product decisions, the data sourcing choices, and the
design direction were mine, worked through and refined in conversation
with Claude rather than figured out alone.
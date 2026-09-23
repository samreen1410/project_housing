"""
StatsCan Web Data Service (WDS) client.

This is a REAL, documented, free, no-key-required API:
https://www.statcan.gc.ca/en/developers/wds

IMPORTANT CORRECTION: table 18-10-0002-01 (originally planned) is Canada-
wide only — it does NOT break down by province, so it's no good for a
British-Columbia-specific estimate. The right table is:

    18-10-0245-01 — "Monthly average retail prices for selected products,
    by province" — this one actually has BC-specific numbers.

Three-step process to get a real data point:
1. Call get_cube_metadata("18100245") to see the table's dimensions
   (Geography, Products) and each member's ID — e.g. "British Columbia"
   has some memberId, "Milk, 2 litres" has some other memberId.
2. Build a "coordinate" string from the member IDs (see
   get_series_info_from_cube_pid_coord) to find the vectorId for that
   specific combination (e.g. "milk in BC" as one time series).
3. Use get_data_from_vector_latest_n_periods() with that vectorId to pull
   the actual latest price.

Run discover_vectors.py (in the project root) locally — it has real
internet access, this sandboxed environment does not — to print out the
members and help you find the right IDs before filling in
GROCERY_ITEM_VECTORS below.
"""
import requests
from datetime import datetime, timezone

WDS_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"

GROCERY_TABLE_PRODUCT_ID = "18100245"  # by-province average retail prices


def get_cube_metadata(product_id: str = GROCERY_TABLE_PRODUCT_ID) -> dict:
    """
    Fetch metadata for a StatsCan table (cube), including its dimensions
    and the member IDs needed to build a coordinate.
    """
    url = f"{WDS_BASE_URL}/getCubeMetadata"
    response = requests.post(url, json=[{"productId": product_id}], timeout=15)
    response.raise_for_status()
    return response.json()


def get_series_info_from_cube_pid_coord(
        product_id: str, coordinate: str
) -> dict:
    """
    Given a table (product_id) and a coordinate — a dot-separated string of
    member IDs, one per dimension, in the order getCubeMetadata lists them,
    padded with trailing zeros for unused dimensions (StatsCan coordinates
    always have 10 segments) — returns that series' info, including its
    vectorId.

    Example coordinate for a 2-dimension table (Geography, Products):
    "<geography_member_id>.<product_member_id>.0.0.0.0.0.0.0.0"
    """
    url = f"{WDS_BASE_URL}/getSeriesInfoFromCubePidCoord"
    payload = [{"productId": product_id, "coordinate": coordinate}]
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def get_data_from_vector_latest_n_periods(vector_id: int, n: int = 1) -> dict:
    """
    Fetch the latest N data points for a specific vector.
    A "vector" is StatsCan's ID for one specific time series — e.g.
    "average price of milk, 2L, in British Columbia".
    """
    url = f"{WDS_BASE_URL}/getDataFromVectorsAndLatestNPeriods"
    payload = [{"vectorId": vector_id, "latestN": n}]
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def parse_vector_response(raw_response: dict) -> dict | None:
    """
    Extract the useful fields (value, reference period) from a single
    vector response. Returns None if the response wasn't successful.
    """
    try:
        obj = raw_response[0]["object"]
        latest_point = obj["vectorDataPoint"][-1]
        return {
            "value": latest_point["value"],
            "reference_period": latest_point["refPer"],  # e.g. "2026-08-01"
        }
    except (KeyError, IndexError, TypeError):
        return None


# Real vector IDs for a basic grocery basket in British Columbia,
# found via discover_vectors.py against table 18-10-0245-01.
GROCERY_ITEM_VECTORS = {
    "Milk, 2 litres": 1159447348,
    "White bread, 675 grams": 1353834695,
    "Eggs, 1 dozen": 1159447354,
    "Ground beef, per kilogram": 1159447338,
    "Chicken breasts, per kilogram": 1159447342,
    "Block cheese, 500 grams": 1159447352,
    "Yogurt, 500 grams": 1159447353,
    "Apples, per kilogram": 1159447355,
    "Bananas, per kilogram": 1159447358,
    "White rice, 2 kilograms": 1458870267,
    "Dry or fresh pasta, 500 grams": 1353834696,
    "Cereal, 400 grams": 1353834697,
}


def refresh_grocery_cache() -> list[dict]:
    """
    Pulls the latest value for each configured grocery item vector.
    Call this from a scheduled job (see admin router) to refresh the cache.
    Returns a list of dicts ready to insert into the grocery_data table.
    """
    results = []
    for item_name, vector_id in GROCERY_ITEM_VECTORS.items():
        raw = get_data_from_vector_latest_n_periods(vector_id, n=1)
        parsed = parse_vector_response(raw)
        if parsed:
            results.append({
                "item_name": item_name,
                "avg_price": parsed["value"],
                "reference_month": parsed["reference_period"][:7],  # YYYY-MM
                "province": "BC",
                "fetched_at": datetime.now(timezone.utc),
            })
    return results
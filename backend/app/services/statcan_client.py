"""
StatsCan Web Data Service (WDS) client.

This is a REAL, documented, free, no-key-required API:
https://www.statcan.gc.ca/en/developers/wds

Two-step process to pull a specific data point:
1. You need a "PID" (product/table ID) and "coordinate" (which row/column
   within that table). Table 18-10-0002-01 ("Monthly average retail prices
   for food and other selected products") is the one you want for grocery
   items like milk, bread, rice.
2. Call getCubeMetadata first (once, manually or in a notebook) to find the
   exact coordinate for the items and geography (British Columbia) you
   want. Then hardcode those coordinates here — they don't change.

This client fetches the latest N periods for a given vector once you've
identified it. Run `discover_vector_ids()` interactively first (e.g. in a
Python shell) to find the vector IDs for the specific items you want
before wiring them into refresh_grocery_cache().
"""
import requests
from datetime import datetime, timezone

WDS_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"


def get_cube_metadata(product_id: str) -> dict:
    """
    Fetch metadata for a StatsCan table (cube), including its dimensions
    and the member IDs needed to build a coordinate.
    Example product_id: "18100002" (no dashes) for average retail prices.
    """
    url = f"{WDS_BASE_URL}/getCubeMetadata"
    response = requests.post(url, json=[{"productId": product_id}], timeout=15)
    response.raise_for_status()
    return response.json()


def get_data_from_vector_latest_n_periods(vector_id: int, n: int = 1) -> dict:
    """
    Fetch the latest N data points for a specific vector.
    A "vector" is StatsCan's ID for one specific time series — e.g.
    "average price of milk, 2L, in British Columbia".
    You find vector IDs by browsing the table on statcan.gc.ca or via
    get_cube_metadata() + the coordinate system.
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


# Example vector IDs to look up and fill in once you've found them via
# get_cube_metadata() — these are placeholders, NOT verified real IDs.
GROCERY_ITEM_VECTORS = {
    # "item_name": vector_id,
    # "Milk, 2 litres": 12345678,
    # "White bread, 675g": 12345679,
    # "White rice, 2kg": 12345680,
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

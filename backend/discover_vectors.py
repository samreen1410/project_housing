"""
Run this LOCALLY (not on any server) to find the StatsCan dimension member
IDs and vector IDs for grocery items in British Columbia. This needs real
internet access, so it won't run inside a sandboxed environment — run it
straight in your terminal:

    python discover_vectors.py

What it does, step by step:
1. Prints every "Geography" member and its ID for table 18-10-0245-01
   (you're looking for "British Columbia")
2. Prints every "Products" member and its ID (you're looking for items
   like "Milk, 1 litre", "Bread, white, 675 g", "Eggs, 1 dozen", etc. —
   exact names in the table may differ slightly, that's expected)
3. Once you've noted the two IDs you want, edit WANTED_ITEMS below and
   re-run — it'll print the vectorId for each item, ready to paste into
   GROCERY_ITEM_VECTORS in app/services/statcan_client.py
"""
import sys
from pathlib import Path

# Allows running this script directly without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.statcan_client import (
    GROCERY_TABLE_PRODUCT_ID,
    get_cube_metadata,
    get_series_info_from_cube_pid_coord,
)


def print_dimension_members():
    metadata = get_cube_metadata(GROCERY_TABLE_PRODUCT_ID)
    dimensions = metadata[0]["object"]["dimension"]

    for i, dim in enumerate(dimensions):
        print(f"\n=== Dimension {i}: {dim['dimensionNameEn']} ===")
        for member in dim["member"]:
            print(f"  {member['memberId']:>6}  {member['memberNameEn']}")


# Once you know the Geography memberId for "British Columbia" and the
# Products memberId for each item you want, fill these in as
# (geography_id, product_id) tuples and re-run this script.
WANTED_ITEMS = {
    "Milk, 2 litres": (10, 14),
    "White bread, 675 grams": (10, 56),
    "Eggs, 1 dozen": (10, 20),
    "Ground beef, per kilogram": (10, 4),
    "Chicken breasts, per kilogram": (10, 8),
    "Block cheese, 500 grams": (10, 18),
    "Yogurt, 500 grams": (10, 19),
    "Apples, per kilogram": (10, 21),
    "Bananas, per kilogram": (10, 24),
    "White rice, 2 kilograms": (10, 94),
    "Dry or fresh pasta, 500 grams": (10, 57),
    "Cereal, 400 grams": (10, 58),
}


def print_vector_ids():
    if not WANTED_ITEMS:
        print("\nWANTED_ITEMS is empty — fill it in first using the "
              "member IDs printed above, then re-run this script.")
        return

    print("\n=== Vector IDs (paste these into GROCERY_ITEM_VECTORS) ===")
    for item_name, (geo_id, product_id) in WANTED_ITEMS.items():
        # Coordinates always have 10 dot-separated segments; unused
        # dimensions beyond the ones this table has are just "0".
        coordinate = f"{geo_id}.{product_id}.0.0.0.0.0.0.0.0"
        result = get_series_info_from_cube_pid_coord(
            GROCERY_TABLE_PRODUCT_ID, coordinate
        )
        try:
            vector_id = result[0]["object"]["vectorId"]
            print(f'  "{item_name}": {vector_id},')
        except (KeyError, IndexError, TypeError):
            print(f"  Could not find a vector for {item_name} — "
                  f"double check the member IDs ({geo_id}, {product_id})")


if __name__ == "__main__":
    print("Fetching table dimensions and members...")
    print_dimension_members()
    print_vector_ids()
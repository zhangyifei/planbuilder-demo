import os
from supabase import create_client, Client
from .utils import haversine_distance

# Radius for fetched regions (meters)
FETCH_RADIUS = 3000  # Adjust as needed

# Minimum realistic travel time (in minutes)
MIN_TRAVEL_TIME = 10  # Prevent unrealistic short travel times

# Initialize the Supabase Client using environment variables or your own config
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://YOUR_PROJECT_ID.supabase.co")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "YOUR_SUPABASE_ANON_OR_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def initialize_database():
    """
    Verifies if the 'places' and 'fetched_regions' tables exist in Supabase
    by calling the 'check_table_exists' RPC function.
    Raises an exception if any table is missing.
    """
    missing_tables = []
    for table in ["places", "fetched_regions"]:
        response = supabase.rpc("check_table_exists", {"tablename": table}).execute()

        # Correct way to access response data and errors
        if hasattr(response, "error") and response.error:
            raise Exception(f"Error checking table {table}: {response.error}")

        if hasattr(response, "data") and not response.data:
            missing_tables.append(table)

    if missing_tables:
        raise Exception(f"Missing tables in Supabase: {', '.join(missing_tables)}")

    print("✅ Database initialized successfully. All required tables exist.")


def save_places_to_db(places):
    """
    Saves a list of place dictionaries to the 'places' table in Supabase.
    Uses upsert behavior (i.e., it will insert or update records based on a conflict key).
    """
    if not places:
        return

    response = supabase.table("places").upsert(places, on_conflict="place_id").execute()

    if hasattr(response, "error") and response.error:
        raise Exception(f"Error upserting places: {response.error.message}")


def save_fetched_region(center_lat, center_lng, radius):
    """
    Saves a fetched region to the 'fetched_regions' table in Supabase.
    """
    data = {
        "center_lat": center_lat,
        "center_lng": center_lng,
        "radius": radius
    }

    response = supabase.table("fetched_regions").insert(data).execute()

    if hasattr(response, "error") and response.error:
        raise Exception(f"Error inserting fetched region: {response.error.message}")


def is_location_fetched(center_lat, center_lng, radius):
    """
    Checks if the current location is within any of the fetched regions in Supabase.
    Returns True if within the radius of any fetched region, False otherwise.
    """
    response = supabase.table("fetched_regions").select("*").execute()
    
    if hasattr(response, "error") and response.error:
        raise Exception(f"Error fetching regions: {response.error.message}")

    regions = response.data if response.data else []

    for region in regions:
        region_lat = region["center_lat"]
        region_lng = region["center_lng"]
        region_radius = region["radius"]

        distance = haversine_distance(center_lat, center_lng, region_lat, region_lng) * 1000  # km to meters
        if distance <= (radius + region_radius):
            return True
    return False


def load_places_from_db():
    """
    Loads all places from the 'places' table in Supabase.
    Returns a list of place dictionaries.
    """
    response = supabase.table("places").select("place_id, name, lat, lng, rating, price_level, category").execute()

    if hasattr(response, "error") and response.error:
        raise Exception(f"Error fetching places: {response.error.message}")

    return response.data if response.data else []
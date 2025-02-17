from datetime import datetime
import googlemaps
from .config import GOOGLE_API_KEY
from .database import initialize_database, is_location_fetched, load_places_from_db, save_fetched_region, save_places_to_db
from .utils import build_itinerary_json, build_itinerary_timeline, haversine_distance
from .planning import categorize_place, count_mealtimes_in_window, filter_and_prepare_places, filter_places_by_travel_time, greedy_itinerary_planner

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def fetch_places_nearby(location, query, radius):
    try:
        result = gmaps.places_nearby(
            location=location,
            radius=radius,
            keyword=query,
            open_now=False
        )
        return result.get("results", [])
    except Exception as e:
        print(f"Error fetching places: {e}")
        return []

def fetch_activities(location, radius=3000):
    """
    Fetch multiple categories: tourist attractions, restaurants, movie theaters.
    Merge them into a unique list (deduplicating by place_id).
    Utilizes the database to avoid redundant API calls.
    """
    categories = ["tourist attractions", "restaurants", "movie theater"]
    all_places = []
    
    # Check if the current location has already been fetched
    if is_location_fetched(location[0], location[1], radius):
        print("Using cached data from the database.")
        # Load existing places from DB that are within the radius
        combined_places = load_places_from_db()
        # Filter places within the radius
        combined_places = [
            p for p in combined_places
            if haversine_distance(location[0], location[1], p["lat"], p["lng"]) * 1000 <= radius
        ]
        return combined_places
    else:
        print("Fetching new data from Google Places API.")
        
        for cat in categories:
            fetched_places = fetch_places_nearby(location, cat, radius=radius)
            all_places.extend(fetched_places)
        
        if not all_places:
            print("No places found for the given categories and location.")
            return []
        
        # Deduplicate by place_id
        unique_places = {p["place_id"]: p for p in all_places}.values()
        unique_places = list(unique_places)
        
        # Categorize new places
        categorized_places = []
        for p in unique_places:
            p["category"] = categorize_place(p)
            categorized_places.append({
                "place_id": p["place_id"],
                "name": p["name"],
                "lat": p["geometry"]["location"]["lat"],
                "lng": p["geometry"]["location"]["lng"],
                "rating": p.get("rating"),
                "price_level": p.get("price_level"),
                "category": p["category"]
            })
        
        # Save new places to DB
        if categorized_places:
            save_places_to_db(categorized_places)
            # Save fetched region
            save_fetched_region(location[0], location[1], radius)
        
        return categorized_places

def generate_plan(request_data):
    # Extract input parameters
    location = tuple(request_data.get("location", [40.7128, -74.0060]))  # Default: NYC
    hotel_location = tuple(request_data.get("hotel_location", [40.7130, -74.0100]))
    budget = request_data.get("budget", 500)
    start_time_str = request_data.get("start_time", "2025-01-08 14:00")
    end_time_str = request_data.get("end_time", "2025-01-08 19:00")
    visited_locations = set(request_data.get("visited_locations", []))
    planned_locations = set(request_data.get("planned_locations", []))
    radius = request_data.get("radius", 3000)
    max_travel_time = request_data.get("max_travel_time", 60)
    # Convert datetime strings
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
    # Fetch and filter places
    combined_places = fetch_activities(location, radius)
    candidate_places = filter_and_prepare_places(
        combined_places, visited_locations, planned_locations, budget, location, radius
    )
    candidate_places = filter_places_by_travel_time(candidate_places, location, max_travel_time)
    if not candidate_places:
        return {"message": "No candidate places found within filters."}
    # Count mealtime slots
    mealtime_slots = count_mealtimes_in_window(start_time, end_time, {
        "lunch": (datetime.strptime("12:00", "%H:%M"), datetime.strptime("14:00", "%H:%M")),
        "dinner": (datetime.strptime("18:00", "%H:%M"), datetime.strptime("21:00", "%H:%M"))
    })
    # Generate itinerary
    itinerary = greedy_itinerary_planner(
        candidate_places, hotel_location, start_time, end_time, budget, mealtime_slots
    )

    build_itinerary_timeline(itinerary)
    # Convert to JSON
    itinerary_json = build_itinerary_json(itinerary)
    return itinerary_json

if __name__ == "__main__":
    initialize_database()
    generate_plan({})

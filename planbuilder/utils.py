import json
import math
from .config import AVERAGE_SPEED_KMH, MIN_TRAVEL_TIME

def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def approximate_travel_time_min(origin, destination, speed_kmh=AVERAGE_SPEED_KMH):
    """
    Approximate transit time (in minutes) by computing haversine distance (km)
    and dividing by speed (km/h). Ensures a minimum transit time.
    """
    lat1, lng1 = origin
    lat2, lng2 = destination
    dist_km = haversine_distance(lat1, lng1, lat2, lng2)
    # time in hours = dist_km / speed_kmh
    time_hours = dist_km / speed_kmh
    return max(time_hours * 60.0, MIN_TRAVEL_TIME)  # ensure minimum transit time

def build_itinerary_timeline(itinerary):
    """
    Formats and prints the itinerary timeline.
    
    Args:
        itinerary (list): List of itinerary entries.
    """
    print("\nGenerated Itinerary:")
    for entry in itinerary:
        duration = (entry["end"] - entry["start"]).total_seconds() / 60
        if entry["type"] == "transit":
            print(f"  Transit from {entry['from_place']} to {entry['to_place']} "
                  f"{entry['start'].strftime('%H:%M')} - {entry['end'].strftime('%H:%M')} "
                  f"({int(duration)} min)")
        elif entry["type"] == "activity":
            if entry["meal"]:
                print(f"  {entry['meal'].capitalize()} at {entry['place']} "
                      f"{entry['start'].strftime('%H:%M')} - {entry['end'].strftime('%H:%M')} "
                      f"({int(duration)} min)")
            else:
                print(f"  Activity at {entry['place']} "
                      f"{entry['start'].strftime('%H:%M')} - {entry['end'].strftime('%H:%M')} "
                      f"({int(duration)} min)")
    print("------------------------------------------------------------")

def build_itinerary_json(itinerary, itinerary_name="Itinerary_Trip", day=1):
    """
    Converts the itinerary into a JSON-formatted list of dictionaries.
    
    Args:
        itinerary (list): List of itinerary entries.
        itinerary_name (str): Name of the itinerary.

    Returns:
        str: JSON string representing the itinerary.
    """
    json_itinerary = []
    for entry in itinerary:
        activity_desc = ""
        activity = ""
        cuisine = ""
        location = ""
        avg_cost_per_person = entry.get("cost_estimate", 0)
        time = entry["start"].strftime("%I:%M %p").lstrip("0")

        if entry["type"] == "transit":
            location = f"transit from {entry['from_place']} to {entry['to_place']}"
            activity = "transit"
            activity_desc = f"transit from {entry['from_place']} to {entry['to_place']}."
        elif entry["type"] == "activity":
            location = entry["place"]
            activity = "Meal" if entry["meal"] else "Activity"
            if entry["meal"]:
                activity_desc = f"Enjoy a {entry['meal']} at {location}."
                cuisine = entry["meal"].capitalize()
            else:
                activity_desc = f"Participate in an activity at {location}."

        json_itinerary.append({
            "itinerary_name": itinerary_name,
            "day": day,
            "time": time,
            "location": location,
            "activity": activity,
            "activity_desc": activity_desc,
            "cuisine": cuisine,
            "avg_cost_per_person": avg_cost_per_person
        })

        # Increment day if entry spans multiple days (optional; based on time management logic)
        # This logic assumes a simple day-based increment, which can be adjusted as needed
        if entry["start"].date() != entry["end"].date():
            day += 1

    return json.dumps(json_itinerary, indent=4)
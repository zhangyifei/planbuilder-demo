from datetime import datetime, timedelta
from .utils import haversine_distance, approximate_travel_time_min
from .config import MIN_TRAVEL_TIME, ACTIVITY_DURATION

def is_place_visited(place_name, visited):
    return place_name.lower() in (v.lower() for v in visited)

def is_place_planned(place_name, planned):
    return place_name.lower() in (p.lower() for p in planned)

def estimate_cost_from_price_level(price_level):
    """
    Approximate cost based on Google's price_level (0–4).
    """
    if price_level is None:
        return 20
    cost_map = {0: 0, 1: 10, 2: 30, 3: 60, 4: 100}
    return cost_map.get(price_level, 20)

def filter_and_prepare_places(places, visited, planned, available_budget, location, radius):
    """
    Filter out places visited or planned, ensure cost is within budget,
    categorize them, and extract relevant info.
    """
    results = []
    for p in places:
        name = p.get("name")
        place_id = p.get("place_id")
        lat = p.get("lat")
        lng = p.get("lng")
        rating = p.get("rating", 0)
        price_level = p.get("price_level")
        category = p.get("category")
        
        if not name or not lat or not lng:
            continue
        
        if is_place_visited(name, visited) or is_place_planned(name, planned):
            continue
        cost_estimate = estimate_cost_from_price_level(price_level)
        if cost_estimate > available_budget:
            continue
        
        # Ensure the place is within the radius
        distance = haversine_distance(location[0], location[1], lat, lng) * 1000  # km to meters
        if distance > radius:
            continue
        
        results.append({
            "name": name,
            "place_id": place_id,
            "lat": lat,
            "lng": lng,
            "rating": rating,
            "cost_estimate": cost_estimate,
            "category": category,  # 'restaurant' or 'other'
        })
    
    return results

def filter_places_by_travel_time(places, location, max_travel_time=60):
    """
    Filters out places that require more than max_travel_time minutes to reach from the current location.
    
    Args:
        places (list): List of place dictionaries.
        location (tuple): Current (lat, lng) location.
        max_travel_time (int): Maximum allowable travel time in minutes.
    
    Returns:
        list: Filtered list of places.
    """
    filtered = []
    for p in places:
        travel_time = approximate_travel_time_min(location, (p["lat"], p["lng"]))
        if travel_time >= MIN_TRAVEL_TIME and travel_time <= max_travel_time:
            p["travel_time"] = travel_time
            filtered.append(p)
    return filtered

def categorize_place(place):
    """
    Categorize the place based on its types or the keyword used to fetch it.
    Returns 'restaurant' or 'other'.
    """
    types = place.get("types", [])
    if "restaurant" in types or "food" in types:
        return "restaurant"
    return "other"
# ----------------------------------------------------------------
# 5. Count Mealtimes in Window
# ----------------------------------------------------------------

def count_mealtimes_in_window(start_dt, end_dt, meal_times):
    """
    Returns a list of mealtime slots that overlap with the user's time window.
    
    Args:
        start_dt (datetime): Start of the itinerary.
        end_dt (datetime): End of the itinerary.
        meal_times (dict): Dictionary of mealtime slots with their start and end times.
    
    Returns:
        list: List of mealtime slot dictionaries with meal name, start, and end times.
    """
    valid_meals = []
    for meal, (meal_start, meal_end) in meal_times.items():
        # Adjust meal_start and meal_end to the date of start_dt
        meal_start_dt = start_dt.replace(hour=meal_start.hour, minute=meal_start.minute, second=0, microsecond=0)
        meal_end_dt = start_dt.replace(hour=meal_end.hour, minute=meal_end.minute, second=0, microsecond=0)
        
        # Handle cases where meal_end might be past midnight
        if meal_end_dt < meal_start_dt:
            meal_end_dt += timedelta(days=1)
        
        # Check if the meal time overlaps with the time window
        if meal_start_dt < end_dt and meal_end_dt > start_dt:
            valid_meals.append({
                "meal": meal,
                "start": max(meal_start_dt, start_dt),
                "end": min(meal_end_dt, end_dt)
            })
    return valid_meals

# ----------------------------------------------------------------
# 6. Greedy Heuristic Algorithm for Itinerary Planning
# ----------------------------------------------------------------

def greedy_itinerary_planner(places, hotel_loc, start_dt, end_dt, budget, mealtime_slots):
    """
    Plans an itinerary using an enhanced Greedy Heuristic Algorithm with time segmentation.

    Args:
        places (list): List of candidate places.
        hotel_loc (tuple): (lat, lng) of the hotel.
        start_dt (datetime): Start datetime of the itinerary.
        end_dt (datetime): End datetime of the itinerary.
        budget (int): Available budget.
        mealtime_slots (list): List of mealtime slots with their time windows.

    Returns:
        list: A list of itinerary entries with detailed information.
    """
    itinerary = []
    current_time = start_dt
    current_location = hotel_loc
    remaining_budget = budget
    last_place_name = "Hotel"  # Initialize the last place as Hotel

    # Sort mealtime slots by their start time
    mealtime_slots = sorted(mealtime_slots, key=lambda x: x["start"])

    for meal_slot in mealtime_slots:
        meal = meal_slot["meal"]
        meal_start = meal_slot["start"]
        meal_end = meal_slot["end"]

        # Calculate available time before the meal
        available_time_before_meal = (meal_start - current_time).total_seconds() / 60.0  # in minutes

        # Schedule as many activities as possible before the meal
        while available_time_before_meal >= (ACTIVITY_DURATION + MIN_TRAVEL_TIME):
            # Select the highest-rated feasible activity
            feasible_activities = [
                p for p in places
                if p["category"] != "restaurant" and
                   p["cost_estimate"] <= remaining_budget and
                   approximate_travel_time_min(current_location, (p["lat"], p["lng"])) + ACTIVITY_DURATION <= available_time_before_meal
            ]
            if not feasible_activities:
                break
            # Sort by rating descending
            feasible_activities.sort(key=lambda x: x["rating"], reverse=True)
            selected_activity = feasible_activities[0]

            # Calculate travel time
            travel_time = approximate_travel_time_min(current_location, (selected_activity["lat"], selected_activity["lng"]))
            travel_end_time = current_time + timedelta(minutes=travel_time)

            # Check if there's enough time to perform the activity
            if (travel_end_time + timedelta(minutes=ACTIVITY_DURATION)) > meal_start:
                break  # Not enough time for this activity

            # Add travel to activity
            itinerary.append({
                "type": "transit",
                "from_place": last_place_name,
                "to_place": selected_activity["name"],
                "start": current_time,
                "end": travel_end_time,
                "cost_estimate": 0  # No cost for travel
            })

            # Add activity
            activity_end_time = travel_end_time + timedelta(minutes=ACTIVITY_DURATION)
            itinerary.append({
                "type": "activity",
                "place": selected_activity["name"],
                "meal": None,
                "start": travel_end_time,
                "end": activity_end_time,
                "cost_estimate": selected_activity["cost_estimate"]
            })

            # Update current location, time, budget, and last_place_name
            current_location = (selected_activity["lat"], selected_activity["lng"])
            current_time = activity_end_time
            remaining_budget -= selected_activity["cost_estimate"]
            last_place_name = selected_activity["name"]

            # Remove the selected activity from places
            places.remove(selected_activity)

            # Update available time before meal
            available_time_before_meal = (meal_start - current_time).total_seconds() / 60.0

        # Schedule the meal
        # Select the highest-rated restaurant within the meal time
        feasible_restaurants = [
            p for p in places
            if p["category"] == "restaurant" and
               p["cost_estimate"] <= remaining_budget and
               approximate_travel_time_min(current_location, (p["lat"], p["lng"])) + ACTIVITY_DURATION <= (meal_end - current_time).total_seconds() / 60.0
        ]
        if feasible_restaurants:
            # Sort by rating descending
            feasible_restaurants.sort(key=lambda x: x["rating"], reverse=True)
            selected_restaurant = feasible_restaurants[0]

            # Calculate travel time
            travel_time = approximate_travel_time_min(current_location, (selected_restaurant["lat"], selected_restaurant["lng"]))
            travel_end_time = current_time + timedelta(minutes=travel_time)

            # Ensure arrival before meal_start
            if travel_end_time > meal_start:
                print(f"Warning: Cannot reach {selected_restaurant['name']} before {meal.capitalize()}. Skipping this meal.")
                continue  # Skip this meal slot

            # Adjust current_time to meal_start if travel ends earlier
            if travel_end_time < meal_start:
                idle_duration = meal_start - travel_end_time
                idle_minutes = idle_duration.total_seconds() / 60.0  # Idle time in minutes
                # Look for short activities that can fit into idle time
                short_activities = [
                    p for p in places
                    if p["category"] != "restaurant"
                    and p["cost_estimate"] <= remaining_budget
                    and approximate_travel_time_min(current_location, (p["lat"], p["lng"])) + ACTIVITY_DURATION <= idle_minutes
                ]               
                if short_activities and len(short_activities)>0:
                    # Sort by rating to prioritize the best options
                    short_activities.sort(key=lambda x: x["rating"], reverse=True)
                    selected_short_activity = short_activities[0]

                    # Calculate travel time
                    travel_time = approximate_travel_time_min(current_location, (selected_short_activity["lat"], selected_short_activity["lng"]))
                    travel_end_time = current_time + timedelta(minutes=travel_time)

                    # Schedule short activity
                    activity_end_time = travel_end_time + timedelta(minutes=ACTIVITY_DURATION)
                    itinerary.append({
                        "type": "transit",
                        "from_place": last_place_name,
                        "to_place": selected_short_activity["name"],
                        "start": current_time,
                        "end": travel_end_time,
                        "cost_estimate": 0
                    })
                    itinerary.append({
                        "type": "activity",
                        "place": selected_short_activity["name"],
                        "meal": None,
                        "start": travel_end_time,
                        "end": activity_end_time,
                        "cost_estimate": short_activities["cost_estimate"]
                    })

                    # Update current location, time, budget, and last_place_name
                    current_location = (selected_short_activity["lat"], selected_short_activity["lng"])
                    current_time = activity_end_time
                    remaining_budget -= selected_short_activity["cost_estimate"]
                    last_place_name = selected_short_activity["name"]

                    # Remove the selected activity from places
                    places.remove(selected_short_activity)

                else:                    
                    current_time = meal_start
            else:
                current_time = travel_end_time

            # Add travel to restaurant
            itinerary.append({
                "type": "transit",
                "from_place": last_place_name,
                "to_place": selected_restaurant["name"],
                "start": current_time,
                "end": travel_end_time,
                "cost_estimate": 0  # No cost for travel
            })

            # Add meal activity
            activity_end_time = current_time + timedelta(minutes=ACTIVITY_DURATION)
            if activity_end_time > meal_end:
                activity_end_time = meal_end  # Adjust to meal end time

            itinerary.append({
                "type": "activity",
                "place": selected_restaurant["name"],
                "meal": meal,
                "start": current_time,
                "end": activity_end_time,
                "cost_estimate": selected_restaurant["cost_estimate"]
            })

            # Update current location, time, budget, and last_place_name
            current_location = (selected_restaurant["lat"], selected_restaurant["lng"])
            current_time = activity_end_time
            remaining_budget -= selected_restaurant["cost_estimate"]
            last_place_name = selected_restaurant["name"]

            # Remove the selected restaurant from places
            places.remove(selected_restaurant)
        else:
            print(f"Warning: No feasible restaurants available for {meal.capitalize()} within constraints.")

    # After scheduling all meals, fill the remaining time with activities
    while (end_dt - current_time).total_seconds() / 60.0 >= (ACTIVITY_DURATION + MIN_TRAVEL_TIME) and places:
        # Select the highest-rated feasible activity
        feasible_activities = [
            p for p in places
            if p["category"] != "restaurant" and
               p["cost_estimate"] <= remaining_budget and
               approximate_travel_time_min(current_location, (p["lat"], p["lng"])) + ACTIVITY_DURATION <= (end_dt - current_time).total_seconds() / 60.0
        ]
        if not feasible_activities:
            break
        # Sort by rating descending
        feasible_activities.sort(key=lambda x: x["rating"], reverse=True)
        selected_activity = feasible_activities[0]

        # Calculate travel time
        travel_time = approximate_travel_time_min(current_location, (selected_activity["lat"], selected_activity["lng"]))
        travel_end_time = current_time + timedelta(minutes=travel_time)

        # Check if there's enough time to perform the activity
        if (travel_end_time + timedelta(minutes=ACTIVITY_DURATION)) > end_dt:
            break  # Not enough time for this activity

        # Add travel to activity
        itinerary.append({
            "type": "transit",
            "from_place": last_place_name,
            "to_place": selected_activity["name"],
            "start": current_time,
            "end": travel_end_time,
            "cost_estimate": 0  # No cost for travel
        })

        # Add activity
        activity_end_time = travel_end_time + timedelta(minutes=ACTIVITY_DURATION)
        itinerary.append({
            "type": "activity",
            "place": selected_activity["name"],
            "meal": None,
            "start": travel_end_time,
            "end": activity_end_time,
            "cost_estimate": selected_activity["cost_estimate"]
        })

        # Update current location, time, budget, and last_place_name
        current_location = (selected_activity["lat"], selected_activity["lng"])
        current_time = activity_end_time
        remaining_budget -= selected_activity["cost_estimate"]
        last_place_name = selected_activity["name"]

        # Remove the selected activity from places
        places.remove(selected_activity)

    # Add travel back to hotel if not already there
    if current_location != hotel_loc:
        travel_time = approximate_travel_time_min(current_location, hotel_loc)
        travel_end_time = current_time + timedelta(minutes=travel_time)
        if travel_end_time <= end_dt:
            itinerary.append({
                "type": "transit",
                "from_place": last_place_name,
                "to_place": "Hotel",
                "start": current_time,
                "end": travel_end_time,
                "cost_estimate": 0  # No cost for travel
            })
            current_time = travel_end_time
            last_place_name = "Hotel"
        else:
            print("Warning: Not enough time to return to the hotel before the end time.")

    return itinerary

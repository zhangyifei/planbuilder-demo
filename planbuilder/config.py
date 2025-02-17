import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "placeholder")
FETCH_RADIUS = 3000
MIN_TRAVEL_TIME = 10
AVERAGE_SPEED_KMH = 30.0
ACTIVITY_DURATION = 60
MEAL_TIMES = {
    "lunch": ("12:00", "14:00"),
    "dinner": ("18:00", "21:00"),
}

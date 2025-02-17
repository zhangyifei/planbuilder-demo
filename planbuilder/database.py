import sqlite3
from .utils import haversine_distance

# Database file path
DB_FILE = "places.db"

# Radius for fetched regions (meters)
FETCH_RADIUS = 3000  # Adjust as needed

# Minimum realistic travel time (in minutes)
MIN_TRAVEL_TIME = 10  # Prevent unrealistic short travel times

# ----------------------------------------------------------------
# 2. Database Setup
# ----------------------------------------------------------------

def initialize_database(db_path=DB_FILE):
    """
    Initializes the SQLite database. Creates the 'places' and 'fetched_regions' tables if they don't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create 'places' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            place_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            rating REAL,
            price_level INTEGER,
            category TEXT,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create 'fetched_regions' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fetched_regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_lat REAL NOT NULL,
            center_lng REAL NOT NULL,
            radius INTEGER NOT NULL,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_places_to_db(places, db_path=DB_FILE):
    """
    Saves a list of place dictionaries to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for place in places:
        cursor.execute('''
            INSERT OR REPLACE INTO places (place_id, name, lat, lng, rating, price_level, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            place["place_id"],
            place["name"],
            place["lat"],
            place["lng"],
            place.get("rating"),
            place.get("price_level"),
            place.get("category")
        ))
    conn.commit()
    conn.close()

def save_fetched_region(center_lat, center_lng, radius, db_path=DB_FILE):
    """
    Saves a fetched region to the 'fetched_regions' table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fetched_regions (center_lat, center_lng, radius)
        VALUES (?, ?, ?)
    ''', (center_lat, center_lng, radius))
    conn.commit()
    conn.close()

def is_location_fetched(center_lat, center_lng, radius, db_path=DB_FILE):
    """
    Checks if the current location is within any of the fetched regions.
    Returns True if fetched, False otherwise.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT center_lat, center_lng, radius FROM fetched_regions')
    regions = cursor.fetchall()
    conn.close()
    for region in regions:
        region_lat, region_lng, region_radius = region
        distance = haversine_distance(center_lat, center_lng, region_lat, region_lng) * 1000  # km to meters
        if distance <= (radius + region_radius):
            return True
    return False

def load_places_from_db(db_path=DB_FILE):
    """
    Loads all places from the SQLite database.
    Returns a list of place dictionaries.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT place_id, name, lat, lng, rating, price_level, category FROM places')
    rows = cursor.fetchall()
    conn.close()
    places = []
    for row in rows:
        places.append({
            "place_id": row[0],
            "name": row[1],
            "lat": row[2],
            "lng": row[3],
            "rating": row[4],
            "price_level": row[5],
            "category": row[6]
        })
    return places
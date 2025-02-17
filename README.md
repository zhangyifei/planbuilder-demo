# planbuilder-demo
Api for planbuilder

# API Documentation

## 1. `POST /api/fetch_places_nearby`

Fetches places near a given geographic location, optionally filtered by a query (keyword) and limited to a specified radius. Internally, this function calls the Google Places API with the provided parameters.

### Request Body

| Field     | Type      | Required | Description |
|-----------|-----------|----------|-------------|
| `location`| `[float, float]` | Yes      | A two-element list representing `[latitude, longitude]` of the central point to search around. |
| `query`   | `string`  | No       | A keyword or category to filter the results (e.g. "restaurants", "tourist attractions"). |
| `radius`  | `integer` | No       | The search radius in meters (e.g., `3000` for 3 km). Defaults to `3000` if not specified. |

#### Example Request

```json
POST /api/fetch_places_nearby
Content-Type: application/json

{
  "location": [40.7128, -74.0060],
  "query": "coffee shops",
  "radius": 1000
}
```

### Response

Returns an array of place objects. Each place object includes:

| Field        | Type     | Description |
|--------------|----------|-------------|
| `place_id`   | `string` | Unique identifier provided by the Google Places API. |
| `name`       | `string` | Name of the place. |
| `geometry`   | `object` | Contains `location` with `lat` and `lng`. |
| `rating`     | `float`  | Average rating of the place (if available). |
| `price_level`| `integer`| Price level of the place (if available, range 1–4). |

#### Example Response

```json
[
  {
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "name": "Starbucks",
    "geometry": {
      "location": {
        "lat": 40.712976,
        "lng": -74.006162
      }
    },
    "rating": 4.2,
    "price_level": 2
  }
]
```

### Error Handling

- If an error occurs, returns `{ "message": "Error fetching places" }` with an appropriate HTTP status code.

---

## 2. `POST /api/fetch_activities`

Fetches places for multiple categories ("tourist attractions", "restaurants", "movie theater"), merges them, categorizes each place, and stores them in a local database (if not already cached).

### Request Body

| Field       | Type             | Required | Description |
|-------------|------------------|----------|-------------|
| `location`  | `[float, float]` | Yes      | A two-element list representing `[latitude, longitude]`. |
| `radius`    | `integer`        | No       | The search radius in meters (default `3000`). |

### Response

Returns an array of place objects, including:

| Field         | Type      | Description |
|---------------|-----------|-------------|
| `place_id`    | `string`  | Unique identifier. |
| `name`        | `string`  | Name of the place. |
| `lat`         | `float`   | Latitude. |
| `lng`         | `float`   | Longitude. |
| `rating`      | `float`   | Average rating. |
| `price_level` | `integer` | Price level (if available). |
| `category`    | `string`  | Categorized type (e.g., "restaurant", "attraction"). |

#### Example Request

```json
POST /api/fetch_activities
Content-Type: application/json

{
  "location": [40.7128, -74.0060],
  "radius": 3000
}
```

#### Example Response

```json
[
  {
    "place_id": "ChIJAT1t_tDeuEmsRUsoyG83frY4",
    "name": "Statue of Liberty",
    "lat": 40.689249,
    "lng": -74.044500,
    "rating": 4.7,
    "category": "attraction"
  }
]
```

### Error Handling

- If an error occurs, returns `{ "message": "No places found" }`.

---

## 3. `POST /api/generate_plan`

Generates a travel plan based on user-provided details including start/end times, budget, hotel location, visited and planned locations, and max travel time.

### Request Body

| Field                | Type                   | Required | Description |
|----------------------|------------------------|----------|-------------|
| `location`           | `[float, float]`       | No       | Primary location to search for activities. |
| `hotel_location`     | `[float, float]`       | No       | User’s hotel location. |
| `budget`             | `number`               | No       | Total budget for activities. |
| `start_time`         | `string (ISO format)`  | No       | Plan start time (`YYYY-MM-DD HH:mm`). |
| `end_time`           | `string (ISO format)`  | No       | Plan end time (`YYYY-MM-DD HH:mm`). |
| `visited_locations`  | `array of strings`     | No       | List of place IDs already visited. |
| `planned_locations`  | `array of strings`     | No       | List of place IDs already planned. |
| `radius`             | `integer`              | No       | Search radius in meters. |
| `max_travel_time`    | `integer`              | No       | Max travel time between locations (in minutes). |

#### Example Request

```json
POST /api/generate_plan
Content-Type: application/json

{
  "location": [40.7128, -74.0060],
  "hotel_location": [40.7130, -74.0100],
  "budget": 400,
  "start_time": "2025-01-08 14:00",
  "end_time": "2025-01-08 19:00",
  "visited_locations": ["ChIJN2yUKtRu5kcREcQ19Yr8ISk"],
  "radius": 3000,
  "max_travel_time": 45
}
```

### Response

Returns an itinerary object with structured stops.

#### Example Response

```json
{
  "itinerary": [
    {
      "place_id": "ChIJAT1t_tDeuEmsRUsoyG83frY4",
      "name": "Statue of Liberty",
      "category": "attraction",
      "start_time": "2025-01-08 14:30",
      "end_time": "2025-01-08 15:30",
      "estimated_cost": 25
    }
  ],
  "total_estimated_cost": 40,
  "message": "Itinerary successfully generated."
}
```

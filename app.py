from flask import Flask, request, jsonify
from flask_cors import CORS
from planbuilder.api import fetch_activities, generate_plan, fetch_places_nearby
from planbuilder.database import initialize_database
from flasgger import Swagger

app = Flask(__name__)
Swagger(app)
CORS(app)

@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route('/api/fetch_places', methods=['POST'])
def api_fetch_places():
    """
    Fetch places near a given location.
    ---
    tags:
      - Places
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            location:
              type: array
              items:
                type: number
              example: [40.7128, -74.0060]
            query:
              type: string
              example: "coffee shop"
            radius:
              type: integer
              example: 3000
    responses:
      200:
        description: A list of places
    """
    data = request.json
    location = data.get('location')
    query = data.get('query')
    radius = data.get('radius', 3000)

    if not location or not query:
        return jsonify({"error": "Missing required fields: 'location' and 'query'"}), 400

    try:
        places = fetch_places_nearby(location, query, radius)
        return jsonify(places), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fetch_activities', methods=['POST'])
def api_fetch_activities():
    """
    Fetch multiple categories of activities near a given location.
    ---
    tags:
      - Activities
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            location:
              type: array
              items:
                type: number
              example: [40.7128, -74.0060]
            radius:
              type: integer
              example: 3000
    responses:
      200:
        description: A list of unique places with categories
    """
    data = request.json
    location = tuple(data.get('location', [40.7128, -74.0060]))  # Default: NYC
    radius = data.get('radius', 3000)

    try:
        activities = fetch_activities(location, radius)
        return jsonify(activities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_plan', methods=['POST'])
def api_generate_plan():
    """
    Generate an itinerary plan based on user preferences.
    ---
    tags:
      - Plan
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            location:
              type: array
              items:
                type: number
              example: [40.7128, -74.0060]
            hotel_location:
              type: array
              items:
                type: number
              example: [40.7130, -74.0100]
            budget:
              type: number
              example: 500
            start_time:
              type: string
              example: "2025-01-08 14:00"
            end_time:
              type: string
              example: "2025-01-08 19:00"
            visited_locations:
              type: array
              items:
                type: string
              example: ["ChIJN2yUKtRu5kcREcQ19Yr8ISk"]
            planned_locations:
              type: array
              items:
                type: string
              example: []
            radius:
              type: integer
              example: 3000
            max_travel_time:
              type: integer
              example: 60
    responses:
      200:
        description: Generated itinerary plan
    """
    data = request.json
    try:
        plan = generate_plan(data)
        return plan, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
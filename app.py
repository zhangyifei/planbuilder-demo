from flask import Flask, request, jsonify
from flask_cors import CORS
from planbuilder.api import fetch_activities, generate_plan, fetch_places_nearby
from planbuilder.database import initialize_database

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route('/fetch_places', methods=['POST'])
def api_fetch_places():
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

@app.route('/fetch_activities', methods=['POST'])
def api_fetch_activities():
    data = request.json
    location = tuple(data.get('location', [40.7128, -74.0060]))  # Default: NYC
    radius = data.get('radius', 3000)

    try:
        activities = fetch_activities(location, radius)
        return jsonify(activities), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_plan', methods=['POST'])
def api_generate_plan():
    data = request.json

    try:
        plan = generate_plan(data)
        return plan, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
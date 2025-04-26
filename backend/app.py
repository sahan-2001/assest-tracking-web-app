from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2, psycopg2.extras
import json

app = Flask(__name__)
CORS(app)

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="12345678",
    port="5432"
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/assets', methods=['GET'])
def get_assets():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Use ST_AsGeoJSON as recommended in the tutorial
    cur.execute("""
        SELECT id, name, ST_AsGeoJSON(geom) as geometry 
        FROM assets
    """)
    rows = cur.fetchall()
    cur.close()

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "id": row["id"],
                "name": row["name"]
            }
        })
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
def update_asset_location(asset_id):
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    cur = conn.cursor()
    # Use PostGIS functions as recommended
    cur.execute(
        "UPDATE assets SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326) WHERE id=%s",
        (longitude, latitude, asset_id)  # Note: longitude first!
    )
    conn.commit()
    cur.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
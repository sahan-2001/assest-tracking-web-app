from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration - update these with your credentials
DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "12345678",
    "port": "5432"
}

def get_db_connection():
    """Establish and return a new database connection"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Endpoint to fetch all assets as GeoJSON FeatureCollection"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Query using PostGIS functions (as shown in PDF Chapter 4.3)
        cur.execute("""
            SELECT 
                id, 
                name, 
                asset_type,
                ST_AsGeoJSON(geom)::json AS geometry,
                TO_CHAR(last_seen, 'YYYY-MM-DD"T"HH24:MI:SS') AS last_seen
            FROM assets
            WHERE geom IS NOT NULL
        """)
        
        # Build GeoJSON FeatureCollection (PDF Chapter 4.5)
        features = []
        for row in cur.fetchall():
            features.append({
                "type": "Feature",
                "geometry": row['geometry'],
                "properties": {
                    "id": row['id'],
                    "name": row['name'],
                    "asset_type": row.get('asset_type', 'unknown'),
                    "last_seen": row['last_seen']
                }
            })
        
        return jsonify({
            "type": "FeatureCollection",
            "features": features
        })
        
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
def update_asset_location(asset_id):
    """Endpoint to update asset location (PDF Chapter 4.4)"""
    data = request.get_json()
    try:
        longitude = float(data['longitude'])
        latitude = float(data['latitude'])
    except (KeyError, ValueError) as e:
        return jsonify({"error": "Invalid coordinates"}), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use PostGIS functions as shown in PDF
        cur.execute("""
            UPDATE assets 
            SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                last_seen = NOW()
            WHERE id = %s
            RETURNING id
        """, (longitude, latitude, asset_id))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Asset not found"}), 404
            
        conn.commit()
        return jsonify({
            "status": "success",
            "asset_id": asset_id,
            "new_location": [longitude, latitude]
        })
        
    except Exception as e:
        app.logger.error(f"Update error: {str(e)}")
        return jsonify({"error": "Update failed"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
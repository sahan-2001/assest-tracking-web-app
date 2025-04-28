from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras

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
    """Establish and return a new database connection."""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')

@app.route('/api/assets/all', methods=['GET'])
def get_all_assets():
    """Return all assets from the database."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT
                id,
                name,
                asset_type,
                ST_AsGeoJSON(geom)::json AS geometry,
                TO_CHAR(last_seen, 'YYYY-MM-DD"T"HH24:MI:SS') AS last_seen
            FROM assets
            WHERE geom IS NOT NULL;
        """)
        assets = []
        for row in cur.fetchall():
            assets.append({
                "type": "Feature",
                "geometry": row['geometry'],
                "properties": {
                    "id": row['id'],
                    "name": row['name'],
                    "asset_type": row.get('asset_type', 'unknown'),
                    "last_seen": row['last_seen'],
                }
            })
        return jsonify({"assets": assets})
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/assets/near', methods=['GET'])
def get_nearby_assets():
    select_lat = request.args.get('select_lat', type=float)
    select_lon = request.args.get('select_lon', type=float)
    dest_lat = request.args.get('dest_lat', type=float)
    dest_lon = request.args.get('dest_lon', type=float)
    radius = request.args.get('radius', default=1000, type=int)  # new: search radius in meters

    if select_lat is None or select_lon is None:
        return jsonify({"error": "Missing coordinates"}), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT
                id,
                name,
                asset_type,
                ST_AsGeoJSON(geom)::json AS geometry,
                TO_CHAR(last_seen, 'YYYY-MM-DD"T"HH24:MI:SS') AS last_seen,
                ST_Distance(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS distance_from_select
            FROM assets
            WHERE geom IS NOT NULL
            AND ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                %s
            )
            ORDER BY distance_from_select
        """, (
            select_lon, select_lat,
            select_lon, select_lat,
            radius
        ))

        features = []
        for row in cur.fetchall():
            features.append({
                "type": "Feature",
                "geometry": row['geometry'],
                "properties": {
                    "id": row['id'],
                    "name": row['name'],
                    "asset_type": row.get('asset_type', 'unknown'),
                    "last_seen": row['last_seen'],
                    "distance_from_select": row['distance_from_select'],
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
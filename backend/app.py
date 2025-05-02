from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)
app = Flask(__name__, static_folder='static')

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "12345678",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/assets/all', methods=['GET'])
def get_all_assets():
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
    radius = request.args.get('radius', default=1000, type=int)

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

@app.route('/booking/book', methods=['POST'])
def book_asset():
    data = request.get_json()
    asset_id = data.get('asset_id')
    user_name = data.get('user_name')
    phone = data.get('phone')
    duration_hours = data.get('duration_hours')

    if not all([asset_id, user_name, phone, duration_hours]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Calculate end time based on duration
        cur.execute("""
            INSERT INTO bookings (asset_id, user_id, start_time, end_time)
            VALUES (%s, %s, NOW(), NOW() + INTERVAL '%s hours')
            RETURNING id;
        """, (asset_id, phone, duration_hours))

        booking_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({"success": True, "booking_id": booking_id})
    except Exception as e:
        app.logger.error(f"Booking error: {str(e)}")
        return jsonify({"success": False, "error": "Booking operation failed"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking_details(booking_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Fetch booking details along with the asset details
        cur.execute("""
            SELECT
                b.id AS booking_id,
                b.start_time,
                b.end_time,
                a.id AS asset_id,
                a.name AS asset_name,
                a.asset_type,
                ST_AsGeoJSON(a.geom)::json AS geometry
            FROM bookings b
            JOIN assets a ON b.asset_id = a.id
            WHERE b.id = %s;
        """, (booking_id,))

        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Prepare the response
        return jsonify({
            "booking_id": booking['booking_id'],
            "start_time": booking['start_time'],
            "end_time": booking['end_time'],
            "asset": {
                "id": booking['asset_id'],
                "name": booking['asset_name'],
                "type": booking['asset_type'],
                "coordinates": booking['geometry']['coordinates']
            }
        })
    except Exception as e:
        app.logger.error(f"Error fetching booking details: {str(e)}")
        return jsonify({"error": "Failed to fetch booking details"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

            
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
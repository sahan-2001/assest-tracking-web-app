from flask import Blueprint, jsonify, request, render_template
import psycopg2
import psycopg2.extras

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

# Database configuration - same as your main app
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

@booking_bp.route('/')
def booking_page():
    """Render the booking page."""
    return render_template('booking.html')

@booking_bp.route('/book', methods=['POST'])
def book_asset():
    """Handle asset booking."""
    data = request.get_json()
    asset_id = data.get('asset_id')
    user_id = data.get('user_id', 'anonymous')
    
    if not asset_id:
        return jsonify({"error": "Asset ID is required"}), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check asset availability
        cur.execute("""
            SELECT a.id, b.id IS NOT NULL as is_booked
            FROM assets a
            LEFT JOIN bookings b ON a.id = b.asset_id 
                AND (b.end_time > NOW() OR b.end_time IS NULL)
            WHERE a.id = %s
            LIMIT 1
        """, (asset_id,))
        
        result = cur.fetchone()
        if not result:
            return jsonify({"error": "Asset not found"}), 404
        if result[1]:  # is_booked
            return jsonify({"error": "Asset is already booked"}), 409

        # Create booking
        cur.execute("""
            INSERT INTO bookings (asset_id, user_id, start_time)
            VALUES (%s, %s, NOW())
            RETURNING id
        """, (asset_id, user_id))
        booking_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            "success": True,
            "booking_id": booking_id,
            "message": "Asset booked successfully"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@booking_bp.route('/status/<asset_id>')
def booking_status(asset_id):
    """Check booking status of an asset."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT b.*, a.name as asset_name
            FROM bookings b
            JOIN assets a ON b.asset_id = a.id
            WHERE b.asset_id = %s
            AND (b.end_time > NOW() OR b.end_time IS NULL)
            ORDER BY b.start_time DESC
            LIMIT 1
        """, (asset_id,))
        
        booking = cur.fetchone()
        if booking:
            return jsonify({
                "is_booked": True,
                "booking": dict(booking)
            })
        return jsonify({"is_booked": False})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
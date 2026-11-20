from flask import Blueprint, render_template, jsonify, session
from flask_login import login_required, current_user
from database.connection import get_db_connection
from modules.sensor.manager import fetch_telemetry_for_motorcycle, get_active_mode, get_simulation_intensity

telemetry_bp = Blueprint('telemetry', __name__)

@telemetry_bp.route('/telemetry')
@login_required
def index():
    bike_id = session.get('active_motorcycle_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # User bikes
            cursor.execute(
                """
                SELECT m.motorcycle_id, mm.name as model_name, mfg.name as mfg_name
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s AND m.is_active = TRUE
                """,
                (current_user.id,)
            )
            bikes = cursor.fetchall()
            if not bike_id and bikes:
                bike_id = bikes[0]['motorcycle_id']
                session['active_motorcycle_id'] = bike_id

            current_bike = next((b for b in bikes if b['motorcycle_id'] == bike_id), None)

            # Applicable sensors for current bike
            cursor.execute(
                """
                SELECT sd.*, sc.is_installed, sc.is_simulated, sc.calibration_offset
                FROM motorcycles m
                JOIN sensor_configurations sc ON m.variant_id = sc.variant_id
                JOIN sensor_definitions sd ON sc.sensor_id = sd.sensor_id
                WHERE m.motorcycle_id = %s AND sc.is_installed = TRUE
                ORDER BY sd.category ASC, sd.name ASC
                """,
                (bike_id,)
            )
            sensors = cursor.fetchall()
    finally:
        conn.close()

    source_mode = get_active_mode(current_user.id)
    intensity = get_simulation_intensity(current_user.id)
    telemetry_packet = fetch_telemetry_for_motorcycle(bike_id, persist=False)

    return render_template(
        'telemetry/live.html',
        bikes=bikes,
        current_bike=current_bike,
        sensors=sensors,
        source_mode=source_mode,
        intensity=intensity,
        telemetry=telemetry_packet
    )

@telemetry_bp.route('/api/telemetry/live', methods=['GET'])
@login_required
def get_live_stream():
    bike_id = session.get('active_motorcycle_id')
    if not bike_id:
        return jsonify({"error": "No active motorcycle selected"}), 400

    telemetry = fetch_telemetry_for_motorcycle(bike_id, persist=True)
    return jsonify(telemetry)

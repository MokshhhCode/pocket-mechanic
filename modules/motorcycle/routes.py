from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from database.connection import get_db_connection, log_audit

motorcycle_bp = Blueprint('motorcycle', __name__, url_prefix='/api/motorcycles')

@motorcycle_bp.route('/manufacturers', methods=['GET'])
def get_manufacturers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT manufacturer_id, name, country, founded_year, logo_slug FROM manufacturers WHERE is_active = TRUE ORDER BY name ASC")
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

@motorcycle_bp.route('/models/<int:mfg_id>', methods=['GET'])
def get_models(mfg_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT model_id, name, category, silhouette_code
                FROM motorcycle_models
                WHERE manufacturer_id = %s
                ORDER BY name ASC
                """,
                (mfg_id,)
            )
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

@motorcycle_bp.route('/specs/<int:model_id>', methods=['GET'])
def get_model_specs(model_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT mv.*, ms.*, mm.name as model_name, mfg.name as mfg_name
                FROM motorcycle_models mm
                JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                JOIN motorcycle_variants mv ON mm.model_id = mv.model_id
                JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                WHERE mm.model_id = %s
                LIMIT 1
                """,
                (model_id,)
            )
            spec = cursor.fetchone()
            if not spec:
                return jsonify({"error": "Specifications not found"}), 404
            return jsonify(spec)
    finally:
        conn.close()

@motorcycle_bp.route('/switch/<int:bike_id>', methods=['POST'])
@login_required
def switch_active_bike(bike_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT motorcycle_id FROM motorcycles WHERE motorcycle_id = %s AND user_id = %s",
                (bike_id, current_user.id)
            )
            bike = cursor.fetchone()
            if not bike:
                return jsonify({"error": "Motorcycle not found or access denied"}), 404

            session['active_motorcycle_id'] = bike_id
            log_audit(current_user.id, "SWITCH_MOTORCYCLE", "motorcycles", bike_id)
            return jsonify({"success": True, "active_motorcycle_id": bike_id})
    finally:
        conn.close()

@motorcycle_bp.route('/register-another', methods=['POST'])
@login_required
def register_another_bike():
    data = request.json or {}
    model_id = data.get('model_id')
    custom_make = data.get('custom_make', '').strip()
    custom_model = data.get('custom_model', '').strip()
    year = int(data.get('year', 2023))
    colour = data.get('colour', 'Black').strip()
    reg_number = data.get('registration_number', '').strip().upper()

    if not reg_number:
        return jsonify({"error": "Registration number is required"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            variant_id = None
            if model_id:
                cursor.execute("SELECT variant_id FROM motorcycle_variants WHERE model_id = %s LIMIT 1", (model_id,))
                v_row = cursor.fetchone()
                if v_row:
                    variant_id = v_row['variant_id']

            cursor.execute(
                """
                INSERT INTO motorcycles (user_id, variant_id, custom_make, custom_model, manufacturing_year, colour, registration_number, current_odometer_km, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 5000, TRUE)
                """,
                (
                    current_user.id, variant_id,
                    custom_make if not variant_id else None,
                    custom_model if not variant_id else None,
                    year, colour, reg_number
                )
            )
            new_bike_id = cursor.lastrowid
            session['active_motorcycle_id'] = new_bike_id
            log_audit(current_user.id, "ADD_MOTORCYCLE", "motorcycles", new_bike_id, {"reg": reg_number})
            return jsonify({"success": True, "motorcycle_id": new_bike_id})
    finally:
        conn.close()

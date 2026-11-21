import json
from decimal import Decimal
from datetime import datetime, date
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, Response
from flask_login import login_required, current_user, login_user
from database.connection import get_db_connection, log_audit
from database.models import User
from modules.sensor.manager import (
    fetch_telemetry_for_motorcycle, get_active_mode, get_simulation_intensity
)
from modules.ml_engine import run_ml_inference
from modules.recommendations import MaintenanceRecommendationEngine

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def welcome():
    # Check for recently authenticated user
    last_user = User.get_last_authenticated_user()
    return render_template('index.html', last_user=last_user)

@dashboard_bp.route('/dashboard')
@login_required
def home():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch all user motorcycles
            cursor.execute(
                """
                SELECT m.*, mv.cooling_type, mv.brake_type, mv.abs_type, mv.final_drive_type,
                       mv.fuel_delivery_type, mv.wheel_type, ms.*,
                       mm.name as model_name, mm.category, mm.image_url, mm.silhouette_code, mfg.name as mfg_name, mfg.logo_slug
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s AND m.is_active = TRUE
                ORDER BY m.created_at DESC
                """,
                (current_user.id,)
            )
            bikes = cursor.fetchall()

            if not bikes:
                return redirect(url_for('auth.register'))

            # Active motorcycle selection
            active_id = session.get('active_motorcycle_id')
            if not active_id or not any(b['motorcycle_id'] == active_id for b in bikes):
                active_id = bikes[0]['motorcycle_id']
                session['active_motorcycle_id'] = active_id

            current_bike = next(b for b in bikes if b['motorcycle_id'] == active_id)

            # 2. Fetch Applicable Components grouped by Check Interval Group
            cursor.execute(
                """
                SELECT c.component_id, c.component_code, c.name as base_name, c.category, c.is_critical,
                       c.check_interval_group, mca.is_applicable, mca.display_name_override, mca.rule_condition,
                       ms.interval_km, ms.inspection_action
                FROM model_component_applicability mca
                JOIN component_catalogue c ON mca.component_id = c.component_id
                LEFT JOIN maintenance_schedules ms ON ms.variant_id = mca.variant_id AND ms.component_id = c.component_id
                WHERE mca.variant_id = %s AND mca.is_applicable = TRUE
                ORDER BY c.is_critical DESC, c.name ASC
                """,
                (current_bike.get('variant_id'),)
            )
            applicable_components = cursor.fetchall()

            # Group components
            group_a_ride = [c for c in applicable_components if c['check_interval_group'] == 'Every Ride']
            group_b_weekly = [c for c in applicable_components if c['check_interval_group'] == 'Weekly']
            group_c_periodic = [c for c in applicable_components if c['check_interval_group'] == 'Periodic']

            # 3. Read developer settings (Defaults first, user-specific second)
            cursor.execute(
                """
                SELECT setting_key, setting_value FROM application_settings
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY (user_id IS NOT NULL) ASC, updated_at ASC
                """,
                (current_user.id,)
            )
            settings_rows = cursor.fetchall()
            settings = {r['setting_key']: r['setting_value'] for r in settings_rows}

    finally:
        conn.close()

    # 4. Fetch latest telemetry & run quick ML condition assessment for urgent work panel
    telemetry = fetch_telemetry_for_motorcycle(active_id, persist=False)
    readings = telemetry.get("readings", {})

    ml_inputs = {
        "odometer_km": current_bike.get("current_odometer_km", 5000),
        "engine_hours": round(current_bike.get("current_odometer_km", 5000) / 38.0, 1),
        "ambient_temp": 30.0,
        "vehicle_speed": readings.get("VEH_SPEED", 45.0),
        "engine_rpm": readings.get("ENG_RPM", 3200.0),
        "engine_temp": readings.get("ENG_TEMP", 88.0),
        "battery_voltage": readings.get("BAT_VOLT", 14.2),
        "vibration_level": readings.get("VIB_LEVEL", 2.8),
        "tyre_pressure_front": readings.get("TYRE_PRES_FRONT", 29.0),
        "tyre_pressure_rear": readings.get("TYRE_PRES_REAR", 33.0),
        "brake_pad_thickness": readings.get("BRAKE_PAD_WEAR", 4.5),
        "oil_quality_index": readings.get("OIL_QUALITY", 88.0),
        "chain_slack_mm": readings.get("CHAIN_SLACK", 27.0),
        "fuel_rate": readings.get("FUEL_RATE", 3.1)
    }
    ml_result = run_ml_inference(ml_inputs, model_name="Random_Forest", motorcycle_id=active_id)
    rec_result = MaintenanceRecommendationEngine.generate_recommendations(
        motorcycle_id=active_id,
        ml_result=ml_result,
        telemetry=telemetry
    )

    # Assign condition colors to component groups dynamically based on readings
    def assign_comp_status(comp_code):
        if comp_code == "TYRE_PRESSURE":
            fp = readings.get("TYRE_PRES_FRONT", 29)
            rp = readings.get("TYRE_PRES_REAR", 33)
            return "red" if (fp < 22 or rp < 24) else ("yellow" if (fp < 26 or rp < 29) else "green")
        elif comp_code in ("BRAKE_OPERATION", "BRAKE_PADS", "REAR_BRAKE_LINING"):
            bp = readings.get("BRAKE_PAD_WEAR", 4.5)
            return "red" if bp < 1.5 else ("yellow" if bp < 2.5 else "green")
        elif comp_code in ("ENGINE_OIL", "INTERNAL_ENGINE"):
            oq = readings.get("OIL_QUALITY", 88)
            et = readings.get("ENG_TEMP", 88)
            return "red" if (oq < 30 or et > 120) else ("yellow" if (oq < 60 or et > 105) else "green")
        elif comp_code in ("BATTERY_HEALTH", "LIGHTS_ELECTRICAL"):
            bv = readings.get("BAT_VOLT", 14.1)
            return "red" if (bv < 11.5 or bv > 15.2) else ("yellow" if bv < 12.4 else "green")
        elif comp_code == "DRIVE_CHAIN":
            cs = readings.get("CHAIN_SLACK", 27)
            return "red" if cs > 45 else ("yellow" if cs > 35 else "green")
        elif comp_code == "ENGINE_COOLANT":
            et = readings.get("ENG_TEMP", 88)
            return "red" if et > 115 else ("yellow" if et > 102 else "green")
        return "green"

    for c in group_a_ride + group_b_weekly + group_c_periodic:
        c['status_color'] = assign_comp_status(c['component_code'])

    return render_template(
        'dashboard/home.html',
        bikes=bikes,
        current_bike=current_bike,
        group_a_ride=group_a_ride,
        group_b_weekly=group_b_weekly,
        group_c_periodic=group_c_periodic,
        settings=settings,
        telemetry=telemetry,
        urgent_work=rec_result,
        ml_result=ml_result
    )

@dashboard_bp.route('/api/settings/update', methods=['POST'])
def update_setting():
    data = request.json or {}
    key = data.get('key')
    val = data.get('value')
    if not key or val is None:
        return jsonify({"error": "Missing key or value"}), 400

    if key == 'THEME_MODE':
        session['THEME_MODE'] = str(val).upper()

    if current_user.is_authenticated:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO application_settings (user_id, setting_key, setting_value)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), updated_at = CURRENT_TIMESTAMP
                    """,
                    (current_user.id, key, str(val))
                )
            log_audit(current_user.id, "UPDATE_SETTING", "application_settings", key, {"value": val})
        finally:
            conn.close()

    resp = jsonify({"success": True, "key": key, "value": val})
    if key == 'THEME_MODE':
        resp.set_cookie('pm_theme', str(val).lower(), max_age=31536000, samesite='Lax', path='/')
    return resp

@dashboard_bp.route('/garage')
@login_required
def garage():
    """Garage and fleet overview with complete OEM technical specifications."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch all user motorcycles
            cursor.execute(
                """
                SELECT m.*, mv.cooling_type, mv.brake_type, mv.abs_type, mv.final_drive_type,
                       mv.fuel_delivery_type, mv.wheel_type, ms.*,
                       mm.name as model_name, mm.category, mm.silhouette_code, mfg.name as mfg_name, mfg.logo_slug
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s AND m.is_active = TRUE
                ORDER BY m.created_at DESC
                """,
                (current_user.id,)
            )
            bikes = cursor.fetchall()

            if not bikes:
                return redirect(url_for('auth.register'))

            # Active motorcycle selection
            active_id = session.get('active_motorcycle_id')
            if not active_id or not any(b['motorcycle_id'] == active_id for b in bikes):
                active_id = bikes[0]['motorcycle_id']
                session['active_motorcycle_id'] = active_id

            current_bike = next(b for b in bikes if b['motorcycle_id'] == active_id)

            # 2. Fetch Applicable Components
            cursor.execute(
                """
                SELECT c.component_id, c.component_code, c.name as base_name, c.category, c.is_critical,
                       c.check_interval_group, mca.is_applicable, mca.display_name_override, mca.rule_condition,
                       ms.interval_km, ms.inspection_action
                FROM model_component_applicability mca
                JOIN component_catalogue c ON mca.component_id = c.component_id
                LEFT JOIN maintenance_schedules ms ON ms.variant_id = mca.variant_id AND ms.component_id = c.component_id
                WHERE mca.variant_id = %s AND mca.is_applicable = TRUE
                ORDER BY c.category ASC, c.name ASC
                """,
                (current_bike.get('variant_id'),)
            )
            applicable_components = cursor.fetchall()

            # 3. Diagnostic history summary for current bike
            cursor.execute(
                """
                SELECT COUNT(*) as total_tickets,
                       SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_tickets,
                       SUM(CASE WHEN severity = 'Critical' AND status != 'Resolved' THEN 1 ELSE 0 END) as active_critical
                FROM diagnostic_tickets
                WHERE motorcycle_id = %s
                """,
                (active_id,)
            )
            ticket_summary = cursor.fetchone() or {"total_tickets": 0, "resolved_tickets": 0, "active_critical": 0}

    finally:
        conn.close()

    return render_template(
        'dashboard/garage.html',
        bikes=bikes,
        current_bike=current_bike,
        applicable_components=applicable_components,
        ticket_summary=ticket_summary
    )

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Local Settings, Rider Profile, and Local Offline MySQL Data Management."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch all local rider profiles
            all_users = User.get_all_users()

            # 2. Database statistics: Table row counts in offline MySQL
            cursor.execute(
                """
                SELECT TABLE_NAME as table_name, TABLE_ROWS as table_rows
                FROM information_schema.tables
                WHERE table_schema = 'pocket_mechanic_db'
                ORDER BY TABLE_NAME ASC
                """
            )
            db_tables = cursor.fetchall()

            # Total records across all tables
            total_records = sum((t.get('table_rows') or 0) for t in db_tables)

            # 3. Current user settings (defaults first, user overrides second)
            cursor.execute(
                """
                SELECT setting_key, setting_value FROM application_settings
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY (user_id IS NOT NULL) ASC, updated_at ASC
                """,
                (current_user.id,)
            )
            settings_rows = cursor.fetchall()
            user_settings = {r['setting_key']: r['setting_value'] for r in settings_rows}

            # 4. User's motorcycle count & active tickets
            cursor.execute("SELECT COUNT(*) as cnt FROM motorcycles WHERE user_id = %s AND is_active = TRUE", (current_user.id,))
            bike_count = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM diagnostic_tickets WHERE user_id = %s", (current_user.id,))
            ticket_count = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_records mr JOIN motorcycles m ON mr.motorcycle_id = m.motorcycle_id WHERE m.user_id = %s", (current_user.id,))
            record_count = cursor.fetchone()['cnt']

    finally:
        conn.close()

    return render_template(
        'dashboard/settings.html',
        all_users=all_users,
        db_tables=db_tables,
        total_records=total_records,
        user_settings=user_settings,
        stats={
            "bikes": bike_count,
            "tickets": ticket_count,
            "records": record_count
        }
    )

@dashboard_bp.route('/api/motorcycles/update/<int:bike_id>', methods=['POST'])
@login_required
def update_motorcycle(bike_id):
    """Updates basic bike information such as odometer, colour, and registration."""
    data = request.json or {}
    odometer = data.get('current_odometer_km')
    colour = data.get('colour', '').strip()
    reg = data.get('registration_number', '').strip().upper()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT motorcycle_id FROM motorcycles WHERE motorcycle_id = %s AND user_id = %s",
                (bike_id, current_user.id)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Motorcycle not found or unauthorized"}), 404

            updates = []
            params = []
            if odometer is not None:
                updates.append("current_odometer_km = %s")
                params.append(int(odometer))
            if colour:
                updates.append("colour = %s")
                params.append(colour)
            if reg:
                updates.append("registration_number = %s")
                params.append(reg)

            if updates:
                params.append(bike_id)
                cursor.execute(
                    f"UPDATE motorcycles SET {', '.join(updates)} WHERE motorcycle_id = %s",
                    tuple(params)
                )
                log_audit(current_user.id, "UPDATE_MOTORCYCLE", "motorcycles", bike_id, data)

        return jsonify({"success": True, "message": "Motorcycle updated successfully."})
    finally:
        conn.close()

@dashboard_bp.route('/api/profile/switch/<int:user_id>', methods=['POST'])
@login_required
def switch_profile(user_id):
    """Switches the active local rider profile without requiring password re-entry."""
    target_user = User.get_by_id(user_id)
    if not target_user:
        return jsonify({"error": "Rider profile not found."}), 404

    login_user(target_user, remember=True)
    session.pop('active_motorcycle_id', None)

    # Automatically set first active motorcycle
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT motorcycle_id FROM motorcycles WHERE user_id = %s AND is_active = TRUE ORDER BY motorcycle_id ASC LIMIT 1",
                (user_id,)
            )
            b = cursor.fetchone()
            if b:
                session['active_motorcycle_id'] = b['motorcycle_id']
    finally:
        conn.close()

    return jsonify({"success": True, "user_id": user_id, "full_name": target_user.full_name})

def _json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

@dashboard_bp.route('/api/data/export', methods=['GET'])
@login_required
def export_data():
    """Generates a comprehensive JSON backup of the user's motorcycles, diagnostics, and maintenance logs."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. User Profile
            cursor.execute("SELECT user_id, full_name, email, city, state, licence_last4, created_at FROM users WHERE user_id = %s", (current_user.id,))
            user_data = cursor.fetchone()

            # 2. Motorcycles
            cursor.execute(
                """
                SELECT m.*, mm.name as model_name, mfg.name as mfg_name
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s
                """,
                (current_user.id,)
            )
            motorcycles = cursor.fetchall()

            # 3. Diagnostic Tickets & ML Results
            cursor.execute(
                """
                SELECT t.*, r.model_name as ml_model, r.predicted_condition, r.confidence_score
                FROM diagnostic_tickets t
                LEFT JOIN diagnostic_results r ON t.ticket_id = r.ticket_id
                WHERE t.user_id = %s
                ORDER BY t.created_at DESC
                """,
                (current_user.id,)
            )
            tickets = cursor.fetchall()

            # 4. Maintenance Records
            cursor.execute(
                """
                SELECT mr.*
                FROM maintenance_records mr
                JOIN motorcycles m ON mr.motorcycle_id = m.motorcycle_id
                WHERE m.user_id = %s
                ORDER BY mr.service_date DESC
                """,
                (current_user.id,)
            )
            records = cursor.fetchall()

            # 5. User Settings
            cursor.execute("SELECT setting_key, setting_value FROM application_settings WHERE user_id = %s", (current_user.id,))
            settings = cursor.fetchall()

        payload = {
            "application": "Pocket Mechanic Desktop",
            "version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "storage_type": "Offline MySQL (pocket_mechanic_db)",
            "rider": user_data,
            "motorcycles": motorcycles,
            "diagnostic_tickets": tickets,
            "maintenance_records": records,
            "settings": settings
        }

        json_str = json.dumps(payload, indent=2, default=_json_serial)
        filename = f"pocket_mechanic_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return Response(
            json_str,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    finally:
        conn.close()

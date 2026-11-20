from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from database.connection import get_db_connection, log_audit

history_bp = Blueprint('history', __name__)

@history_bp.route('/history', methods=['GET'])
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

            # 1. Fetch Diagnostic Tickets for this motorcycle
            cursor.execute(
                """
                SELECT t.*, r.model_name as ml_model, r.predicted_condition, r.confidence_score,
                       c.name as component_name
                FROM diagnostic_tickets t
                LEFT JOIN diagnostic_results r ON t.ticket_id = r.ticket_id
                LEFT JOIN component_catalogue c ON t.component_id = c.component_id
                WHERE t.motorcycle_id = %s AND t.user_id = %s
                ORDER BY t.created_at DESC
                """,
                (bike_id, current_user.id)
            )
            tickets = cursor.fetchall()

            # 2. Fetch Maintenance Services & Repairs
            cursor.execute(
                """
                SELECT mr.*, t.issue_title as ticket_title
                FROM maintenance_records mr
                LEFT JOIN diagnostic_tickets t ON mr.ticket_id = t.ticket_id
                WHERE mr.motorcycle_id = %s
                ORDER BY mr.service_date DESC, mr.created_at DESC
                """,
                (bike_id,)
            )
            records = cursor.fetchall()

            # 3. Component replacements
            cursor.execute(
                """
                SELECT cr.*, c.name as component_name
                FROM component_replacements cr
                JOIN component_catalogue c ON cr.component_id = c.component_id
                WHERE cr.motorcycle_id = %s
                ORDER BY cr.replaced_at DESC
                """,
                (bike_id,)
            )
            replacements = cursor.fetchall()

            # Components for manual record entry
            cursor.execute("SELECT component_id, name FROM component_catalogue ORDER BY name ASC")
            all_components = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        'history/timeline.html',
        bikes=bikes,
        current_bike=current_bike,
        tickets=tickets,
        records=records,
        replacements=replacements,
        all_components=all_components
    )

@history_bp.route('/api/history/add-record', methods=['POST'])
@login_required
def add_maintenance_record():
    data = request.json or {}
    bike_id = int(data.get('motorcycle_id') or session.get('active_motorcycle_id') or 1)
    service_type = data.get('service_type', 'Periodic Service').strip()
    service_date = data.get('service_date')
    odometer = int(data.get('odometer_reading_km', 5000))
    center = data.get('service_center', '').strip()
    cost = float(data.get('total_cost', 0.0))
    performed_by = data.get('performed_by', '').strip()
    description = data.get('description', '').strip()
    ticket_id = data.get('ticket_id')

    if not service_date or not description:
        return jsonify({"error": "Service date and description are required."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO maintenance_records (motorcycle_id, ticket_id, service_date, odometer_reading_km, service_type, description, service_center, total_cost, performed_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    bike_id, int(ticket_id) if ticket_id else None,
                    service_date, odometer, service_type, description, center, cost, performed_by
                )
            )
            record_id = cursor.lastrowid

            # If linked to a ticket, resolve ticket automatically
            if ticket_id:
                cursor.execute(
                    "UPDATE diagnostic_tickets SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP WHERE ticket_id = %s",
                    (int(ticket_id),)
                )

            # Update motorcycle odometer
            cursor.execute(
                "UPDATE motorcycles SET current_odometer_km = GREATEST(current_odometer_km, %s) WHERE motorcycle_id = %s",
                (odometer, bike_id)
            )

        log_audit(current_user.id, "ADD_MAINTENANCE_RECORD", "maintenance_records", record_id, {"service_type": service_type})
        return jsonify({"success": True, "record_id": record_id})
    finally:
        conn.close()

@history_bp.route('/schedule')
@login_required
def schedule():
    """Maintenance Schedule and Inspection Checklists based on OEM guidelines and odometer."""
    bike_id = session.get('active_motorcycle_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch active bike details
            cursor.execute(
                """
                SELECT m.motorcycle_id, m.current_odometer_km, m.manufacturing_year, m.colour, m.registration_number,
                       mv.variant_id, mm.name as model_name, mfg.name as mfg_name
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.motorcycle_id = %s
                """,
                (bike_id,)
            )
            active_bike = cursor.fetchone()

            if not active_bike:
                return redirect(url_for('dashboard.home'))

            current_km = active_bike.get('current_odometer_km', 5000)

            # 2. Fetch OEM Maintenance Schedule items for this variant
            cursor.execute(
                """
                SELECT ms.*, c.name as component_name, c.category, c.component_code
                FROM maintenance_schedules ms
                JOIN component_catalogue c ON ms.component_id = c.component_id
                WHERE ms.variant_id = %s
                ORDER BY ms.interval_km ASC, c.name ASC
                """,
                (active_bike.get('variant_id'),)
            )
            schedules = cursor.fetchall()

            # Group into Pre-Ride, Weekly, and Periodic Milestones
            pre_ride_items = [s for s in schedules if s.get('schedule_group') == 'Every Ride']
            weekly_items = [s for s in schedules if s.get('schedule_group') == 'Weekly']
            periodic_items = [s for s in schedules if s.get('schedule_group') == 'Periodic']

            # If no periodic items in schedule, create standard periodic checklist items
            milestones = [
                {"km": 1000, "title": "First Service Break-in Inspection", "due_in_km": max(0, 1000 - current_km), "is_due": current_km >= 1000},
                {"km": 5000, "title": "Engine Oil & Filter Renewal", "due_in_km": max(0, 5000 - (current_km % 5000)), "is_due": (current_km % 5000) > 4500 or (current_km % 5000) < 500},
                {"km": 10000, "title": "Spark Plug & Air Filter Replacement", "due_in_km": max(0, 10000 - (current_km % 10000)), "is_due": (current_km % 10000) > 9000 or (current_km % 10000) < 1000},
                {"km": 15000, "title": "Valve Clearance & Coolant Flush", "due_in_km": max(0, 15000 - (current_km % 15000)), "is_due": (current_km % 15000) > 14000 or (current_km % 15000) < 1000},
                {"km": 20000, "title": "Full Drive Chain & Sprocket Replacement", "due_in_km": max(0, 20000 - (current_km % 20000)), "is_due": (current_km % 20000) > 19000 or (current_km % 20000) < 1000}
            ]

            # 3. Recent inspections/services logged
            cursor.execute(
                """
                SELECT * FROM maintenance_records
                WHERE motorcycle_id = %s
                ORDER BY service_date DESC LIMIT 5
                """,
                (bike_id,)
            )
            recent_logs = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        'history/schedule.html',
        active_bike=active_bike,
        pre_ride_items=pre_ride_items,
        weekly_items=weekly_items,
        periodic_items=periodic_items,
        milestones=milestones,
        recent_logs=recent_logs
    )

@history_bp.route('/api/history/log-inspection', methods=['POST'])
@login_required
def log_inspection():
    """Quickly logs a completed inspection checklist directly into maintenance records."""
    data = request.json or {}
    bike_id = int(data.get('motorcycle_id') or session.get('active_motorcycle_id') or 1)
    checklist_title = data.get('checklist_title', 'Routine Inspection Completed').strip()
    notes = data.get('notes', 'All items passed visual & mechanical inspection according to OEM checklist.').strip()
    odometer = int(data.get('odometer_reading_km', 5000))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO maintenance_records (motorcycle_id, service_date, odometer_reading_km, service_type, description, service_center, total_cost, performed_by)
                VALUES (%s, CURRENT_DATE(), %s, 'Inspection', %s, 'Owner Inspection (Pocket Mechanic)', 0.0, %s)
                """,
                (bike_id, odometer, f"[{checklist_title}] {notes}", current_user.full_name)
            )
            record_id = cursor.lastrowid
        log_audit(current_user.id, "LOG_INSPECTION", "maintenance_records", record_id, {"title": checklist_title})
        return jsonify({"success": True, "record_id": record_id, "message": "Inspection successfully recorded into service history."})
    finally:
        conn.close()

import json
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from database.connection import get_db_connection, log_audit
from modules.sensor.manager import fetch_telemetry_for_motorcycle
from modules.ml_engine import run_ml_inference
from modules.recommendations import MaintenanceRecommendationEngine

diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/diagnostics', methods=['GET'])
@login_required
def index():
    bike_id = session.get('active_motorcycle_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch user motorcycles
            cursor.execute(
                """
                SELECT m.motorcycle_id, m.custom_make, m.custom_model, m.colour, m.registration_number,
                       mm.name as model_name, mfg.name as mfg_name, mv.cooling_type, mv.final_drive_type
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s AND m.is_active = TRUE
                """,
                (current_user.id,)
            )
            bikes = cursor.fetchall()
            if not bikes:
                flash("Please register a motorcycle first to run diagnostics.", "info")
                return redirect(url_for('auth.register'))

            if not bike_id or not any(b['motorcycle_id'] == bike_id for b in bikes):
                bike_id = bikes[0]['motorcycle_id']
                session['active_motorcycle_id'] = bike_id

            # Active bike details
            active_bike = next(b for b in bikes if b['motorcycle_id'] == bike_id)

            # 2. Fetch applicable components for active motorcycle
            cursor.execute(
                """
                SELECT c.component_id, c.component_code, c.name, c.category, c.is_critical,
                       mca.is_applicable, mca.display_name_override, mca.rule_condition
                FROM motorcycles m
                JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                JOIN model_component_applicability mca ON mv.variant_id = mca.variant_id
                JOIN component_catalogue c ON mca.component_id = c.component_id
                WHERE m.motorcycle_id = %s AND mca.is_applicable = TRUE
                ORDER BY c.is_critical DESC, c.name ASC
                """,
                (bike_id,)
            )
            components = cursor.fetchall()

            # 3. Fetch trained ML models
            cursor.execute(
                """
                SELECT m.model_id, m.model_name, m.algorithm, e.accuracy, e.f1_score, r.training_duration_sec
                FROM ml_models m
                JOIN ml_training_runs r ON m.model_id = r.model_id
                JOIN ml_evaluation_metrics e ON r.run_id = e.run_id
                ORDER BY e.f1_score DESC
                """
            )
            ml_models = cursor.fetchall()

            # 4. Fetch open tickets
            cursor.execute(
                """
                SELECT ticket_id, issue_title, severity, status, created_at
                FROM diagnostic_tickets
                WHERE motorcycle_id = %s AND status NOT IN ('Resolved')
                ORDER BY ticket_id DESC
                """,
                (bike_id,)
            )
            open_tickets = cursor.fetchall()

            # 5. Check Live ML Diagnostics setting
            cursor.execute(
                "SELECT setting_value FROM application_settings WHERE setting_key = 'LIVE_ML_DIAGNOSTICS' ORDER BY user_id DESC LIMIT 1"
            )
            live_setting = cursor.fetchone()
            live_ml_enabled = (live_setting['setting_value'].upper() == "ON") if live_setting else True

    finally:
        conn.close()

    # Pre-selected component from query params if passed from Wrenchy or Dashboard
    preselect_comp = request.args.get('component', '')
    preselect_desc = request.args.get('symptom', '')

    return render_template(
        'diagnostics/diagnose.html',
        bikes=bikes,
        active_bike=active_bike,
        components=components,
        ml_models=ml_models,
        open_tickets=open_tickets,
        live_ml_enabled=live_ml_enabled,
        preselect_comp=preselect_comp,
        preselect_desc=preselect_desc
    )

@diagnostics_bp.route('/api/diagnostics/execute', methods=['POST'])
@login_required
def execute_diagnosis():
    data = request.json or {}
    bike_id = int(data.get('motorcycle_id') or session.get('active_motorcycle_id') or 1)
    component_code = data.get('component_code', '').strip()
    problem_desc = data.get('problem_description', '').strip() or "Routine holistic diagnostic scan"
    category = data.get('problem_category', 'General Performance')
    selected_model = data.get('model_name') or data.get('model_override') or data.get('model') or 'Random_Forest'

    session_id = f"diag_{uuid.uuid4().hex[:12]}"

    # Step 1: Telemetry Acquisition
    telemetry = fetch_telemetry_for_motorcycle(bike_id, persist=True)
    readings = telemetry.get("readings", {})

    # Step 2: Component Applicability Lookup
    conn = get_db_connection()
    component_id = None
    component_name = "Overall Vehicle Systems"
    try:
        with conn.cursor() as cursor:
            if component_code:
                cursor.execute(
                    """
                    SELECT c.component_id, c.name, mca.display_name_override
                    FROM component_catalogue c
                    LEFT JOIN model_component_applicability mca ON c.component_id = mca.component_id
                    LEFT JOIN motorcycles m ON m.variant_id = mca.variant_id
                    WHERE c.component_code = %s AND (m.motorcycle_id = %s OR m.motorcycle_id IS NULL)
                    LIMIT 1
                    """,
                    (component_code, bike_id)
                )
                c_row = cursor.fetchone()
                if c_row:
                    component_id = c_row['component_id']
                    component_name = c_row['display_name_override'] or c_row['name']

            # Create Diagnostic Session Record
            cursor.execute(
                """
                INSERT INTO diagnostic_sessions (session_id, motorcycle_id, user_id, component_id, trigger_source, status)
                VALUES (%s, %s, %s, %s, 'USER_MANUAL', 'PROCESSING')
                """,
                (session_id, bike_id, current_user.id, component_id)
            )
    finally:
        conn.close()

    # Step 3: Classical ML Engine Inference
    ml_inputs = {
        "odometer_km": 8500,
        "engine_hours": 210,
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

    ml_result = run_ml_inference(ml_inputs, model_name=selected_model, motorcycle_id=bike_id)

    # Step 4: Maintenance Recommendation Layer
    rec_result = MaintenanceRecommendationEngine.generate_recommendations(
        motorcycle_id=bike_id,
        ml_result=ml_result,
        telemetry=telemetry,
        component_code=component_code,
        user_symptoms=problem_desc
    )

    # Step 5: Save Diagnostic Ticket & Result in MySQL
    ticket_id = None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Severity mapping
            severity = rec_result.get("overall_priority", "Medium")
            condition = rec_result.get("overall_condition", "Normal")
            ticket_title = f"{component_name}: {rec_result.get('urgent_summary', 'Diagnostic Assessment')[:100]}"
            ticket_status = "Open" if condition != "Normal" else "Resolved"

            cursor.execute(
                """
                INSERT INTO diagnostic_tickets (motorcycle_id, user_id, component_id, issue_title, severity, status, description, recommended_action, resolved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    bike_id, current_user.id, component_id, ticket_title, severity, ticket_status,
                    f"User Symptoms: {problem_desc}\nDetected Fault: {ml_result.get('fault_label')}\n{rec_result.get('supporting_reason')}",
                    rec_result.get('recommended_action'),
                    datetime.now(timezone.utc) if ticket_status == "Resolved" else None
                )
            )
            ticket_id = cursor.lastrowid

            # Save Diagnostic Result
            cursor.execute(
                """
                INSERT INTO diagnostic_results (ticket_id, session_id, model_name, predicted_condition, confidence_score, anomaly_detected, raw_features_json, live_trace_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ticket_id, session_id, ml_result.get('model_used', 'Random Forest'),
                    condition, ml_result.get('confidence', 0.95),
                    len(telemetry.get('anomalies', [])) > 0,
                    json.dumps(ml_inputs),
                    json.dumps(ml_result.get('live_trace', []))
                )
            )

            # Update session status
            cursor.execute(
                "UPDATE diagnostic_sessions SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                (session_id,)
            )

        log_audit(current_user.id, "DIAGNOSTIC_COMPLETED", "diagnostic_tickets", ticket_id, {"condition": condition, "model": selected_model})
    finally:
        conn.close()

    response_payload = {
        "success": True,
        "ticket_id": ticket_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "component_diagnosed": component_name,
        "user_symptoms": problem_desc,
        "predicted_condition": rec_result.get("overall_condition"),
        "severity": rec_result.get("overall_priority"),
        "status_color": rec_result.get("status_color"),
        "urgent_summary": rec_result.get("urgent_summary"),
        "recommended_action": rec_result.get("recommended_action"),
        "supporting_reason": rec_result.get("supporting_reason"),
        "immediate_inspection_required": rec_result.get("immediate_inspection_required"),
        "whats_right": rec_result.get("whats_right", []),
        "whats_wrong": rec_result.get("whats_wrong", []),
        "primary_issue": rec_result.get("primary_issue"),
        "ml_engine": {
            "model_selected": ml_result.get("model_used"),
            "confidence_pct": ml_result.get("confidence_pct"),
            "probabilities": ml_result.get("probabilities"),
            "fault_label": ml_result.get("fault_label"),
            "remaining_pad_life_km": ml_result.get("remaining_life_km"),
            "pca_coordinates": ml_result.get("pca_coordinates"),
            "cluster_id": ml_result.get("cluster_id"),
            "feature_importance": ml_result.get("feature_importance"),
            "live_trace": ml_result.get("live_trace"),
            "scaling_math": ml_result.get("scaling_math", []),
            "pca_math": ml_result.get("pca_math", {}),
            "clustering_math": ml_result.get("clustering_math", {}),
            "algorithm_math": ml_result.get("algorithm_math", {})
        },
        "telemetry_snapshot": readings,
        "anomalies_detected": telemetry.get("anomalies", []),
        "all_detected_issues": rec_result.get("all_detected_issues", [])
    }
    return jsonify(response_payload)

@diagnostics_bp.route('/diagnostics/report/<int:ticket_id>', methods=['GET'])
@login_required
def view_report(ticket_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.*, r.result_id, r.model_name as ml_model_name, r.predicted_condition,
                       r.confidence_score, r.raw_features_json, r.live_trace_json,
                       m.registration_number, m.colour, m.manufacturing_year,
                       mm.name as bike_model_name, mfg.name as mfg_name, u.full_name, u.email
                FROM diagnostic_tickets t
                JOIN diagnostic_results r ON t.ticket_id = r.ticket_id
                JOIN motorcycles m ON t.motorcycle_id = m.motorcycle_id
                JOIN users u ON t.user_id = u.user_id
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE t.ticket_id = %s AND t.user_id = %s
                """,
                (ticket_id, current_user.id)
            )
            report = cursor.fetchone()
            if not report:
                flash("Diagnostic report not found or access denied.", "danger")
                return redirect(url_for('diagnostics.index'))

            # Parse JSON features and trace
            raw_features = json.loads(report['raw_features_json']) if report['raw_features_json'] else {}
            live_trace = json.loads(report['live_trace_json']) if report['live_trace_json'] else []
    finally:
        conn.close()

    return render_template(
        'diagnostics/report.html',
        report=report,
        raw_features=raw_features,
        live_trace=live_trace
    )

@diagnostics_bp.route('/api/diagnostics/ticket/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ('Open', 'Under Investigation', 'Awaiting Maintenance', 'Resolved', 'Reopened'):
        return jsonify({"error": "Invalid ticket status"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            resolved_at = datetime.now(timezone.utc) if new_status == 'Resolved' else None
            cursor.execute(
                """
                UPDATE diagnostic_tickets
                SET status = %s, resolved_at = %s, updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = %s AND user_id = %s
                """,
                (new_status, resolved_at, ticket_id, current_user.id)
            )
        log_audit(current_user.id, "UPDATE_TICKET_STATUS", "diagnostic_tickets", ticket_id, {"status": new_status})
        return jsonify({"success": True, "ticket_id": ticket_id, "status": new_status})
    finally:
        conn.close()

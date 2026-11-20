from typing import Dict, Any, Optional, List
from database.connection import get_db_connection

class MaintenanceRecommendationEngine:
    """
    Intelligent Maintenance Recommendation Layer.
    Synthesizes classical ML predictions, verified OEM technical specifications,
    sensor telemetry limits, component applicability, and maintenance intervals
    to generate actionable, model-specific mechanical advice.
    """

    @staticmethod
    def generate_recommendations(motorcycle_id: int, ml_result: Dict[str, Any],
                                 telemetry: Dict[str, Any],
                                 component_code: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db_connection()
        specs = {}
        applicability = {}
        try:
            with conn.cursor() as cursor:
                # 1. Fetch motorcycle verified specs
                cursor.execute(
                    """
                    SELECT m.*, mv.*, ms.*, mm.name as model_name, mfg.name as mfg_name
                    FROM motorcycles m
                    LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                    LEFT JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                    LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                    WHERE m.motorcycle_id = %s
                    """,
                    (motorcycle_id,)
                )
                specs = cursor.fetchone() or {}

                # 2. Fetch component applicability rules
                if specs.get("variant_id"):
                    cursor.execute(
                        """
                        SELECT c.component_code, mca.is_applicable, mca.display_name_override, mca.rule_condition
                        FROM model_component_applicability mca
                        JOIN component_catalogue c ON mca.component_id = c.component_id
                        WHERE mca.variant_id = %s
                        """,
                        (specs['variant_id'],)
                    )
                    for row in cursor.fetchall():
                        applicability[row['component_code']] = row
        finally:
            conn.close()

        readings = telemetry.get("readings", {})
        predicted_condition = ml_result.get("predicted_condition", "Normal")
        fault_label = ml_result.get("fault_label", "Nominal")
        confidence = ml_result.get("confidence", 0.95)
        remaining_km = ml_result.get("remaining_life_km", 5000.0)

        cooling = specs.get("cooling_type", "Air")
        drive = specs.get("final_drive_type", "Chain")
        brakes = specs.get("brake_type", "Dual Disc")
        oil_grade = specs.get("oil_grade", "15W-50 API SL")
        brake_fluid = specs.get("brake_fluid_type", "DOT 4")
        front_psi = specs.get("front_tyre_psi", 29)
        rear_psi = specs.get("rear_tyre_psi", 33)

        issues: List[Dict[str, Any]] = []

        # Check 1: Engine Temperature & Thermal System
        eng_temp = readings.get("ENG_TEMP", 85.0)
        temp_limit = 112.0 if "Air" in cooling else 105.0
        if eng_temp > temp_limit or fault_label == "Thermal_Overheating":
            issues.append({
                "component": "Engine Thermal System",
                "severity": "Critical" if eng_temp > 120.0 else "High",
                "condition": "Urgent Attention Required" if eng_temp > 120.0 else "Attention Required",
                "reading": f"{eng_temp} °C (Limit: {temp_limit} °C)",
                "summary": f"Engine cylinder temperature elevated to {eng_temp} °C under {cooling}-cooled architecture.",
                "reason": (
                    f"Sensor detects abnormal heat build-up exceeding the maximum operational tolerance of {temp_limit} °C. "
                    + (f"Check coolant reservoir level and radiator fan operation." if "Liquid" in cooling
                       else f"Ensure cylinder air cooling fins are free of road grime and verify {oil_grade} engine oil level.")
                ),
                "action": "Halt vehicle operation to avoid cylinder seizure or valve guide distortion. Inspect oil level and cooling system.",
                "immediate_inspection": True
            })

        # Check 2: Braking Friction Material
        pad_thickness = readings.get("BRAKE_PAD_WEAR", 4.5)
        if pad_thickness < 2.0 or fault_label == "Brake_Thinning":
            pad_name = "Brake Pads" if "Disc" in brakes else "Brake Shoes"
            issues.append({
                "component": f"Braking Friction Lining ({pad_name})",
                "severity": "Critical" if pad_thickness < 1.5 else "High",
                "condition": "Urgent Attention Required",
                "reading": f"{pad_thickness} mm (Minimum Limit: 2.0 mm)",
                "summary": f"Braking friction material thinned to {pad_thickness} mm, approaching safety threshold.",
                "reason": (
                    f"Friction lining thickness has worn below the OEM safety limit. "
                    f"Estimated remaining pad life is {remaining_km:.0f} km. Running below 1.5mm causes metal-to-metal contact with rotor/drum."
                ),
                "action": f"Replace {pad_name} immediately with genuine OEM or certified sintered compound. Inspect rotor/drum for scoring.",
                "immediate_inspection": True
            })

        # Check 3: Battery & Electrical Voltage
        bat_volt = readings.get("BAT_VOLT", 14.1)
        if bat_volt < 12.0 or bat_volt > 15.0 or fault_label == "Battery_Degraded":
            issues.append({
                "component": "Electrical Charging System",
                "severity": "High" if bat_volt < 11.5 else "Medium",
                "condition": "Attention Required" if bat_volt >= 11.5 else "Urgent Attention Required",
                "reading": f"{bat_volt} V (Nominal: 13.8 - 14.5 V)",
                "summary": f"System charging voltage out of spec at {bat_volt} V.",
                "reason": (
                    f"Alternator/regulator output is {bat_volt} V. "
                    + ("Voltage under 12.0V indicates charging failure, stator coil short, or weak battery cell." if bat_volt < 12.0
                       else "Voltage over 15.0V indicates faulty regulator/rectifier, risking ECU and battery damage.")
                ),
                "action": "Check stator resistance, regulator/rectifier diode connections, and battery terminal tightness.",
                "immediate_inspection": False
            })

        # Check 4: Vibration & Chassis Harmonics
        vib_level = readings.get("VIB_LEVEL", 2.8)
        if vib_level > 6.0 or fault_label == "Vibration_Excessive":
            issues.append({
                "component": "Chassis & Engine Mounts",
                "severity": "High",
                "condition": "Attention Required",
                "reading": f"{vib_level} mm/s RMS (Normal: 1.5 - 5.5 mm/s)",
                "summary": f"Abnormal harmonic vibration detected ({vib_level} mm/s RMS).",
                "reason": "Vibrational signature indicates possible loose engine hanger bolts, unbalanced wheels, or uneven cylinder firing.",
                "action": "Torque all engine mounting bolts and chassis fasteners to manufacturer specified values.",
                "immediate_inspection": False
            })

        # Check 5: Drive Chain Tension (Only if chain drive is applicable!)
        if drive == "Chain":
            chain_slack = readings.get("CHAIN_SLACK", 27.0)
            if chain_slack > 38.0 or fault_label == "Chain_Loose":
                issues.append({
                    "component": "Drive Chain System",
                    "severity": "High" if chain_slack > 45.0 else "Medium",
                    "condition": "Attention Required" if chain_slack <= 45.0 else "Urgent Attention Required",
                    "reading": f"{chain_slack} mm (Recommended Slack: {specs.get('chain_slack_mm', '25-30 mm')})",
                    "summary": f"Drive chain slack has stretched to {chain_slack} mm.",
                    "reason": f"Excessive chain slack increases risk of chain slap against swingarm buffer or dangerous sprocket derailment.",
                    "action": f"Adjust rear axle chain tensioners to restore slack to {specs.get('chain_slack_mm', '25-30 mm')}. Clean and apply chain lube.",
                    "immediate_inspection": chain_slack > 45.0
                })

        # Check 6: Tyre Pressures
        tyre_front_val = readings.get("TYRE_PRES_FRONT", front_psi)
        tyre_rear_val = readings.get("TYRE_PRES_REAR", rear_psi)
        if abs(tyre_front_val - front_psi) > 4.0 or abs(tyre_rear_val - rear_psi) > 4.0:
            issues.append({
                "component": "Tyre Pressure & Contact Patch",
                "severity": "Medium",
                "condition": "Attention Required",
                "reading": f"Front: {tyre_front_val} PSI (Spec: {front_psi}), Rear: {tyre_rear_val} PSI (Spec: {rear_psi})",
                "summary": "Tyre inflation pressure deviates from cold specification.",
                "reason": "Incorrect inflation alters contact patch, compromises high-speed braking stability, and increases tyre tread wear.",
                "action": f"Adjust cold tyre pressures to Front: {front_psi} PSI, Rear: {rear_psi} PSI using a calibrated tyre pressure gauge.",
                "immediate_inspection": False
            })

        # Determine Primary Urgent Issue
        if issues:
            # Sort by severity: Critical > High > Medium > Low
            sev_weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            sorted_issues = sorted(issues, key=lambda x: sev_weights.get(x["severity"], 0), reverse=True)
            primary = sorted_issues[0]
            overall_condition = primary["condition"]
            overall_priority = primary["severity"]
            summary_message = primary["summary"]
            recommended_action = primary["action"]
            supporting_reason = primary["reason"]
            immediate_inspection = primary["immediate_inspection"]
        else:
            primary = None
            overall_condition = "Normal"
            overall_priority = "Low"
            summary_message = "All monitored motorcycle systems are operating within nominal manufacturer tolerances."
            recommended_action = f"Proceed with routine scheduled service at next {specs.get('service_interval_km', 5000)} km interval."
            supporting_reason = f"Engine, charging, braking, and drivetrain telemetry comply with {specs.get('model_name', 'motorcycle')} specifications."
            immediate_inspection = False

        status_color = "green"
        if overall_condition == "Attention Required":
            status_color = "yellow"
        elif overall_condition == "Urgent Attention Required":
            status_color = "red"

        return {
            "motorcycle_id": motorcycle_id,
            "overall_condition": overall_condition,
            "overall_priority": overall_priority,
            "status_color": status_color,
            "urgent_summary": summary_message,
            "recommended_action": recommended_action,
            "supporting_reason": supporting_reason,
            "immediate_inspection_required": immediate_inspection,
            "primary_issue": primary,
            "all_detected_issues": issues,
            "ml_model_used": ml_result.get("model_used", "Random Forest"),
            "ml_confidence_pct": ml_result.get("confidence_pct", 95.0),
            "estimated_pad_rul_km": remaining_km,
            "service_interval_km": specs.get("service_interval_km", 5000)
        }

import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from modules.sensor.base_provider import BaseSensorProvider
from database.connection import get_db_connection

class SimulatedSensorProvider(BaseSensorProvider):
    """
    Stage 1 Physics-Aware Simulated Motorcycle Telemetry Provider.
    Generates dynamic, correlated sensor signals reflecting normal, abnormal,
    and severe fault operating profiles under 3 selectable intensities.
    """

    def __init__(self):
        self._step_counter = 0

    def is_hardware(self) -> bool:
        return False

    def get_provider_status(self) -> Dict[str, Any]:
        return {
            "mode": "SIMULATOR",
            "is_hardware": False,
            "connected": True,
            "sampling_active": True,
            "version": "1.2.0-sim",
            "message": "Physics simulator active. Generating dynamic vehicle telemetry."
        }

    def get_telemetry_packet(self, motorcycle_id: int, variant_specs: Optional[Dict[str, Any]] = None,
                             intensity: str = "Regular") -> Dict[str, Any]:
        self._step_counter += 1
        now = datetime.now(timezone.utc)
        iso_now = now.isoformat()

        # Extract vehicle specifications or use sensible defaults
        displacement = float(variant_specs.get("displacement_cc", 350.0)) if variant_specs else 350.0
        cooling = str(variant_specs.get("cooling_type", "Air")) if variant_specs else "Air"
        idle_rpm = int(variant_specs.get("idle_rpm", 1200)) if variant_specs else 1200
        drive_type = str(variant_specs.get("final_drive_type", "Chain")) if variant_specs else "Chain"
        front_psi_spec = int(variant_specs.get("front_tyre_psi", 29)) if variant_specs else 29
        rear_psi_spec = int(variant_specs.get("rear_tyre_psi", 33)) if variant_specs else 33
        cylinders = int(variant_specs.get("num_cylinders", 1)) if variant_specs else 1

        # Smooth cyclic sinusoidal drive-cycle simulation (idle -> cruising -> deceleration)
        t = (self._step_counter % 60) * (2 * math.pi / 60)
        cycle_intensity = (math.sin(t) + 1) / 2.0  # 0.0 (idle) to 1.0 (cruising)

        # Baseline engine speed and vehicle speed
        rpm_range = 3500 if displacement > 500 else 4500
        rpm = idle_rpm + (cycle_intensity * rpm_range) + random.gauss(0, 25)
        speed = (cycle_intensity * 75.0) + random.gauss(0, 1.2) if rpm > (idle_rpm + 200) else 0.0
        speed = max(0.0, speed)

        # Baseline cylinder head temperature: Air-cooled runs warmer than Liquid
        temp_base = 92.0 if "Air" in cooling else 84.0
        temp_rise = cycle_intensity * 12.0
        eng_temp = temp_base + temp_rise + random.gauss(0, 0.4)

        # Baseline battery charging voltage: 14.2V while running, 12.6V at idle
        bat_volt = (13.8 + (cycle_intensity * 0.4)) + random.gauss(0, 0.04)

        # Baseline vibration: Single cylinders vibrate more than multi-cylinders
        vib_base = 3.6 if cylinders == 1 else (2.4 if cylinders == 2 else 1.6)
        vib_level = vib_base + (cycle_intensity * 1.8) + random.gauss(0, 0.1)

        # Baseline tyre pressures
        tyre_front = front_psi_spec + (cycle_intensity * 1.2) + random.gauss(0, 0.1)
        tyre_rear = rear_psi_spec + (cycle_intensity * 1.5) + random.gauss(0, 0.1)

        # Component health defaults (Regular)
        brake_pad = 4.8 + random.gauss(0, 0.05)
        oil_quality = 88.0 + random.gauss(0, 0.5)
        chain_slack = 27.0 + random.gauss(0, 0.3)
        fuel_rate = 2.4 + (cycle_intensity * 2.8) + random.gauss(0, 0.1)

        anomalies: List[str] = []
        intensity_norm = intensity.capitalize()

        # Apply simulation intensity perturbations
        if intensity_norm == "Medium":
            # Induce transient thermal & voltage stress
            eng_temp += random.uniform(12.0, 18.0)  # ~105-110°C
            bat_volt -= random.uniform(0.6, 1.1)    # ~12.8V (weak charging)
            vib_level += random.uniform(1.8, 3.2)   # higher vibration
            brake_pad = max(2.2, brake_pad - 1.8)   # thinning pad (~3.0mm)
            oil_quality = max(55.0, oil_quality - 28.0) # degrading oil (~60%)
            chain_slack += random.uniform(8.0, 14.0)    # slack ~38mm
            tyre_front -= random.uniform(3.0, 5.0)      # slightly soft tyre

            if eng_temp > 105.0:
                anomalies.append("ENG_TEMP")
            if bat_volt < 13.0:
                anomalies.append("BAT_VOLT")
            if chain_slack > 35.0 and drive_type == "Chain":
                anomalies.append("CHAIN_SLACK")
            if brake_pad < 3.0:
                anomalies.append("BRAKE_PAD_WEAR")

        elif intensity_norm == "Intense":
            # Induce severe mechanical/thermal failure states
            eng_temp += random.uniform(28.0, 36.0)   # Overheating: 118-128°C!
            bat_volt = random.uniform(10.8, 11.5)    # Alternator diode breakdown: <11.5V!
            vib_level += random.uniform(4.5, 6.5)    # Severe resonance / mount tear: 8-11 mm/s!
            brake_pad = random.uniform(0.9, 1.4)     # Critical pad wear: <1.5mm!
            oil_quality = random.uniform(18.0, 32.0) # Acidity & viscosity collapse: <35%!
            chain_slack = random.uniform(44.0, 56.0) # Loose jumping chain: >45mm!
            tyre_rear = rear_psi_spec - random.uniform(11.0, 16.0) # Severe puncture/loss
            fuel_rate += random.uniform(3.0, 4.5)    # Inefficient combustion

            anomalies.extend(["ENG_TEMP", "BAT_VOLT", "VIB_LEVEL", "BRAKE_PAD_WEAR", "OIL_QUALITY", "TYRE_PRES_REAR"])
            if drive_type == "Chain":
                anomalies.append("CHAIN_SLACK")

        readings = {
            "ENG_TEMP": round(eng_temp, 1),
            "ENG_RPM": round(max(0.0, rpm), 0),
            "BAT_VOLT": round(bat_volt, 2),
            "VIB_LEVEL": round(max(0.2, vib_level), 2),
            "VEH_SPEED": round(speed, 1),
            "TYRE_PRES_FRONT": round(tyre_front, 1),
            "TYRE_PRES_REAR": round(tyre_rear, 1),
            "BRAKE_PAD_WEAR": round(max(0.5, brake_pad), 2),
            "OIL_QUALITY": round(min(100.0, max(5.0, oil_quality)), 1),
            "CHAIN_SLACK": round(chain_slack, 1) if drive_type == "Chain" else 0.0,
            "FUEL_RATE": round(max(0.5, fuel_rate), 2)
        }

        # Determine overall packet status
        status = "ONLINE"
        if len(anomalies) >= 3 or intensity_norm == "Intense":
            status = "CRITICAL_FAULT"
        elif len(anomalies) > 0 or intensity_norm == "Medium":
            status = "ATTENTION_REQUIRED"

        return {
            "motorcycle_id": motorcycle_id,
            "timestamp": iso_now,
            "source_type": "SIMULATED",
            "intensity": intensity_norm,
            "status": status,
            "readings": readings,
            "anomalies": anomalies,
            "drive_type": drive_type
        }

    def persist_readings(self, motorcycle_id: int, packet: Dict[str, Any], session_id: Optional[str] = None):
        """Stores simulated sensor telemetry in the sensor_readings table with source tag."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get sensor ID mapping
                cursor.execute("SELECT sensor_id, sensor_code FROM sensor_definitions")
                sensor_id_map = {row['sensor_code']: row['sensor_id'] for row in cursor.fetchall()}

                readings = packet.get("readings", {})
                anomalies = set(packet.get("anomalies", []))
                source = packet.get("source_type", "SIMULATED")

                insert_values = []
                for scode, val in readings.items():
                    if scode in sensor_id_map:
                        sid = sensor_id_map[scode]
                        is_anom = scode in anomalies
                        insert_values.append((motorcycle_id, sid, float(val), source, is_anom, session_id))

                if insert_values:
                    cursor.executemany(
                        """
                        INSERT INTO sensor_readings (motorcycle_id, sensor_id, value, source_type, is_anomaly, session_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        insert_values
                    )
        finally:
            conn.close()

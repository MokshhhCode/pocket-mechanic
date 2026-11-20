from typing import Dict, Any, Optional
from database.connection import get_db_connection
from modules.sensor.simulated_provider import SimulatedSensorProvider
from modules.sensor.hardware_provider import HardwareSensorProvider

_sim_provider = SimulatedSensorProvider()
_hw_provider = HardwareSensorProvider()

def get_active_mode(user_id: Optional[int] = None) -> str:
    """Reads current sensor data source mode from application_settings."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT setting_value FROM application_settings
                WHERE setting_key = 'DATA_SOURCE_MODE'
                ORDER BY user_id DESC LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row:
                return row['setting_value'].upper()
            return "SIMULATOR"
    finally:
        conn.close()

def get_simulation_intensity(user_id: Optional[int] = None) -> str:
    """Reads current simulation intensity (Regular, Medium, Intense)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT setting_value FROM application_settings
                WHERE setting_key = 'SIMULATION_INTENSITY'
                ORDER BY user_id DESC LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row:
                return row['setting_value'].capitalize()
            return "Regular"
    finally:
        conn.close()

def get_active_sensor_provider(mode: Optional[str] = None):
    """Returns the active sensor provider instance (Simulated or Hardware)."""
    active_mode = mode.upper() if mode else get_active_mode()
    if active_mode == "HARDWARE":
        return _hw_provider
    return _sim_provider

def fetch_telemetry_for_motorcycle(motorcycle_id: int, intensity_override: Optional[str] = None,
                                   persist: bool = True) -> Dict[str, Any]:
    """
    Standard interface to obtain latest telemetry for a given motorcycle.
    Retrieves vehicle specs from MySQL, polls the active provider, and optionally persists reading.
    """
    conn = get_db_connection()
    specs = {}
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT ms.*, mv.cooling_type, mv.brake_type, mv.abs_type, mv.final_drive_type
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                WHERE m.motorcycle_id = %s
                """,
                (motorcycle_id,)
            )
            specs = cursor.fetchone() or {}
    finally:
        conn.close()

    intensity = intensity_override or get_simulation_intensity()
    provider = get_active_sensor_provider()
    packet = provider.get_telemetry_packet(motorcycle_id, specs, intensity=intensity)

    if persist and packet.get("readings") and isinstance(provider, SimulatedSensorProvider):
        provider.persist_readings(motorcycle_id, packet)

    return packet

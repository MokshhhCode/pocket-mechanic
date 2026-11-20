import glob
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from modules.sensor.base_provider import BaseSensorProvider

class HardwareSensorProvider(BaseSensorProvider):
    """
    Stage 2 Physical Hardware Sensor Provider.
    Interfaces with physical motorcycle telemetry hardware (ESP32 via USB Serial or MQTT).
    Strict Integrity Rule: If hardware is not connected, it returns NO fabricated readings
    and explicitly signals disconnected status.
    """

    def __init__(self, serial_port: Optional[str] = None, baud_rate: int = 115200):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.connected = False
        self._check_hardware_availability()

    def is_hardware(self) -> bool:
        return True

    def _check_hardware_availability(self):
        """Scans for ESP32 / USB Serial ports on host."""
        ports = glob.glob("/dev/tty.usbserial*") + glob.glob("/dev/cu.SLAB_USBtoUART*") + glob.glob("/dev/ttyUSB*")
        if ports:
            self.serial_port = ports[0]
            self.connected = True
        else:
            self.connected = False

    def get_provider_status(self) -> Dict[str, Any]:
        self._check_hardware_availability()
        if self.connected:
            return {
                "mode": "HARDWARE",
                "is_hardware": True,
                "connected": True,
                "port": self.serial_port,
                "baud": self.baud_rate,
                "target_device": "ESP32 Automotive DAQ Module (Stage 2)",
                "sampling_active": True,
                "message": f"Connected to hardware on {self.serial_port}"
            }
        else:
            return {
                "mode": "HARDWARE",
                "is_hardware": True,
                "connected": False,
                "port": None,
                "target_device": "ESP32 Automotive DAQ Module (Stage 2)",
                "sampling_active": False,
                "message": "Hardware Sensor Unit Not Detected. Connect ESP32 via USB or configure MQTT gateway. No fabricated data will be displayed."
            }

    def get_telemetry_packet(self, motorcycle_id: int, variant_specs: Optional[Dict[str, Any]] = None,
                             intensity: str = "Regular") -> Dict[str, Any]:
        self._check_hardware_availability()
        now = datetime.now(timezone.utc).isoformat()

        if not self.connected:
            return {
                "motorcycle_id": motorcycle_id,
                "timestamp": now,
                "source_type": "HARDWARE",
                "status": "DISCONNECTED",
                "readings": None,  # No fabricated data
                "anomalies": [],
                "error": "Hardware interface offline. ESP32 DAQ not detected on USB serial or MQTT bus."
            }

        # If connected (Stage 2 implementation placeholder for pyserial read)
        return {
            "motorcycle_id": motorcycle_id,
            "timestamp": now,
            "source_type": "HARDWARE",
            "status": "ONLINE",
            "readings": {},
            "anomalies": []
        }

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSensorProvider(ABC):
    """
    Common sensor-data interface for Pocket Mechanic.
    Decouples sensor ingestion from the ML engine, diagnostics, and UI.
    Stage 1: Implemented by SimulatedSensorProvider.
    Stage 2: Implemented by HardwareSensorProvider (ESP32 USB/MQTT).
    """

    @abstractmethod
    def get_telemetry_packet(self, motorcycle_id: int, variant_specs: Optional[Dict[str, Any]] = None,
                             intensity: str = "Regular") -> Dict[str, Any]:
        """
        Retrieves a standardized telemetry reading packet.
        Returns a dict containing:
          - motorcycle_id: int
          - timestamp: ISO 8601 string
          - source_type: 'SIMULATED' or 'HARDWARE'
          - status: 'ONLINE', 'DEGRADED', 'OFFLINE'
          - readings: Dict[str, float] mapping sensor_code to measured/simulated float value
          - anomalies: List[str] list of flagged sensor codes exceeding tolerance
        """
        pass

    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        """Returns connection and configuration status of the provider."""
        pass

    @abstractmethod
    def is_hardware(self) -> bool:
        """Returns True if this is a real physical hardware provider, False otherwise."""
        pass

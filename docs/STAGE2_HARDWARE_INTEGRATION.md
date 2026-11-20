# POCKET MECHANIC — Stage 2 Hardware Integration Specification
### ESP32 Automotive Telemetry Acquisition Unit (DAQ)

---

## 1. Stage 2 Hardware Overview

In Stage 2, physical sensor hardware replaces the Stage 1 `SimulatedSensorProvider` through the common `BaseSensorProvider` interface without modifying the ML engine, database, or UI.

```
+-------------------------------------------------------------+
|             MOTORCYCLE SENSORS (PHYSICAL HARNESS)           |
|                                                             |
|  - Engine Temp: DS18B20 / K-Type Thermocouple               |
|  - Vibration: MPU-6050 (3-Axis I2C Accelerometer)           |
|  - Battery Voltage: Precision 4:1 Resistor Divider          |
|  - Engine RPM: Inductive Spark Plug Wire Pickup / Opto      |
|  - Tyre Pressure: BLE TPMS Valve Stem Sensors               |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|               ESP32-WROOM-32 DAQ MICROCONTROLLER            |
|                                                             |
|  - ADC Sampling @ 10 Hz with Kalmar Filtering               |
|  - I2C Bus @ 400 kHz for Vibration RMS Computation          |
|  - Pulse Capture Timer for Crankshaft RPM                   |
|  - JSON Serialization Packetizer                            |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       | USB Serial (115200)   | WiFi MQTT (JSON)      |
       v                       v                       v
+-------------------------------------------------------------+
|                    POCKET MECHANIC BACKEND                  |
|                                                             |
|  `modules/sensor/hardware_provider.py`                      |
|  Inherits `BaseSensorProvider` -> Feeds ML Pipeline         |
+-------------------------------------------------------------+
```

---

## 2. Standard Hardware Telemetry JSON Packet

The ESP32 firmware transmits newline-delimited JSON packets over USB Serial at 115,200 baud or MQTT topic `pocketmechanic/telemetry`:

```json
{
  "device_id": "PM-ESP32-DAQ-01",
  "firmware": "v2.0.4-hw",
  "timestamp_ms": 1420950,
  "readings": {
    "ENG_TEMP": 89.2,
    "ENG_RPM": 3450,
    "BAT_VOLT": 14.18,
    "VIB_LEVEL": 3.12,
    "VEH_SPEED": 48.5,
    "TYRE_PRES_FRONT": 29.2,
    "TYRE_PRES_REAR": 33.1,
    "BRAKE_PAD_WEAR": 4.10,
    "OIL_QUALITY": 84.5,
    "CHAIN_SLACK": 28.0,
    "FUEL_RATE": 3.25
  },
  "sensor_health": {
    "temp_probe": "OK",
    "mpu6050": "OK",
    "voltage_adc": "OK",
    "rpm_pulse": "OK"
  }
}
```

---

## 3. Data Integrity & Disconnected Mode Behavior

When Hardware Sensor Mode is selected on the Developer Toolbar:
1. `HardwareSensorProvider` actively scans host serial ports (`/dev/tty.usbserial*`, `/dev/cu.SLAB_USBtoUART*`, `/dev/ttyUSB*`).
2. If no microcontroller is connected:
   - Status transitions to `DISCONNECTED`.
   - `readings` is set to `None`.
   - **Zero fabricated data** is fed into the ML engine or displayed on dashboards.
   - The UI surfaces a clear alert: *"Hardware sensor unit not detected on USB serial or MQTT bus."*

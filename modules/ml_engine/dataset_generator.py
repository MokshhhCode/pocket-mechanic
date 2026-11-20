"""
Pocket Mechanic: Synthetic Motorcycle Sensor Dataset Generator
Generates realistic multi-regime motorcycle operating telemetry data
reflecting verified physical parameters, component degradation mechanics,
and labelled fault states for classical Machine Learning training.
"""

import os
import random
import numpy as np
import pandas as pd

def generate_motorcycle_dataset(num_samples: int = 6000, random_seed: int = 42) -> str:
    np.random.seed(random_seed)
    random.seed(random_seed)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "synthetic_sensor_dataset.csv")

    records = []

    # Distribution of operating profiles:
    # 0: Nominal / Healthy (~60%)
    # 1: Thermal Overheating (~10%)
    # 2: Battery / Alternator Collapse (~8%)
    # 3: Severe Brake Pad Wear (~8%)
    # 4: Excessive Mechanical Vibration (~8%)
    # 5: Severe Chain Slack / Derailment Risk (~6%)

    classes = [
        ("Nominal", "Normal", "Low", 0.60),
        ("Thermal_Overheating", "Urgent Attention Required", "Critical", 0.10),
        ("Battery_Degraded", "Attention Required", "High", 0.08),
        ("Brake_Thinning", "Urgent Attention Required", "Critical", 0.08),
        ("Vibration_Excessive", "Attention Required", "High", 0.08),
        ("Chain_Loose", "Attention Required", "Medium", 0.06),
    ]

    for fault_label, condition_label, priority_label, proportion in classes:
        n_class = int(num_samples * proportion)
        for _ in range(n_class):
            odometer_km = random.randint(500, 65000)
            engine_hours = round(odometer_km / random.uniform(32.0, 48.0), 1)
            ambient_temp = round(random.uniform(18.0, 42.0), 1)

            # Normal baselines
            speed = round(random.uniform(0.0, 115.0), 1)
            rpm = round(1200 + (speed * 42.0) + random.gauss(0, 80), 0) if speed > 5 else round(random.uniform(1150, 1400), 0)
            rpm = min(11000.0, max(1000.0, rpm))

            eng_temp = round(82.0 + (rpm / 250.0) + (ambient_temp * 0.25) + random.gauss(0, 2.0), 1)
            bat_volt = round(14.1 + random.gauss(0, 0.15), 2) if rpm > 1800 else round(12.7 + random.gauss(0, 0.1), 2)
            vib_level = round(1.8 + (rpm / 2200.0) + random.gauss(0, 0.3), 2)
            front_psi = round(29.0 + random.gauss(0, 0.8), 1)
            rear_psi = round(33.0 + random.gauss(0, 0.9), 1)
            brake_pad = round(max(3.2, 5.5 - (odometer_km % 15000) / 4500.0 + random.gauss(0, 0.2)), 2)
            oil_quality = round(max(65.0, 100.0 - (odometer_km % 6000) / 100.0 + random.gauss(0, 2.0)), 1)
            chain_slack = round(26.0 + ((odometer_km % 2500) / 300.0) + random.gauss(0, 1.0), 1)
            fuel_rate = round(2.8 + (speed * 0.025) + random.gauss(0, 0.15), 2)

            # Target regression value: estimated remaining brake life in km
            remaining_brake_km = max(100.0, round((brake_pad - 1.0) * 3200.0 + random.gauss(0, 150), 0))

            # Apply specific fault regime characteristics
            if fault_label == "Thermal_Overheating":
                eng_temp = round(random.uniform(116.0, 134.0), 1)
                oil_quality = round(max(15.0, oil_quality - random.uniform(30.0, 50.0)), 1)
                fuel_rate = round(fuel_rate + random.uniform(1.2, 2.5), 2)
            elif fault_label == "Battery_Degraded":
                bat_volt = round(random.uniform(10.6, 11.7), 2)
            elif fault_label == "Brake_Thinning":
                brake_pad = round(random.uniform(0.6, 1.45), 2)
                remaining_brake_km = max(0.0, round((brake_pad - 0.5) * 800.0, 0))
            elif fault_label == "Vibration_Excessive":
                vib_level = round(random.uniform(7.8, 12.5), 2)
            elif fault_label == "Chain_Loose":
                chain_slack = round(random.uniform(43.0, 58.0), 1)

            records.append({
                "odometer_km": odometer_km,
                "engine_hours": engine_hours,
                "ambient_temp": ambient_temp,
                "vehicle_speed": speed,
                "engine_rpm": rpm,
                "engine_temp": eng_temp,
                "battery_voltage": bat_volt,
                "vibration_level": vib_level,
                "tyre_pressure_front": front_psi,
                "tyre_pressure_rear": rear_psi,
                "brake_pad_thickness": brake_pad,
                "oil_quality_index": oil_quality,
                "chain_slack_mm": chain_slack,
                "fuel_rate": fuel_rate,
                "fault_label": fault_label,
                "condition_label": condition_label,
                "priority_label": priority_label,
                "remaining_brake_life_km": remaining_brake_km
            })

    df = pd.DataFrame(records)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} synthetic motorcycle telemetry samples -> {csv_path}")
    return csv_path

if __name__ == "__main__":
    generate_motorcycle_dataset()

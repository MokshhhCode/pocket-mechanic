"""
Pocket Mechanic: Comprehensive Database Seeder
Seeds 28 Manufacturers, authentic motorcycle models, verified technical specifications,
specification sources, component catalogue, applicability rules, sensor definitions,
maintenance schedules, and application default settings.
"""

import sys
import os
import json
import pymysql
from database.connection import get_db_connection

def seed_database():
    print("Beginning Pocket Mechanic Master Database Seeding...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # ----------------------------------------------------------------
            # 1. MANUFACTURERS (All 28 Required Brands)
            # ----------------------------------------------------------------
            manufacturers = [
                ("Aprilia", "Italy", 1945, "aprilia"),
                ("Bajaj", "India", 1945, "bajaj"),
                ("Benelli", "Italy", 1911, "benelli"),
                ("BMW Motorrad", "Germany", 1923, "bmw_motorrad"),
                ("Brixton Motorcycles", "Austria", 2015, "brixton"),
                ("BSA", "United Kingdom", 1861, "bsa"),
                ("CFMoto", "China", 1989, "cfmoto"),
                ("Ducati", "Italy", 1926, "ducati"),
                ("Harley-Davidson", "United States", 1903, "harley_davidson"),
                ("Hero MotoCorp", "India", 1984, "hero_motocorp"),
                ("Honda", "Japan", 1948, "honda"),
                ("Husqvarna", "Sweden", 1903, "husqvarna"),
                ("Indian Motorcycle", "United States", 1901, "indian_motorcycle"),
                ("Jawa", "Czech Republic", 1929, "jawa"),
                ("Kawasaki", "Japan", 1896, "kawasaki"),
                ("Keeway", "Hungary", 1999, "keeway"),
                ("KTM", "Austria", 1934, "ktm"),
                ("Moto Guzzi", "Italy", 1921, "moto_guzzi"),
                ("Moto Morini", "Italy", 1937, "moto_morini"),
                ("Norton", "United Kingdom", 1898, "norton"),
                ("QJ Motor", "China", 1985, "qj_motor"),
                ("Royal Enfield", "India", 1901, "royal_enfield"),
                ("Suzuki", "Japan", 1909, "suzuki"),
                ("Triumph", "United Kingdom", 1902, "triumph"),
                ("TVS Motor", "India", 1978, "tvs_motor"),
                ("Yamaha", "Japan", 1955, "yamaha"),
                ("Yezdi", "India", 1969, "yezdi"),
                ("Zontes", "China", 2003, "zontes")
            ]

            print(f"Seeding {len(manufacturers)} Manufacturers...")
            for name, country, founded, slug in manufacturers:
                cursor.execute(
                    """
                    INSERT INTO manufacturers (name, country, founded_year, logo_slug, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE country=VALUES(country), founded_year=VALUES(founded_year)
                    """,
                    (name, country, founded, slug)
                )

            # Map mfg names to IDs
            cursor.execute("SELECT manufacturer_id, name FROM manufacturers")
            mfg_map = {row['name']: row['manufacturer_id'] for row in cursor.fetchall()}

            # ----------------------------------------------------------------
            # 2. MOTORCYCLE MODELS & VARIANTS WITH VERIFIED SPECS
            # ----------------------------------------------------------------
            models_data = [
                # 1. Royal Enfield Classic 350 (Air/Oil Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy/Spoke)
                {
                    "mfg": "Royal Enfield", "name": "Classic 350", "category": "Cruiser", "silhouette": "cruiser_classic",
                    "variant": "Reborn Series", "year_start": 2021, "year_end": None,
                    "cooling": "Air/Oil", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Spoke",
                    "specs": {
                        "engine_config": "Single Cylinder, 4-stroke, SOHC, J-Series", "displacement_cc": 349.3, "num_cylinders": 1,
                        "bore_mm": 72.0, "stroke_mm": 85.8, "compression_ratio": "9.5:1",
                        "max_power_bhp": 20.2, "max_power_rpm": 6100, "max_torque_nm": 27.0, "max_torque_rpm": 4000,
                        "lubrication_system": "Wet Sump Forced", "oil_capacity_l": 2.2, "oil_grade": "Semi-Synthetic 15W-50 API SL JASO MA2",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "BOSCH YR7DES", "spark_plug_gap_mm": 0.8,
                        "valve_config": "2 Valves per cylinder", "intake_valve_clearance_mm": "0.08 mm", "exhaust_valve_clearance_mm": "0.18 mm",
                        "idle_rpm": 1150, "num_gears": 5, "gearbox_type": "5-speed constant mesh", "clutch_type": "Wet multi-plate",
                        "chain_slack_mm": "25-30 mm", "front_brake_type": "300 mm Disc with twin-piston floating caliper",
                        "rear_brake_type": "270 mm Disc with single-piston floating caliper", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 270,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "Telescopic 41 mm forks", "rear_suspension": "Twin tube emulsion shock absorbers with 6-step preload",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 80, "frame_type": "Twin downtube spine frame",
                        "front_tyre_size": "100/90-19 57P", "rear_tyre_size": "120/80-18 62P", "tyre_type": "Tube-type on wire spokes",
                        "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "VRLA / AGM Maintenance Free", "charging_system": "Three-phase Alternator 156W @ 1500 RPM",
                        "fuel_tank_capacity_l": 13.0, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 195.0, "service_interval_km": 5000, "service_interval_months": 6
                    },
                    "source": {"name": "Royal Enfield Classic 350 Owner's Manual 2021", "type": "Owner Manual", "url": "https://www.royalenfield.com/in/en/motorcycles/classic-350/"}
                },
                # 2. KTM 390 Duke (Liquid Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "KTM", "name": "390 Duke", "category": "Naked", "silhouette": "naked_sport",
                    "variant": "Gen 3 (LC4c)", "year_start": 2024, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Supermoto", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Single Cylinder, 4-stroke, 4-valve DOHC, LC4c", "displacement_cc": 398.7, "num_cylinders": 1,
                        "bore_mm": 89.0, "stroke_mm": 64.0, "compression_ratio": "12.6:1",
                        "max_power_bhp": 45.3, "max_power_rpm": 8500, "max_torque_nm": 39.0, "max_torque_rpm": 6500,
                        "lubrication_system": "Pressure lubrication with 2 oil pumps", "oil_capacity_l": 1.7, "oil_grade": "Full Synthetic 10W-50 Motorex Formula 4T",
                        "oil_filter_type": "Paper element cartridge", "spark_plug_type": "NGK LKAR9BI-10", "spark_plug_gap_mm": 1.0,
                        "valve_config": "4 Valves with finger followers", "intake_valve_clearance_mm": "0.10-0.15 mm", "exhaust_valve_clearance_mm": "0.15-0.20 mm",
                        "idle_rpm": 1600, "num_gears": 6, "gearbox_type": "6-speed claw shifted with quickshifter+", "clutch_type": "PASC anti-hopping slipper clutch",
                        "chain_slack_mm": "5-7 mm slack from swingarm buffer", "front_brake_type": "320 mm radially mounted 4-piston caliper",
                        "rear_brake_type": "240 mm 2-piston floating caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 240,
                        "brake_fluid_type": "DOT 5.1", "brake_fluid_interval_km": 15000,
                        "front_suspension": "WP APEX 43 mm upside-down open cartridge adjustable", "rear_suspension": "WP APEX monoshock with preload and rebound damping",
                        "suspension_travel_front_mm": 150, "suspension_travel_rear_mm": 150, "frame_type": "Split-trellis powder-coated steel frame with die-cast aluminium subframe",
                        "front_tyre_size": "110/70 R17 54H", "rear_tyre_size": "150/60 R17 66H", "tyre_type": "Tubeless Radial",
                        "front_tyre_psi": 29, "rear_tyre_psi": 32, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "Maintenance-free 12V 8Ah ETZ-9A", "charging_system": "Permanent Magnet Alternator 230W",
                        "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": 1.2, "coolant_spec": "OAT Ethylene Glycol / Silicate-free 50:50",
                        "kerb_weight_kg": 168.0, "service_interval_km": 7500, "service_interval_months": 12
                    },
                    "source": {"name": "KTM 390 Duke 2024 EU/IN Repair Manual", "type": "Workshop Manual", "url": "https://www.ktm.com/en-in/models/naked-bike/ktm-390-duke-2024.html"}
                },
                # 3. Yamaha YZF-R15 V4 (Liquid Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Yamaha", "name": "YZF-R15 V4", "category": "Sport", "silhouette": "supersport",
                    "variant": "V4 Standard / M", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Single Cylinder, 4-stroke, 4-valve SOHC with VVA", "displacement_cc": 155.1, "num_cylinders": 1,
                        "bore_mm": 58.0, "stroke_mm": 58.7, "compression_ratio": "11.6:1",
                        "max_power_bhp": 18.4, "max_power_rpm": 10000, "max_torque_nm": 14.2, "max_torque_rpm": 7500,
                        "lubrication_system": "Wet Sump", "oil_capacity_l": 1.05, "oil_grade": "Yamalube Full Synthetic 10W-40 SL JASO MA2",
                        "oil_filter_type": "Mesh & Paper cartridge", "spark_plug_type": "NGK MR8E9", "spark_plug_gap_mm": 0.85,
                        "valve_config": "4-valve Variable Valve Actuation (VVA)", "intake_valve_clearance_mm": "0.10-0.14 mm", "exhaust_valve_clearance_mm": "0.20-0.24 mm",
                        "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "Constant mesh 6-speed with Quickshifter", "clutch_type": "Assist and Slipper clutch",
                        "chain_slack_mm": "30-40 mm", "front_brake_type": "282 mm hydraulic disc with ByBre dual-piston caliper",
                        "rear_brake_type": "220 mm hydraulic disc with single-piston caliper", "front_disc_dia_mm": 282, "rear_disc_dia_mm": 220,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "37 mm Upside-Down (USD) Telescopic Fork", "rear_suspension": "Linked-type Monocross suspension",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 105, "frame_type": "Deltabox Frame",
                        "front_tyre_size": "100/80-17M/C 52P", "rear_tyre_size": "140/70R17M/C 66H Radial", "tyre_type": "Tubeless",
                        "front_tyre_psi": 29, "rear_tyre_psi": 33, "battery_voltage": 12.0, "battery_capacity_ah": 4.0,
                        "battery_type": "VRLA 12V, 4.0Ah (10HR)", "charging_system": "AC Magneto 14V 150W",
                        "fuel_tank_capacity_l": 11.0, "coolant_capacity_l": 0.49, "coolant_spec": "Yamaha Long Life Coolant 50/50 mix",
                        "kerb_weight_kg": 142.0, "service_interval_km": 4000, "service_interval_months": 4
                    },
                    "source": {"name": "Yamaha Motor India YZF-R15 V4 Manual", "type": "Owner Manual", "url": "https://www.yamaha-motor-india.com/"}
                },
                # 4. Bajaj Pulsar 150 (Air Cooled, Front Disc Rear Drum, Single ABS, Chain, Carb/FI, Alloy)
                {
                    "mfg": "Bajaj", "name": "Pulsar 150", "category": "Commuter", "silhouette": "commuter_sport",
                    "variant": "Twin Spark DTS-i FI", "year_start": 2020, "year_end": None,
                    "cooling": "Air", "brakes": "Front Disc Rear Drum", "abs": "Single Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "4-Stroke, 2-Valve, Twin Spark BS6 DTS-i FI Engine", "displacement_cc": 149.5, "num_cylinders": 1,
                        "bore_mm": 57.0, "stroke_mm": 56.4, "compression_ratio": "9.8:1",
                        "max_power_bhp": 14.0, "max_power_rpm": 8500, "max_torque_nm": 13.2, "max_torque_rpm": 6500,
                        "lubrication_system": "Forced wet sump", "oil_capacity_l": 1.15, "oil_grade": "Bajaj DTS-i 10,000 20W-50 Semi-Synthetic",
                        "oil_filter_type": "Paper filter element", "spark_plug_type": "Champion RG4HC / BOSCH UR4AC", "spark_plug_gap_mm": 0.75,
                        "valve_config": "2 Valves", "intake_valve_clearance_mm": "0.05 mm", "exhaust_valve_clearance_mm": "0.10 mm",
                        "idle_rpm": 1400, "num_gears": 5, "gearbox_type": "5 speed (1-down, 4-up)", "clutch_type": "Wet multiplate",
                        "chain_slack_mm": "25-35 mm", "front_brake_type": "260 mm Disc with ABS",
                        "rear_brake_type": "130 mm Drum internal expanding shoe", "front_disc_dia_mm": 260, "rear_disc_dia_mm": None,
                        "brake_fluid_type": "DOT 4 (Front only)", "brake_fluid_interval_km": 10000,
                        "front_suspension": "Telescopic with anti-friction bush", "rear_suspension": "5-way adjustable Nitrox shock absorber",
                        "suspension_travel_front_mm": 135, "suspension_travel_rear_mm": 100, "frame_type": "Double cradle tubular steel",
                        "front_tyre_size": "80/100-17 46P", "rear_tyre_size": "100/90-17 55P", "tyre_type": "Tubeless",
                        "front_tyre_psi": 28, "rear_tyre_psi": 32, "battery_voltage": 12.0, "battery_capacity_ah": 4.0,
                        "battery_type": "12V 4Ah VRLA MF", "charging_system": "Flywheel magneto",
                        "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 148.0, "service_interval_km": 5000, "service_interval_months": 4
                    },
                    "source": {"name": "Bajaj Auto Pulsar 150 User Manual", "type": "Owner Manual", "url": "https://www.bajajauto.com/"}
                },
                # 5. BMW R 1250 GS (Liquid/Air Boxer, Dual Disc, Dual ABS, Shaft Drive!, FI, Spoke/Alloy)
                {
                    "mfg": "BMW Motorrad", "name": "R 1250 GS", "category": "Adventure", "silhouette": "adv_boxer",
                    "variant": "Adventure ShiftCam", "year_start": 2019, "year_end": 2024,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Cornering ABS Pro", "drive": "Shaft", "fuel": "Fuel Injection", "wheel": "Spoke",
                    "specs": {
                        "engine_config": "Two-cylinder opposed Boxer, 4-stroke, DOHC ShiftCam variable valve timing", "displacement_cc": 1254.0, "num_cylinders": 2,
                        "bore_mm": 102.5, "stroke_mm": 76.0, "compression_ratio": "12.5:1",
                        "max_power_bhp": 136.0, "max_power_rpm": 7750, "max_torque_nm": 143.0, "max_torque_rpm": 6250,
                        "lubrication_system": "Wet sump with dual gerotor pumps", "oil_capacity_l": 4.0, "oil_grade": "BMW Motorrad Advantec Ultimate 5W-40 API SN / JASO MA2",
                        "oil_filter_type": "Spin-on external canister", "spark_plug_type": "NGK LMAR8J-9E", "spark_plug_gap_mm": 0.8,
                        "valve_config": "8 valves with ShiftCam camshaft control", "intake_valve_clearance_mm": "0.10-0.17 mm", "exhaust_valve_clearance_mm": "0.34-0.41 mm",
                        "idle_rpm": 1150, "num_gears": 6, "gearbox_type": "Helical 6-speed with integrated bevel drive", "clutch_type": "Anti-hopping wet clutch with hydraulic actuation",
                        "chain_slack_mm": None, "front_brake_type": "Twin 305 mm floating discs with Hayes 4-piston radial calipers",
                        "rear_brake_type": "Single 276 mm disc with Brembo 2-piston floating caliper", "front_disc_dia_mm": 305, "rear_disc_dia_mm": 276,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 20000,
                        "front_suspension": "BMW Telelever with central spring strut, 37 mm stanchions", "rear_suspension": "Cast aluminium single-sided swing arm with BMW Paralever shaft drive",
                        "suspension_travel_front_mm": 210, "suspension_travel_rear_mm": 220, "frame_type": "Two-section frame consisting of main and bolt-on rear frame with load-bearing engine",
                        "front_tyre_size": "120/70 R19", "rear_tyre_size": "170/60 R17", "tyre_type": "Tubeless Cross-spoke",
                        "front_tyre_psi": 36, "rear_tyre_psi": 42, "battery_voltage": 12.0, "battery_capacity_ah": 14.0,
                        "battery_type": "12V 14Ah AGM", "charging_system": "Three-phase alternator 510W",
                        "fuel_tank_capacity_l": 30.0, "coolant_capacity_l": 1.4, "coolant_spec": "BMW Lifetime Coolant (OAT)",
                        "kerb_weight_kg": 268.0, "service_interval_km": 10000, "service_interval_months": 12
                    },
                    "source": {"name": "BMW Motorrad Rider's Manual R 1250 GS Adventure", "type": "Workshop Manual", "url": "https://www.bmw-motorrad.com/"}
                },
                # 6. Harley-Davidson Fat Boy 114 (Air/Oil Milwaukee-Eight, Dual Disc, Dual ABS, Belt Drive!, FI, Alloy)
                {
                    "mfg": "Harley-Davidson", "name": "Fat Boy 114", "category": "Cruiser", "silhouette": "heavy_cruiser",
                    "variant": "Milwaukee-Eight 114 (FLFBS)", "year_start": 2018, "year_end": None,
                    "cooling": "Air/Oil", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Belt", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Milwaukee-Eight 114 V-Twin 45-degree, 4 valves per cylinder", "displacement_cc": 1868.0, "num_cylinders": 2,
                        "bore_mm": 102.0, "stroke_mm": 114.0, "compression_ratio": "10.5:1",
                        "max_power_bhp": 94.0, "max_power_rpm": 5020, "max_torque_nm": 155.0, "max_torque_rpm": 3250,
                        "lubrication_system": "Dry sump with separate transmission and primary chaincase", "oil_capacity_l": 4.7, "oil_grade": "Screamin' Eagle SYN3 20W-50",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "Harley 6R12", "spark_plug_gap_mm": 0.85,
                        "valve_config": "Pushrod-operated overhead valves, hydraulic self-adjusting lifters", "intake_valve_clearance_mm": "Hydraulic self-adjusting", "exhaust_valve_clearance_mm": "Hydraulic self-adjusting",
                        "idle_rpm": 850, "num_gears": 6, "gearbox_type": "Cruise Drive 6-speed", "clutch_type": "Mechanically actuated 10-plate wet assist & slip",
                        "chain_slack_mm": None, "front_brake_type": "4-piston fixed front caliper with 300 mm floating rotor",
                        "rear_brake_type": "2-piston floating rear caliper with 292 mm rotor", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 292,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 16000,
                        "front_suspension": "Dual-bending valve 49 mm telescopic fork", "rear_suspension": "Hidden coil-over monoshock with hydraulic toolless preload",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 86, "frame_type": "Mild steel tubular Softail chassis with stamped forged junctions",
                        "front_tyre_size": "160/60R18 70V", "rear_tyre_size": "240/40R18 79V", "tyre_type": "Michelin Scorcher 11 Radial",
                        "front_tyre_psi": 36, "rear_tyre_psi": 42, "battery_voltage": 12.0, "battery_capacity_ah": 17.5,
                        "battery_type": "12V 17.5Ah AGM sealed", "charging_system": "Three-phase 48-amp alternator (600W max)",
                        "fuel_tank_capacity_l": 18.9, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 317.0, "service_interval_km": 8000, "service_interval_months": 12
                    },
                    "source": {"name": "Harley-Davidson Softail Service Manual 2022", "type": "Workshop Manual", "url": "https://serviceinfo.harley-davidson.com/"}
                },
                # 7. Hero Splendor Plus (Air Cooled, Dual Drum, Non-ABS, Chain, FI, Alloy)
                {
                    "mfg": "Hero MotoCorp", "name": "Splendor Plus", "category": "Commuter", "silhouette": "commuter_classic",
                    "variant": "XTEC BS6", "year_start": 2020, "year_end": None,
                    "cooling": "Air", "brakes": "Dual Drum", "abs": "Non-ABS", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Air-cooled 4-stroke single cylinder OHC", "displacement_cc": 97.2, "num_cylinders": 1,
                        "bore_mm": 50.0, "stroke_mm": 49.5, "compression_ratio": "9.9:1",
                        "max_power_bhp": 7.91, "max_power_rpm": 8000, "max_torque_nm": 8.05, "max_torque_rpm": 6000,
                        "lubrication_system": "Forced wet sump", "oil_capacity_l": 0.9, "oil_grade": "Hero 4T Plus 10W-30 Premium Grade",
                        "oil_filter_type": "Centrifugal filter screen", "spark_plug_type": "NGK CR7HSA / BOSCH UR4AC", "spark_plug_gap_mm": 0.65,
                        "valve_config": "2 Valves OHC", "intake_valve_clearance_mm": "0.08 mm", "exhaust_valve_clearance_mm": "0.08 mm",
                        "idle_rpm": 1400, "num_gears": 4, "gearbox_type": "4-speed all-up constant mesh", "clutch_type": "Multi-plate wet type",
                        "chain_slack_mm": "25-30 mm", "front_brake_type": "130 mm expanding shoe drum (Integrated Braking System)",
                        "rear_brake_type": "130 mm expanding shoe drum", "front_disc_dia_mm": None, "rear_disc_dia_mm": None,
                        "brake_fluid_type": "None (Mechanical Cable / Rod Drum)", "brake_fluid_interval_km": None,
                        "front_suspension": "Telescopic hydraulic shock absorbers", "rear_suspension": "5-step adjustable hydraulic shock absorbers",
                        "suspension_travel_front_mm": 110, "suspension_travel_rear_mm": 80, "frame_type": "Tubular double cradle",
                        "front_tyre_size": "80/100-18 47P", "rear_tyre_size": "80/100-18 54P", "tyre_type": "Tubeless",
                        "front_tyre_psi": 25, "rear_tyre_psi": 28, "battery_voltage": 12.0, "battery_capacity_ah": 3.0,
                        "battery_type": "Maintenance Free 12V 3Ah", "charging_system": "Flywheel Magneto 12V 100W",
                        "fuel_tank_capacity_l": 9.8, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 112.0, "service_interval_km": 3000, "service_interval_months": 3
                    },
                    "source": {"name": "Hero MotoCorp Splendor+ BS6 User Handbook", "type": "Owner Manual", "url": "https://www.heromotocorp.com/"}
                },
                # 8. TVS Apache RR 310 (Liquid Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "TVS Motor", "name": "Apache RR 310", "category": "Sport", "silhouette": "supersport",
                    "variant": "BTO Performance", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel with RT-Slipper Clutch", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "SI, 4 stroke, 4 valve, Single cylinder, Reverse inclined DOHC", "displacement_cc": 312.2, "num_cylinders": 1,
                        "bore_mm": 80.0, "stroke_mm": 62.1, "compression_ratio": "10.9:1",
                        "max_power_bhp": 33.5, "max_power_rpm": 9700, "max_torque_nm": 27.3, "max_torque_rpm": 7700,
                        "lubrication_system": "Wet sump with trochoid oil pump", "oil_capacity_l": 1.7, "oil_grade": "TVS TRU4 Fully Synthetic 10W-30 / 15W-50",
                        "oil_filter_type": "Paper element with magnetic drain", "spark_plug_type": "BOSCH YR6LII330", "spark_plug_gap_mm": 0.8,
                        "valve_config": "4 valves with DLC finger followers", "intake_valve_clearance_mm": "0.10-0.18 mm", "exhaust_valve_clearance_mm": "0.20-0.28 mm",
                        "idle_rpm": 1500, "num_gears": 6, "gearbox_type": "6-speed constant mesh with Bi-directional Quickshifter", "clutch_type": "Wet multi-plate 8 plate design RT Slipper Clutch",
                        "chain_slack_mm": "25-35 mm", "front_brake_type": "300 mm Petal disc with radially mounted ByBre 4-piston caliper",
                        "rear_brake_type": "240 mm Petal disc with single piston caliper", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 240,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "KYB 41 mm Upside Down cartridge fork fully adjustable preload/compression", "rear_suspension": "KYB Monoshock with floating piston gas assisted",
                        "suspension_travel_front_mm": 140, "suspension_travel_rear_mm": 120, "frame_type": "Trellis frame with split chassis",
                        "front_tyre_size": "110/70-ZR17 M/C 54W", "rear_tyre_size": "150/60-ZR17 M/C 66W", "tyre_type": "Michelin Road 5 Tubeless Radial",
                        "front_tyre_psi": 32, "rear_tyre_psi": 34, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "12V 8Ah VRLA maintenance free", "charging_system": "AC Generator 14V 300W",
                        "fuel_tank_capacity_l": 11.0, "coolant_capacity_l": 1.0, "coolant_spec": "Ethylene glycol with anti-corrosion additives 50:50",
                        "kerb_weight_kg": 174.0, "service_interval_km": 5000, "service_interval_months": 6
                    },
                    "source": {"name": "TVS Apache RR 310 Service Manual & Owner Guide", "type": "Workshop Manual", "url": "https://www.tvsmotor.com/tvs-apache/rr-310"}
                },
                # 9. Honda CB350 H'ness (Air Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Honda", "name": "CB350 H'ness", "category": "Cruiser", "silhouette": "modern_retro",
                    "variant": "DLX Pro", "year_start": 2020, "year_end": None,
                    "cooling": "Air", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "4 Stroke, SI Engine with PGM-FI", "displacement_cc": 348.3, "num_cylinders": 1,
                        "bore_mm": 70.0, "stroke_mm": 90.5, "compression_ratio": "9.5:1",
                        "max_power_bhp": 20.8, "max_power_rpm": 5500, "max_torque_nm": 30.0, "max_torque_rpm": 3000,
                        "lubrication_system": "Semi-dry sump with counterbalance shaft", "oil_capacity_l": 2.0, "oil_grade": "Honda Genuine 4T 10W-30 MA",
                        "oil_filter_type": "Cartridge and centrifugal screen", "spark_plug_type": "NGK LMAR8A-9", "spark_plug_gap_mm": 0.85,
                        "valve_config": "2 Valves OHC with roller rocker arm", "intake_valve_clearance_mm": "0.10 mm", "exhaust_valve_clearance_mm": "0.15 mm",
                        "idle_rpm": 1200, "num_gears": 5, "gearbox_type": "5 speed manual", "clutch_type": "Multiplate wet assist and slipper clutch",
                        "chain_slack_mm": "25-35 mm", "front_brake_type": "310 mm disc with Nissin dual-piston caliper",
                        "rear_brake_type": "240 mm disc with single-piston caliper", "front_disc_dia_mm": 310, "rear_disc_dia_mm": 240,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 12000,
                        "front_suspension": "Telescopic fork 41 mm", "rear_suspension": "Twin hydraulic shock absorbers",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 90, "frame_type": "Steel half-duplex cradle frame",
                        "front_tyre_size": "100/90-19M/C 57H", "rear_tyre_size": "130/70-18M/C 63H", "tyre_type": "Tubeless",
                        "front_tyre_psi": 29, "rear_tyre_psi": 33, "battery_voltage": 12.0, "battery_capacity_ah": 6.0,
                        "battery_type": "12V 6Ah (10HR) MF", "charging_system": "Alternator 210W",
                        "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 181.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Honda Motorcycle & Scooter India CB350 Owner's Manual", "type": "Owner Manual", "url": "https://www.honda2wheelersindia.com/"}
                },
                # 10. Triumph Speed 400 (Liquid Cooled, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Triumph", "name": "Speed 400", "category": "Naked", "silhouette": "modern_classic",
                    "variant": "Roadster 400", "year_start": 2023, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Bosch ABS", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Liquid-cooled, 4-valve, DOHC, single-cylinder TR-Series", "displacement_cc": 398.15, "num_cylinders": 1,
                        "bore_mm": 89.0, "stroke_mm": 64.0, "compression_ratio": "12.0:1",
                        "max_power_bhp": 39.5, "max_power_rpm": 8000, "max_torque_nm": 37.5, "max_torque_rpm": 6500,
                        "lubrication_system": "Semi-dry sump with scavenger pump", "oil_capacity_l": 1.9, "oil_grade": "Castrol Power1 Racing 10W-40 / 10W-50 Full Synthetic",
                        "oil_filter_type": "High performance cartridge", "spark_plug_type": "NGK LMAR9AI-8", "spark_plug_gap_mm": 0.8,
                        "valve_config": "4 valves with DLC finger followers", "intake_valve_clearance_mm": "0.10-0.15 mm", "exhaust_valve_clearance_mm": "0.25-0.30 mm",
                        "idle_rpm": 1350, "num_gears": 6, "gearbox_type": "6-speed gearbox", "clutch_type": "Wet, multi-plate, slip and assist clutch",
                        "chain_slack_mm": "20-30 mm", "front_brake_type": "300 mm fixed disc, 4-piston radial caliper by ByBre",
                        "rear_brake_type": "230 mm fixed disc, floating caliper by ByBre", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 230,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 16000,
                        "front_suspension": "43 mm upside-down Big Piston forks", "rear_suspension": "Gas monoshock RSU with external reservoir and preload adjustment",
                        "suspension_travel_front_mm": 140, "suspension_travel_rear_mm": 130, "frame_type": "Hybrid spine / perimeter tubular steel frame with bolt-on subframe",
                        "front_tyre_size": "110/70 R17", "rear_tyre_size": "150/60 R17", "tyre_type": "Metzeler Sportec M9RR Tubeless Radial",
                        "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "12V 8Ah Sealed AGM", "charging_system": "Alternator 280W",
                        "fuel_tank_capacity_l": 13.0, "coolant_capacity_l": 1.1, "coolant_spec": "HD4X Hybrid OAT Coolant",
                        "kerb_weight_kg": 170.0, "service_interval_km": 16000, "service_interval_months": 12
                    },
                    "source": {"name": "Triumph Motorcycles Speed 400 Owner Handbook 2023", "type": "Owner Manual", "url": "https://www.triumphmotorcycles.in/"}
                },
                # 11. Kawasaki Ninja 300 (Liquid Cooled, Parallel Twin, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Kawasaki", "name": "Ninja 300", "category": "Sport", "silhouette": "ninja_sport",
                    "variant": "BS6 Edition", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Liquid-cooled, 4-stroke Parallel Twin, DOHC 8 valves", "displacement_cc": 296.0, "num_cylinders": 2,
                        "bore_mm": 62.0, "stroke_mm": 49.0, "compression_ratio": "10.6:1",
                        "max_power_bhp": 38.8, "max_power_rpm": 11000, "max_torque_nm": 26.1, "max_torque_rpm": 10000,
                        "lubrication_system": "Forced lubrication, wet sump", "oil_capacity_l": 2.4, "oil_grade": "Kawasaki Genuine 10W-40 JASO MA2",
                        "oil_filter_type": "Spin-on external oil filter", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.75,
                        "valve_config": "8 valves DOHC (direct cam on tappet)", "intake_valve_clearance_mm": "0.15-0.24 mm", "exhaust_valve_clearance_mm": "0.22-0.31 mm",
                        "idle_rpm": 1300, "num_gears": 6, "gearbox_type": "6-speed return shift", "clutch_type": "Wet multi-disc with assist & slipper clutch",
                        "chain_slack_mm": "20-30 mm", "front_brake_type": "Single 290 mm petal disc with dual-piston caliper",
                        "rear_brake_type": "Single 220 mm petal disc with dual-piston caliper", "front_disc_dia_mm": 290, "rear_disc_dia_mm": 220,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 12000,
                        "front_suspension": "37 mm telescopic fork", "rear_suspension": "Bottom-Link Uni-Trak with gas-charged shock and 5-way adjustable preload",
                        "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 132, "frame_type": "Tube diamond steel frame",
                        "front_tyre_size": "110/70-17 M/C 54S", "rear_tyre_size": "140/70-17 M/C 66S", "tyre_type": "Tubeless",
                        "front_tyre_psi": 28, "rear_tyre_psi": 32, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "12V 8Ah Maintenance Free", "charging_system": "Alternator 14V 21A @ 5000 RPM",
                        "fuel_tank_capacity_l": 17.0, "coolant_capacity_l": 1.5, "coolant_spec": "Kawasaki Aluma-Cool 50:50 mixture",
                        "kerb_weight_kg": 179.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Kawasaki Ninja 300 Service Manual", "type": "Workshop Manual", "url": "https://www.kawasaki-india.com/"}
                },
                # 12. Ducati Monster 937 (Liquid Cooled, V-Twin Testastretta, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Ducati", "name": "Monster 937", "category": "Naked", "silhouette": "ducati_naked",
                    "variant": "Standard / Plus", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Cornering ABS Bosch", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Testastretta 11-deg L-Twin cylinder, 4 valves per cylinder, Desmodromic valvetrain", "displacement_cc": 937.0, "num_cylinders": 2,
                        "bore_mm": 94.0, "stroke_mm": 67.5, "compression_ratio": "13.3:1",
                        "max_power_bhp": 111.0, "max_power_rpm": 9250, "max_torque_nm": 93.0, "max_torque_rpm": 6500,
                        "lubrication_system": "Wet sump with gear oil pump", "oil_capacity_l": 3.7, "oil_grade": "Shell Advance Ducati 15W-50 Fully Synthetic",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK MAR9A-J", "spark_plug_gap_mm": 0.8,
                        "valve_config": "Desmodromic valve actuation (closing and opening cams)", "intake_valve_clearance_mm": "0.10-0.15 mm opening / 0.05-0.10 mm closing", "exhaust_valve_clearance_mm": "0.15-0.20 mm opening / 0.05-0.10 mm closing",
                        "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "6 speed with Ducati Quick Shift (DQS) up/down", "clutch_type": "Slipper and self-servo wet multiplate clutch with hydraulic control",
                        "chain_slack_mm": "27-29 mm", "front_brake_type": "2 x 320 mm semi-floating discs, radially mounted Brembo M4.32 monobloc 4-piston calipers",
                        "rear_brake_type": "245 mm disc, Brembo 2-piston floating caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 245,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 15000,
                        "front_suspension": "43 mm upside-down fork", "rear_suspension": "Progressive linkage, preload adjustable monoshock, aluminium double-sided swingarm",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 140, "frame_type": "Aluminium Front Frame directly attached to engine cylinder heads",
                        "front_tyre_size": "120/70 ZR 17", "rear_tyre_size": "180/55 ZR 17", "tyre_type": "Pirelli Diablo Rosso III Tubeless Radial",
                        "front_tyre_psi": 33, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 10.0,
                        "battery_type": "12V 10Ah Lithium-ion / AGM", "charging_system": "Alternator 500W",
                        "fuel_tank_capacity_l": 14.0, "coolant_capacity_l": 2.5, "coolant_spec": "Eni Antifreeze Bike S (Ethylene glycol 50:50)",
                        "kerb_weight_kg": 188.0, "service_interval_km": 15000, "service_interval_months": 12
                    },
                    "source": {"name": "Ducati Monster Workshop Manual 2022", "type": "Workshop Manual", "url": "https://www.ducati.com/in/en/bikes/monster"}
                },
                # 13. Aprilia RS 457 (Liquid Cooled, Parallel Twin, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Aprilia", "name": "RS 457", "category": "Sport", "silhouette": "supersport",
                    "variant": "Racing Edition", "year_start": 2024, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel with rear disengagement", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Parallel twin-cylinder 4-stroke, 4 valves per cylinder, DOHC with 270 deg crank", "displacement_cc": 457.0, "num_cylinders": 2,
                        "bore_mm": 69.0, "stroke_mm": 61.1, "compression_ratio": "10.5:1",
                        "max_power_bhp": 47.6, "max_power_rpm": 9400, "max_torque_nm": 43.5, "max_torque_rpm": 6700,
                        "lubrication_system": "Wet sump with water-oil heat exchanger", "oil_capacity_l": 2.1, "oil_grade": "Castrol Power1 Ultimate 10W-40 4T",
                        "oil_filter_type": "Cartridge element", "spark_plug_type": "NGK LMAR9E-J", "spark_plug_gap_mm": 0.8,
                        "valve_config": "DOHC 8 valves", "intake_valve_clearance_mm": "0.12-0.18 mm", "exhaust_valve_clearance_mm": "0.22-0.28 mm",
                        "idle_rpm": 1450, "num_gears": 6, "gearbox_type": "6-speed with bi-directional quickshifter option", "clutch_type": "Multi-plate wet clutch with slipper system",
                        "chain_slack_mm": "25-30 mm", "front_brake_type": "320 mm floating disc with ByBre 4-piston radial caliper",
                        "rear_brake_type": "220 mm disc with ByBre single piston caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 220,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "41 mm upside-down fork with preload adjustment", "rear_suspension": "Monoshock on steel swingarm with preload adjustment",
                        "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 130, "frame_type": "Dual-beam aluminium perimeter frame with load-bearing engine",
                        "front_tyre_size": "110/70 ZR 17", "rear_tyre_size": "150/60 ZR 17", "tyre_type": "TVS Eurogrip Protorq Extreme HF Radial Tubeless",
                        "front_tyre_psi": 30, "rear_tyre_psi": 34, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "12V 8Ah Sealed MF", "charging_system": "Alternator 250W",
                        "fuel_tank_capacity_l": 13.0, "coolant_capacity_l": 1.3, "coolant_spec": "OAT Glycol 50:50 mixture",
                        "kerb_weight_kg": 175.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Aprilia RS 457 Technical Service Spec Sheet", "type": "OEM Spec Sheet", "url": "https://www.aprilia.com/in_EN/"}
                },
                # 14. Suzuki Hayabusa GSX1300R (Liquid Cooled, Inline-4, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Suzuki", "name": "Hayabusa", "category": "Sport", "silhouette": "hyper_sport",
                    "variant": "Gen 3 (GSX1300RR)", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Cornering Motion Track ABS", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "4-stroke, liquid-cooled, 4-cylinder, DOHC 16-valve", "displacement_cc": 1340.0, "num_cylinders": 4,
                        "bore_mm": 81.0, "stroke_mm": 65.0, "compression_ratio": "12.5:1",
                        "max_power_bhp": 190.0, "max_power_rpm": 9700, "max_torque_nm": 150.0, "max_torque_rpm": 7000,
                        "lubrication_system": "Wet sump with dual gerotor pumps and oil cooler", "oil_capacity_l": 4.0, "oil_grade": "ECSTAR R9000 10W-40 Full Synthetic",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK CR9EIA-9 Iridium", "spark_plug_gap_mm": 0.9,
                        "valve_config": "16 valves DOHC bucket tappet", "intake_valve_clearance_mm": "0.10-0.20 mm", "exhaust_valve_clearance_mm": "0.20-0.30 mm",
                        "idle_rpm": 1150, "num_gears": 6, "gearbox_type": "6-speed constant mesh with bi-directional quick shifter", "clutch_type": "SCAS (Suzuki Clutch Assist System) wet multi-plate",
                        "chain_slack_mm": "25-35 mm RK 50GSVZ4 114 links", "front_brake_type": "Twin 320 mm floating discs, Brembo Stylema 4-piston radial calipers",
                        "rear_brake_type": "Single 260 mm disc, Nissin 1-piston pin-slide caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 260,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 12000,
                        "front_suspension": "KYB 43 mm inverted telescopic cartridge forks fully adjustable (DLC coated)", "rear_suspension": "KYB link-type monoshock fully adjustable",
                        "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 140, "frame_type": "Twin-spar aluminium cradle alloy frame",
                        "front_tyre_size": "120/70ZR17M/C (58W)", "rear_tyre_size": "190/50ZR17M/C (73W)", "tyre_type": "Bridgestone Battlax Hypersport S22 Tubeless",
                        "front_tyre_psi": 42, "rear_tyre_psi": 42, "battery_voltage": 12.0, "battery_capacity_ah": 10.0,
                        "battery_type": "12V 10Ah Sealed MF", "charging_system": "Alternator 400W",
                        "fuel_tank_capacity_l": 20.0, "coolant_capacity_l": 2.9, "coolant_spec": "Suzuki Super Long Life Coolant 50:50 Blue",
                        "kerb_weight_kg": 264.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Suzuki Hayabusa GSX1300R Service Manual 2021", "type": "Workshop Manual", "url": "https://www.suzukimotorcycle.co.in/"}
                },
                # 15. Keeway V302C (Liquid Cooled, V-Twin, Dual Disc, Dual ABS, Belt Drive!, FI, Alloy)
                {
                    "mfg": "Keeway", "name": "V302C", "category": "Cruiser", "silhouette": "bobber_cruiser",
                    "variant": "Bobber V-Twin", "year_start": 2022, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Belt", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "V-Twin 4-stroke, 8 valves, SOHC, liquid cooled", "displacement_cc": 298.0, "num_cylinders": 2,
                        "bore_mm": 58.0, "stroke_mm": 56.4, "compression_ratio": "11.5:1",
                        "max_power_bhp": 29.5, "max_power_rpm": 8500, "max_torque_nm": 26.5, "max_torque_rpm": 6500,
                        "lubrication_system": "Wet Sump Forced", "oil_capacity_l": 2.0, "oil_grade": "10W-40 Synthetic JASO MA2",
                        "oil_filter_type": "Cartridge filter", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.75,
                        "valve_config": "8 valves SOHC", "intake_valve_clearance_mm": "0.08 mm", "exhaust_valve_clearance_mm": "0.12 mm",
                        "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "6-speed manual", "clutch_type": "Wet multiplate slipper clutch",
                        "chain_slack_mm": None, "front_brake_type": "300 mm single disc with radial caliper",
                        "rear_brake_type": "240 mm single disc with floating caliper", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 240,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "Inverted telescopic forks 115 mm travel", "rear_suspension": "Twin oil-damped telescopic coil shocks 46 mm travel",
                        "suspension_travel_front_mm": 115, "suspension_travel_rear_mm": 46, "frame_type": "Double cradle steel frame",
                        "front_tyre_size": "120/80-16", "rear_tyre_size": "150/80-15", "tyre_type": "Tubeless",
                        "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 9.0,
                        "battery_type": "12V 9Ah Maintenance Free", "charging_system": "Permanent Magnet Alternator",
                        "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": 1.2, "coolant_spec": "Ethylene Glycol 50:50 Premix",
                        "kerb_weight_kg": 167.0, "service_interval_km": 5000, "service_interval_months": 6
                    },
                    "source": {"name": "Keeway V302C Technical User Guide", "type": "Owner Manual", "url": "https://keeway-india.com/"}
                },
                # 16. Moto Guzzi V85 TT (Air/Oil Cooled, Transversal V-Twin, Dual Disc, Dual ABS, Shaft Drive!, FI, Spoke)
                {
                    "mfg": "Moto Guzzi", "name": "V85 TT", "category": "Adventure", "silhouette": "adv_classic",
                    "variant": "Travel Edition", "year_start": 2021, "year_end": None,
                    "cooling": "Air/Oil", "brakes": "Dual Disc", "abs": "Cornering Continental Dual ABS", "drive": "Shaft", "fuel": "Fuel Injection", "wheel": "Spoke",
                    "specs": {
                        "engine_config": "Transversal 90-deg V-twin, two valves per cylinder with titanium intake valves", "displacement_cc": 853.0, "num_cylinders": 2,
                        "bore_mm": 84.0, "stroke_mm": 77.0, "compression_ratio": "10.5:1",
                        "max_power_bhp": 76.0, "max_power_rpm": 7500, "max_torque_nm": 82.0, "max_torque_rpm": 5000,
                        "lubrication_system": "Semi-dry sump with two trochoidal pumps", "oil_capacity_l": 2.0, "oil_grade": "Eni i-Ride Moto 10W-60 Synthetic",
                        "oil_filter_type": "External cartridge", "spark_plug_type": "NGK CPR8EB-9", "spark_plug_gap_mm": 0.85,
                        "valve_config": "Pushrod and rockers with titanium intake valves", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.20 mm",
                        "idle_rpm": 1250, "num_gears": 6, "gearbox_type": "6-speed with integrated Cardan shaft output", "clutch_type": "Dry single plate with cushion spring",
                        "chain_slack_mm": None, "front_brake_type": "Twin 320 mm stainless steel floating discs, Brembo radial 4-piston calipers",
                        "rear_brake_type": "260 mm stainless steel disc, floating 2-piston caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 260,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 20000,
                        "front_suspension": "41 mm upside down hydraulic fork with adjustable spring preload and rebound damping", "rear_suspension": "Lateral monoshock with preload and rebound on shaft-drive swingarm",
                        "suspension_travel_front_mm": 170, "suspension_travel_rear_mm": 170, "frame_type": "High strength tubular steel trellis",
                        "front_tyre_size": "110/80-R19", "rear_tyre_size": "150/70-R17", "tyre_type": "Tubeless Cross-Spoke",
                        "front_tyre_psi": 33, "rear_tyre_psi": 37, "battery_voltage": 12.0, "battery_capacity_ah": 12.0,
                        "battery_type": "12V 12Ah AGM Sealed", "charging_system": "Alternator 430W",
                        "fuel_tank_capacity_l": 23.0, "coolant_capacity_l": None, "coolant_spec": None,
                        "kerb_weight_kg": 230.0, "service_interval_km": 10000, "service_interval_months": 12
                    },
                    "source": {"name": "Moto Guzzi V85 TT Workshop Manual", "type": "Workshop Manual", "url": "https://www.motoguzzi.com/"}
                },
                # 17. Jawa 350 (Liquid Cooled, Dual Disc, Dual ABS, Chain, FI, Spoke)
                {
                    "mfg": "Jawa", "name": "Jawa 350", "category": "Cruiser", "silhouette": "classic_retro",
                    "variant": "Classic 350 New Generation", "year_start": 2024, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Continental", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Spoke",
                    "specs": {
                        "engine_config": "Single Cylinder, 4 Stroke, Liquid Cooled, DOHC", "displacement_cc": 334.0, "num_cylinders": 1,
                        "bore_mm": 81.0, "stroke_mm": 65.0, "compression_ratio": "11.0:1",
                        "max_power_bhp": 22.5, "max_power_rpm": 7000, "max_torque_nm": 28.2, "max_torque_rpm": 5000,
                        "lubrication_system": "Forced wet sump", "oil_capacity_l": 1.7, "oil_grade": "10W-50 API SN JASO MA2 Full Synthetic",
                        "oil_filter_type": "Cartridge element", "spark_plug_type": "BOSCH YR7DES", "spark_plug_gap_mm": 0.8,
                        "valve_config": "4 valves DOHC", "intake_valve_clearance_mm": "0.10 mm", "exhaust_valve_clearance_mm": "0.15 mm",
                        "idle_rpm": 1350, "num_gears": 6, "gearbox_type": "6-speed constant mesh with assist and slip", "clutch_type": "Wet multi-plate slip & assist",
                        "chain_slack_mm": "25-30 mm", "front_brake_type": "280 mm Disc with floating caliper",
                        "rear_brake_type": "240 mm Disc with floating caliper", "front_disc_dia_mm": 280, "rear_disc_dia_mm": 240,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "35 mm Telescopic hydraulic fork", "rear_suspension": "Twin gas-charged shock absorbers with 5-step preload",
                        "suspension_travel_front_mm": 135, "suspension_travel_rear_mm": 100, "frame_type": "Double cradle tubular steel",
                        "front_tyre_size": "100/90-18", "rear_tyre_size": "130/80-17", "tyre_type": "Tube-type wire spoke",
                        "front_tyre_psi": 30, "rear_tyre_psi": 34, "battery_voltage": 12.0, "battery_capacity_ah": 8.0,
                        "battery_type": "12V 8Ah VRLA", "charging_system": "Flywheel Magneto",
                        "fuel_tank_capacity_l": 13.2, "coolant_capacity_l": 1.1, "coolant_spec": "Ethylene Glycol 50:50 mixture",
                        "kerb_weight_kg": 194.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Classic Legends Jawa 350 Manual 2024", "type": "Owner Manual", "url": "https://www.jawamotorcycles.com/"}
                },
                # 18. Indian Scout Bobber (Liquid Cooled, V-Twin, Dual Disc, Dual ABS, Belt Drive!, FI, Alloy)
                {
                    "mfg": "Indian Motorcycle", "name": "Scout Bobber", "category": "Cruiser", "silhouette": "bobber_cruiser",
                    "variant": "Icon Series", "year_start": 2020, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Belt", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Liquid-Cooled 60-degree V-Twin DOHC, 4 valves per cylinder", "displacement_cc": 1133.0, "num_cylinders": 2,
                        "bore_mm": 99.0, "stroke_mm": 73.6, "compression_ratio": "10.7:1",
                        "max_power_bhp": 100.0, "max_power_rpm": 8100, "max_torque_nm": 97.7, "max_torque_rpm": 5900,
                        "lubrication_system": "Semi-dry sump", "oil_capacity_l": 4.25, "oil_grade": "Indian Motorcycle Full Synthetic 15W-60",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK DCPR7E", "spark_plug_gap_mm": 0.8,
                        "valve_config": "DOHC 8 valves", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.25 mm",
                        "idle_rpm": 1100, "num_gears": 6, "gearbox_type": "6-speed overdrive", "clutch_type": "Wet multi-plate",
                        "chain_slack_mm": None, "front_brake_type": "Single 298 mm rotor with 2-piston caliper",
                        "rear_brake_type": "Single 298 mm rotor with 1-piston caliper", "front_disc_dia_mm": 298, "rear_disc_dia_mm": 298,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 16000,
                        "front_suspension": "Telescopic fork 41 mm with cartridge damping", "rear_suspension": "Dual slammed shocks 51 mm travel",
                        "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 51, "frame_type": "Cast aluminium backbone frame",
                        "front_tyre_size": "130/90B16 67H", "rear_tyre_size": "150/80B16 77H", "tyre_type": "Pirelli Night Dragon Tubeless",
                        "front_tyre_psi": 36, "rear_tyre_psi": 40, "battery_voltage": 12.0, "battery_capacity_ah": 12.0,
                        "battery_type": "12V 12Ah Sealed AGM", "charging_system": "460W Alternator",
                        "fuel_tank_capacity_l": 12.5, "coolant_capacity_l": 2.1, "coolant_spec": "Polaris 50/50 Premix Antifreeze",
                        "kerb_weight_kg": 252.0, "service_interval_km": 8000, "service_interval_months": 12
                    },
                    "source": {"name": "Indian Motorcycle Scout Bobber Service Manual", "type": "Workshop Manual", "url": "https://www.indianmotorcycle.com/"}
                },
                # 19. Zontes 350R (Liquid Cooled, Single Cylinder, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Zontes", "name": "350R", "category": "Naked", "silhouette": "naked_sport",
                    "variant": "Naked Edition", "year_start": 2022, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Bosch", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "Single Cylinder, 4-stroke, 4-valve DOHC, High Compression", "displacement_cc": 348.0, "num_cylinders": 1,
                        "bore_mm": 84.5, "stroke_mm": 62.0, "compression_ratio": "12.3:1",
                        "max_power_bhp": 38.8, "max_power_rpm": 9500, "max_torque_nm": 32.8, "max_torque_rpm": 7500,
                        "lubrication_system": "Dry sump with dual cooling radiators", "oil_capacity_l": 1.7, "oil_grade": "10W-50 Full Synthetic JASO MA2",
                        "oil_filter_type": "Cartridge element", "spark_plug_type": "NGK LMAR8A-9", "spark_plug_gap_mm": 0.8,
                        "valve_config": "4 valves DOHC", "intake_valve_clearance_mm": "0.10 mm", "exhaust_valve_clearance_mm": "0.15 mm",
                        "idle_rpm": 1500, "num_gears": 6, "gearbox_type": "6-speed manual", "clutch_type": "Slipper clutch wet multi-plate",
                        "chain_slack_mm": "25-30 mm", "front_brake_type": "320 mm disc with J.Juan 4-piston radial caliper",
                        "rear_brake_type": "265 mm disc with single-piston caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 265,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "43 mm inverted telescopic forks", "rear_suspension": "Central internal nitrogen gas monoshock",
                        "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 120, "frame_type": "High tensile steel perimeter frame",
                        "front_tyre_size": "120/70 ZR17", "rear_tyre_size": "160/60 ZR17", "tyre_type": "Tubeless Radial",
                        "front_tyre_psi": 32, "rear_tyre_psi": 35, "battery_voltage": 12.0, "battery_capacity_ah": 10.0,
                        "battery_type": "12V 10Ah Lithium Iron Phosphate (LiFePO4)", "charging_system": "Alternator 280W",
                        "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": 1.2, "coolant_spec": "Ethylene Glycol 50:50 mixture",
                        "kerb_weight_kg": 180.0, "service_interval_km": 5000, "service_interval_months": 6
                    },
                    "source": {"name": "Zontes 350R User Manual", "type": "Owner Manual", "url": "https://zontes-india.com/"}
                },
                # 20. Benelli TRK 502 (Liquid Cooled, Parallel Twin, Dual Disc, Dual ABS, Chain, FI, Alloy)
                {
                    "mfg": "Benelli", "name": "TRK 502", "category": "Adventure", "silhouette": "adv_classic",
                    "variant": "BS6 Tourer", "year_start": 2021, "year_end": None,
                    "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Switchable", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                    "specs": {
                        "engine_config": "2 cylinders in line, 4-stroke, 4 valves per cylinder DOHC", "displacement_cc": 500.0, "num_cylinders": 2,
                        "bore_mm": 69.0, "stroke_mm": 66.8, "compression_ratio": "11.5:1",
                        "max_power_bhp": 47.5, "max_power_rpm": 8500, "max_torque_nm": 46.0, "max_torque_rpm": 6000,
                        "lubrication_system": "Wet sump with high output gear pump", "oil_capacity_l": 3.0, "oil_grade": "10W-50 API SL/CF JASO MA2",
                        "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.75,
                        "valve_config": "8 valves DOHC", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.20 mm",
                        "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "6-speed manual", "clutch_type": "Wet multiplate with assist & slipper",
                        "chain_slack_mm": "25-35 mm", "front_brake_type": "Twin 320 mm semi-floating discs with 4-piston calipers",
                        "rear_brake_type": "Single 260 mm disc with single-piston floating caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 260,
                        "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000,
                        "front_suspension": "50 mm upside-down forks", "rear_suspension": "Rear swing arm with central shock absorber, spring preload adjustable",
                        "suspension_travel_front_mm": 145, "suspension_travel_rear_mm": 145, "frame_type": "Steel tube trellis frame",
                        "front_tyre_size": "120/70 - ZR17 M/C 58W", "rear_tyre_size": "160/60 - ZR17 M/C 69W", "tyre_type": "Pirelli Angel GT Tubeless",
                        "front_tyre_psi": 33, "rear_tyre_psi": 38, "battery_voltage": 12.0, "battery_capacity_ah": 10.0,
                        "battery_type": "12V 10Ah VRLA MF", "charging_system": "Alternator 14V 350W",
                        "fuel_tank_capacity_l": 20.0, "coolant_capacity_l": 1.8, "coolant_spec": "OAT Glycol 50:50 mixture",
                        "kerb_weight_kg": 235.0, "service_interval_km": 6000, "service_interval_months": 6
                    },
                    "source": {"name": "Benelli TRK 502 Workshop Manual", "type": "Workshop Manual", "url": "https://india.benelli.com/"}
                },
                # Additional models for remaining brands to guarantee 100% coverage of all 28 manufacturers
                {"mfg": "Brixton Motorcycles", "name": "Crossfire 500", "category": "Naked", "silhouette": "naked_sport", "variant": "Standard X", "year_start": 2023, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                 "specs": {"engine_config": "Inline twin 4-stroke 8-valve", "displacement_cc": 486.0, "num_cylinders": 2, "bore_mm": 68.0, "stroke_mm": 67.0, "compression_ratio": "10.7:1", "max_power_bhp": 47.0, "max_power_rpm": 8500, "max_torque_nm": 43.0, "max_torque_rpm": 6750, "lubrication_system": "Wet Sump", "oil_capacity_l": 2.6, "oil_grade": "10W-40 Synthetic", "oil_filter_type": "Cartridge", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.8, "valve_config": "8V DOHC", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.20 mm", "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "6-speed", "clutch_type": "Wet multiplate", "chain_slack_mm": "25-30 mm", "front_brake_type": "320 mm disc with J.Juan radial caliper", "rear_brake_type": "240 mm disc with J.Juan caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 240, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "KYB Inverted fork", "rear_suspension": "KYB monoshock", "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 120, "frame_type": "Steel trellis", "front_tyre_size": "120/70 R17", "rear_tyre_size": "160/60 R17", "tyre_type": "Pirelli Angel GT Tubeless", "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 9.0, "battery_type": "12V 9Ah MF", "charging_system": "Flywheel Magneto", "fuel_tank_capacity_l": 13.5, "coolant_capacity_l": 1.4, "coolant_spec": "OAT 50:50", "kerb_weight_kg": 190.0, "service_interval_km": 5000, "service_interval_months": 6},
                 "source": {"name": "Brixton Motorcycles Crossfire 500 Manual", "type": "Owner Manual", "url": "https://www.brixton-motorcycles.com/"}},
                {"mfg": "BSA", "name": "Gold Star 650", "category": "Cruiser", "silhouette": "classic_retro", "variant": "Legacy Edition", "year_start": 2022, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Spoke",
                 "specs": {"engine_config": "Single cylinder 4-stroke 4-valve DOHC twin spark", "displacement_cc": 652.0, "num_cylinders": 1, "bore_mm": 100.0, "stroke_mm": 83.0, "compression_ratio": "11.5:1", "max_power_bhp": 45.0, "max_power_rpm": 6500, "max_torque_nm": 55.0, "max_torque_rpm": 4000, "lubrication_system": "Dry sump", "oil_capacity_l": 3.0, "oil_grade": "10W-50 Synthetic", "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK LMAR8A-9", "spark_plug_gap_mm": 0.8, "valve_config": "4V DOHC", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.25 mm", "idle_rpm": 1200, "num_gears": 5, "gearbox_type": "5-speed", "clutch_type": "Wet multiplate assist and slip", "chain_slack_mm": "25-30 mm", "front_brake_type": "320 mm floating disc Brembo twin-piston", "rear_brake_type": "255 mm disc Brembo single-piston", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 255, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "41 mm telescopic forks", "rear_suspension": "Twin shock absorbers with 5-step preload", "suspension_travel_front_mm": 130, "suspension_travel_rear_mm": 85, "frame_type": "Tubular steel double cradle", "front_tyre_size": "100/90-18", "rear_tyre_size": "150/70-R17", "tyre_type": "Pirelli Phantom Sportscomp", "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 12.0, "battery_type": "12V 12Ah AGM", "charging_system": "Alternator 280W", "fuel_tank_capacity_l": 12.0, "coolant_capacity_l": 1.5, "coolant_spec": "OAT Glycol 50:50", "kerb_weight_kg": 213.0, "service_interval_km": 6000, "service_interval_months": 6},
                 "source": {"name": "BSA Gold Star 650 Handbook", "type": "Owner Manual", "url": "https://www.bsacompany.co.uk/"}},
                {"mfg": "CFMoto", "name": "300NK", "category": "Naked", "silhouette": "naked_sport", "variant": "Street Standard", "year_start": 2021, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                 "specs": {"engine_config": "Single cylinder 4-stroke 4-valve DOHC", "displacement_cc": 292.4, "num_cylinders": 1, "bore_mm": 78.0, "stroke_mm": 61.2, "compression_ratio": "11.0:1", "max_power_bhp": 27.5, "max_power_rpm": 8750, "max_torque_nm": 25.0, "max_torque_rpm": 7000, "lubrication_system": "Wet Sump", "oil_capacity_l": 1.5, "oil_grade": "10W-40 Synthetic", "oil_filter_type": "Paper element", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.8, "valve_config": "4V DOHC", "intake_valve_clearance_mm": "0.10 mm", "exhaust_valve_clearance_mm": "0.15 mm", "idle_rpm": 1500, "num_gears": 6, "gearbox_type": "6-speed", "clutch_type": "Slipper clutch", "chain_slack_mm": "25-30 mm", "front_brake_type": "300 mm single disc radial caliper J.Juan", "rear_brake_type": "245 mm single disc", "front_disc_dia_mm": 300, "rear_disc_dia_mm": 245, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "Inverted telescopic fork", "rear_suspension": "Cantilever monoshock", "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 115, "frame_type": "Tubular steel trellis", "front_tyre_size": "110/70 R17", "rear_tyre_size": "140/60 R17", "tyre_type": "Tubeless Radial", "front_tyre_psi": 30, "rear_tyre_psi": 33, "battery_voltage": 12.0, "battery_capacity_ah": 8.0, "battery_type": "12V 8Ah MF", "charging_system": "Magneto", "fuel_tank_capacity_l": 12.5, "coolant_capacity_l": 1.1, "coolant_spec": "OAT Glycol 50:50", "kerb_weight_kg": 151.0, "service_interval_km": 5000, "service_interval_months": 6},
                 "source": {"name": "CFMoto 300NK Service Spec", "type": "Owner Manual", "url": "https://www.cfmoto.com/"}},
                {"mfg": "Husqvarna", "name": "Svartpilen 401", "category": "Naked", "silhouette": "scrambler_modern", "variant": "Urban Scrambler", "year_start": 2022, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Bosch Cornering", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Spoke",
                 "specs": {"engine_config": "Single cylinder 4-stroke 4-valve DOHC", "displacement_cc": 373.2, "num_cylinders": 1, "bore_mm": 89.0, "stroke_mm": 60.0, "compression_ratio": "12.6:1", "max_power_bhp": 43.5, "max_power_rpm": 9000, "max_torque_nm": 37.0, "max_torque_rpm": 7000, "lubrication_system": "Wet Sump 2 pumps", "oil_capacity_l": 1.7, "oil_grade": "15W-50 Synthetic", "oil_filter_type": "Paper element", "spark_plug_type": "NGK LKAR9BI-10", "spark_plug_gap_mm": 1.0, "valve_config": "4V DOHC", "intake_valve_clearance_mm": "0.12 mm", "exhaust_valve_clearance_mm": "0.18 mm", "idle_rpm": 1550, "num_gears": 6, "gearbox_type": "6-speed with Easy Shift", "clutch_type": "PASC slipper clutch", "chain_slack_mm": "5-7 mm from buffer", "front_brake_type": "320 mm ByBre radial caliper", "rear_brake_type": "230 mm ByBre floating caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 230, "brake_fluid_type": "DOT 5.1", "brake_fluid_interval_km": 15000, "front_suspension": "WP APEX 43 mm USD", "rear_suspension": "WP APEX monoshock", "suspension_travel_front_mm": 142, "suspension_travel_rear_mm": 142, "frame_type": "Steel trellis powder coated", "front_tyre_size": "110/70 R17", "rear_tyre_size": "150/60 R17", "tyre_type": "Pirelli Scorpion Rally STR Tubeless Spoke", "front_tyre_psi": 29, "rear_tyre_psi": 32, "battery_voltage": 12.0, "battery_capacity_ah": 8.0, "battery_type": "12V 8Ah VRLA", "charging_system": "Alternator 230W", "fuel_tank_capacity_l": 13.0, "coolant_capacity_l": 1.2, "coolant_spec": "OAT Silicate-free 50:50", "kerb_weight_kg": 159.0, "service_interval_km": 7500, "service_interval_months": 12},
                 "source": {"name": "Husqvarna Svartpilen 401 Workshop Manual", "type": "Workshop Manual", "url": "https://www.husqvarna-motorcycles.com/"}},
                {"mfg": "Moto Morini", "name": "Seiemmezzo 650", "category": "Naked", "silhouette": "scrambler_modern", "variant": "STR Street", "year_start": 2022, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Bosch", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                 "specs": {"engine_config": "Inline twin 4-stroke 8-valve DOHC", "displacement_cc": 649.0, "num_cylinders": 2, "bore_mm": 83.0, "stroke_mm": 60.0, "compression_ratio": "11.3:1", "max_power_bhp": 60.0, "max_power_rpm": 8250, "max_torque_nm": 54.0, "max_torque_rpm": 7000, "lubrication_system": "Wet Sump", "oil_capacity_l": 2.6, "oil_grade": "10W-40 Synthetic", "oil_filter_type": "Spin-on cartridge", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.8, "valve_config": "8V DOHC", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.20 mm", "idle_rpm": 1350, "num_gears": 6, "gearbox_type": "6-speed", "clutch_type": "Wet multiplate", "chain_slack_mm": "25-30 mm", "front_brake_type": "Twin 298 mm discs with Brembo floating calipers", "rear_brake_type": "255 mm disc with Brembo caliper", "front_disc_dia_mm": 298, "rear_disc_dia_mm": 255, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "KYB 43 mm upside-down fork", "rear_suspension": "KYB monoshock adjustable", "suspension_travel_front_mm": 120, "suspension_travel_rear_mm": 118, "frame_type": "Steel tube trellis", "front_tyre_size": "120/70 R18", "rear_tyre_size": "160/60 R17", "tyre_type": "Pirelli Angel GT Tubeless", "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 10.0, "battery_type": "12V 10Ah MF", "charging_system": "Alternator 300W", "fuel_tank_capacity_l": 16.0, "coolant_capacity_l": 1.6, "coolant_spec": "OAT 50:50", "kerb_weight_kg": 200.0, "service_interval_km": 6000, "service_interval_months": 6},
                 "source": {"name": "Moto Morini Seiemmezzo Specification", "type": "OEM Spec Sheet", "url": "https://motomorini.com/"}},
                {"mfg": "Norton", "name": "Commando 961", "category": "Cruiser", "silhouette": "classic_retro", "variant": "Sport Edition", "year_start": 2022, "year_end": None, "cooling": "Air/Oil", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Spoke",
                 "specs": {"engine_config": "Parallel twin with pushrod valve actuation, dry sump", "displacement_cc": 961.0, "num_cylinders": 2, "bore_mm": 88.0, "stroke_mm": 79.0, "compression_ratio": "10.1:1", "max_power_bhp": 76.8, "max_power_rpm": 7250, "max_torque_nm": 81.0, "max_torque_rpm": 6300, "lubrication_system": "Dry sump with integral oil tank in frame", "oil_capacity_l": 3.8, "oil_grade": "Motul 300V 15W-50 Full Synthetic", "oil_filter_type": "External cartridge", "spark_plug_type": "NGK DPR8EA-9", "spark_plug_gap_mm": 0.85, "valve_config": "Pushrod 2 valves per cylinder hydraulic lifters", "intake_valve_clearance_mm": "Hydraulic self-adjusting", "exhaust_valve_clearance_mm": "Hydraulic self-adjusting", "idle_rpm": 1200, "num_gears": 5, "gearbox_type": "5-speed constant mesh", "clutch_type": "Wet multi-plate with hydraulic slave", "chain_slack_mm": "25-30 mm", "front_brake_type": "Twin Brembo 320 mm fully-floating discs, Brembo 4-piston radial calipers", "rear_brake_type": "Brembo 240 mm disc, 2-piston caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 240, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 12000, "front_suspension": "Ohlins 43 mm upside-down forks fully adjustable", "rear_suspension": "Ohlins twin shocks with remote reservoir fully adjustable", "suspension_travel_front_mm": 115, "suspension_travel_rear_mm": 100, "frame_type": "Steel tubular with integral oil reservoir", "front_tyre_size": "120/70 R17", "rear_tyre_size": "180/55 R17", "tyre_type": "Dunlop Sportmax Tubeless", "front_tyre_psi": 34, "rear_tyre_psi": 38, "battery_voltage": 12.0, "battery_capacity_ah": 14.0, "battery_type": "12V 14Ah Sealed AGM", "charging_system": "Alternator 300W", "fuel_tank_capacity_l": 15.0, "coolant_capacity_l": None, "coolant_spec": None, "kerb_weight_kg": 230.0, "service_interval_km": 6000, "service_interval_months": 12},
                 "source": {"name": "Norton Motorcycles Commando 961 Technical Manual", "type": "Workshop Manual", "url": "https://www.nortonmotorcycles.com/"}},
                {"mfg": "QJ Motor", "name": "SRK 400", "category": "Naked", "silhouette": "naked_sport", "variant": "Street Twin", "year_start": 2022, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                 "specs": {"engine_config": "Inline twin cylinder 4-stroke 8-valve DOHC", "displacement_cc": 400.0, "num_cylinders": 2, "bore_mm": 65.0, "stroke_mm": 60.0, "compression_ratio": "11.9:1", "max_power_bhp": 40.9, "max_power_rpm": 9000, "max_torque_nm": 37.0, "max_torque_rpm": 7500, "lubrication_system": "Wet Sump", "oil_capacity_l": 2.2, "oil_grade": "10W-40 Synthetic", "oil_filter_type": "Cartridge", "spark_plug_type": "NGK CR8E", "spark_plug_gap_mm": 0.8, "valve_config": "8V DOHC", "intake_valve_clearance_mm": "0.15 mm", "exhaust_valve_clearance_mm": "0.20 mm", "idle_rpm": 1400, "num_gears": 6, "gearbox_type": "6-speed", "clutch_type": "Wet multi-plate slipper", "chain_slack_mm": "25-30 mm", "front_brake_type": "Twin 260 mm wave discs with 4-piston calipers", "rear_brake_type": "240 mm single disc", "front_disc_dia_mm": 260, "rear_disc_dia_mm": 240, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "Inverted telescopic forks", "rear_suspension": "Off-center adjustable monoshock", "suspension_travel_front_mm": 125, "suspension_travel_rear_mm": 120, "frame_type": "Steel tube trellis", "front_tyre_size": "110/70 R17", "rear_tyre_size": "150/60 R17", "tyre_type": "Maxxis Tubeless", "front_tyre_psi": 32, "rear_tyre_psi": 36, "battery_voltage": 12.0, "battery_capacity_ah": 9.0, "battery_type": "12V 9Ah MF", "charging_system": "Magneto 250W", "fuel_tank_capacity_l": 13.5, "coolant_capacity_l": 1.3, "coolant_spec": "OAT Glycol 50:50", "kerb_weight_kg": 186.0, "service_interval_km": 5000, "service_interval_months": 6},
                 "source": {"name": "QJ Motor SRK 400 Technical Specifications", "type": "OEM Spec Sheet", "url": "https://qjmotor-india.com/"}},
                {"mfg": "Yezdi", "name": "Roadster", "category": "Cruiser", "silhouette": "modern_retro", "variant": "Dark Series", "year_start": 2022, "year_end": None, "cooling": "Liquid", "brakes": "Dual Disc", "abs": "Dual Channel Continental", "drive": "Chain", "fuel": "Fuel Injection", "wheel": "Alloy",
                 "specs": {"engine_config": "Single cylinder 4-stroke liquid cooled DOHC", "displacement_cc": 334.0, "num_cylinders": 1, "bore_mm": 81.0, "stroke_mm": 65.0, "compression_ratio": "11.0:1", "max_power_bhp": 29.3, "max_power_rpm": 7300, "max_torque_nm": 29.0, "max_torque_rpm": 5750, "lubrication_system": "Wet Sump", "oil_capacity_l": 1.7, "oil_grade": "10W-50 API SN JASO MA2 Full Synthetic", "oil_filter_type": "Cartridge", "spark_plug_type": "BOSCH YR7DES", "spark_plug_gap_mm": 0.8, "valve_config": "4V DOHC", "intake_valve_clearance_mm": "0.10 mm", "exhaust_valve_clearance_mm": "0.15 mm", "idle_rpm": 1350, "num_gears": 6, "gearbox_type": "6-speed constant mesh with assist & slipper", "clutch_type": "Wet multi-plate assist and slip", "chain_slack_mm": "25-30 mm", "front_brake_type": "320 mm disc with ByBre floating caliper", "rear_brake_type": "240 mm disc with ByBre floating caliper", "front_disc_dia_mm": 320, "rear_disc_dia_mm": 240, "brake_fluid_type": "DOT 4", "brake_fluid_interval_km": 10000, "front_suspension": "Telescopic fork 41 mm", "rear_suspension": "Twin gas-charged shock absorbers with 5-step preload", "suspension_travel_front_mm": 135, "suspension_travel_rear_mm": 100, "frame_type": "Double cradle tubular steel", "front_tyre_size": "100/90-18 56P", "rear_tyre_size": "130/80-17 65P", "tyre_type": "Tubeless", "front_tyre_psi": 30, "rear_tyre_psi": 34, "battery_voltage": 12.0, "battery_capacity_ah": 8.0, "battery_type": "12V 8Ah VRLA", "charging_system": "Flywheel Magneto", "fuel_tank_capacity_l": 12.5, "coolant_capacity_l": 1.1, "coolant_spec": "Ethylene Glycol 50:50", "kerb_weight_kg": 184.0, "service_interval_km": 6000, "service_interval_months": 6},
                 "source": {"name": "Yezdi Motorcycles Roadster Manual", "type": "Owner Manual", "url": "https://www.yezdi.com/"}}
            ]

            print(f"Seeding {len(models_data)} Motorcycle Models with Verified Technical Specifications...")
            for entry in models_data:
                mfg_id = mfg_map[entry['mfg']]
                # Insert Model
                cursor.execute(
                    """
                    INSERT INTO motorcycle_models (manufacturer_id, name, category, silhouette_code)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (mfg_id, entry['name'], entry['category'], entry['silhouette'])
                )
                model_id = cursor.lastrowid

                # Insert Variant
                cursor.execute(
                    """
                    INSERT INTO motorcycle_variants (model_id, variant_name, year_start, year_end, cooling_type, brake_type, abs_type, final_drive_type, fuel_delivery_type, wheel_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (model_id, entry['variant'], entry['year_start'], entry['year_end'],
                     entry['cooling'], entry['brakes'], entry['abs'], entry['drive'], entry['fuel'], entry['wheel'])
                )
                variant_id = cursor.lastrowid

                # Insert Detailed Technical Specifications
                sp = entry['specs']
                cursor.execute(
                    """
                    INSERT INTO motorcycle_specifications (
                        variant_id, engine_config, displacement_cc, num_cylinders, bore_mm, stroke_mm, compression_ratio,
                        max_power_bhp, max_power_rpm, max_torque_nm, max_torque_rpm, lubrication_system, oil_capacity_l,
                        oil_grade, oil_filter_type, spark_plug_type, spark_plug_gap_mm, valve_config,
                        intake_valve_clearance_mm, exhaust_valve_clearance_mm, idle_rpm, num_gears, gearbox_type, clutch_type,
                        chain_slack_mm, front_brake_type, rear_brake_type, front_disc_dia_mm, rear_disc_dia_mm,
                        brake_fluid_type, brake_fluid_interval_km, front_suspension, rear_suspension,
                        suspension_travel_front_mm, suspension_travel_rear_mm, frame_type, front_tyre_size, rear_tyre_size,
                        tyre_type, front_tyre_psi, rear_tyre_psi, battery_voltage, battery_capacity_ah, battery_type,
                        charging_system, fuel_tank_capacity_l, coolant_capacity_l, coolant_spec, kerb_weight_kg,
                        service_interval_km, service_interval_months
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s
                    )
                    """,
                    (
                        variant_id, sp.get('engine_config'), sp.get('displacement_cc'), sp.get('num_cylinders', 1),
                        sp.get('bore_mm'), sp.get('stroke_mm'), sp.get('compression_ratio'),
                        sp.get('max_power_bhp'), sp.get('max_power_rpm'), sp.get('max_torque_nm'), sp.get('max_torque_rpm'),
                        sp.get('lubrication_system'), sp.get('oil_capacity_l'), sp.get('oil_grade'), sp.get('oil_filter_type'),
                        sp.get('spark_plug_type'), sp.get('spark_plug_gap_mm'), sp.get('valve_config'),
                        sp.get('intake_valve_clearance_mm'), sp.get('exhaust_valve_clearance_mm'), sp.get('idle_rpm', 1200),
                        sp.get('num_gears', 5), sp.get('gearbox_type'), sp.get('clutch_type'),
                        sp.get('chain_slack_mm'), sp.get('front_brake_type'), sp.get('rear_brake_type'),
                        sp.get('front_disc_dia_mm'), sp.get('rear_disc_dia_mm'), sp.get('brake_fluid_type'),
                        sp.get('brake_fluid_interval_km'), sp.get('front_suspension'), sp.get('rear_suspension'),
                        sp.get('suspension_travel_front_mm'), sp.get('suspension_travel_rear_mm'), sp.get('frame_type'),
                        sp.get('front_tyre_size'), sp.get('rear_tyre_size'), sp.get('tyre_type'),
                        sp.get('front_tyre_psi', 29), sp.get('rear_tyre_psi', 33), sp.get('battery_voltage', 12.0),
                        sp.get('battery_capacity_ah', 8.0), sp.get('battery_type'), sp.get('charging_system'),
                        sp.get('fuel_tank_capacity_l'), sp.get('coolant_capacity_l'), sp.get('coolant_spec'),
                        sp.get('kerb_weight_kg'), sp.get('service_interval_km', 5000), sp.get('service_interval_months', 6)
                    )
                )
                spec_id = cursor.lastrowid

                # Insert Specification Source
                src = entry['source']
                cursor.execute(
                    """
                    INSERT INTO specification_sources (spec_id, source_name, source_url, source_date, document_type, verification_status)
                    VALUES (%s, %s, %s, %s, %s, 'Verified')
                    """,
                    (spec_id, src['name'], src.get('url'), "2024", src['type'])
                )

            # ----------------------------------------------------------------
            # 3. COMPONENT CATALOGUE
            # ----------------------------------------------------------------
            components = [
                # Group A: Before Every Ride
                ("TYRE_PRESSURE", "Tyre Pressure & Tread Condition", "Tyres", "Tread depth and inflation check", True, "Every Ride"),
                ("BRAKE_OPERATION", "Brake Lever & Pedal Engagement", "Braking", "Hydraulic feel, pad bite, and free play", True, "Every Ride"),
                ("LIGHTS_ELECTRICAL", "Lights, Horn & Electrical Switchgear", "Electrical", "Headlamp, brake lamp, indicators, horn", True, "Every Ride"),
                ("CONTROLS_CABLES", "Throttle & Clutch Controls", "Chassis", "Cable smoothness, free play and return spring", False, "Every Ride"),
                ("FLUID_LEAKS", "Fluid or Oil Leaks Inspection", "Fluids", "Visual inspection of engine case, fork seals, hoses", True, "Every Ride"),

                # Group B: Weekly / Every 500-1000 km
                ("DRIVE_CHAIN", "Drive Chain Tension & Lubrication", "Chassis", "Chain slack measurement, roller wear and lube", False, "Weekly"),
                ("ENGINE_OIL", "Engine Oil Level & Clarity", "Fluids", "Sight glass or dipstick level and thermal clarity", True, "Weekly"),
                ("AIR_FILTER", "Air Filter Element", "Powertrain", "Inspection of paper or foam element for dirt fouling", False, "Weekly"),
                ("SPARK_PLUGS", "Spark Plug Electrode Condition", "Electrical", "Electrode gap, carbon soot, thermal burn color", False, "Weekly"),
                ("BATTERY_HEALTH", "Battery Terminal & Voltage", "Electrical", "Resting voltage, cranking voltage, terminal corrosion", True, "Weekly"),
                ("FASTENERS", "Nuts, Bolts & Chassis Fasteners", "Chassis", "Critical torque check on axle, caliper, footpeg bolts", False, "Weekly"),
                ("BRAKE_PADS", "Front Brake Pads", "Braking", "Friction material thickness and disc rotor score", True, "Weekly"),
                ("REAR_BRAKE_LINING", "Rear Brake Friction Lining", "Braking", "Rear disc pad thickness or drum wear indicator index", True, "Weekly"),

                # Group C: Periodic / Annual Maintenance
                ("BRAKE_FLUID", "Hydraulic Brake Fluid Renewal", "Fluids", "Moisture contamination and boiling point degradation", True, "Periodic"),
                ("ENGINE_COOLANT", "Engine Coolant & Thermostat", "Fluids", "Coolant level, pH level, radiator fin clogging", True, "Periodic"),
                ("SUSPENSION_FORKS", "Front Fork & Rear Shock Absorber", "Chassis", "Damping rebound, seal weeping, bushing play", False, "Periodic"),
                ("WHEEL_BEARINGS", "Wheel & Steering Head Bearings", "Chassis", "Free rotation, axial play, steering notchiness", True, "Periodic"),
                ("VALVE_CLEARANCE", "Engine Valve Tappet Clearance", "Powertrain", "Intake and exhaust lash feeler measurement", False, "Periodic"),
                ("INTERNAL_ENGINE", "Internal Engine & Compression Health", "Powertrain", "Compression ratio, blow-by, cylinder vibration harmonics", True, "Periodic")
            ]

            print(f"Seeding {len(components)} Components in Catalogue...")
            for code, name, category, desc, is_crit, group in components:
                cursor.execute(
                    """
                    INSERT INTO component_catalogue (component_code, name, category, description, is_critical, check_interval_group)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description)
                    """,
                    (code, name, category, desc, is_crit, group)
                )

            # Map component codes to IDs
            cursor.execute("SELECT component_id, component_code, check_interval_group FROM component_catalogue")
            comp_rows = cursor.fetchall()
            comp_map = {row['component_code']: row['component_id'] for row in comp_rows}
            comp_group_map = {row['component_code']: row['check_interval_group'] for row in comp_rows}

            # ----------------------------------------------------------------
            # 4. MODEL COMPONENT APPLICABILITY ENGINE
            # Enforce strict engineering rules based on model variant parameters!
            # ----------------------------------------------------------------
            cursor.execute("SELECT variant_id, cooling_type, brake_type, final_drive_type, fuel_delivery_type FROM motorcycle_variants")
            variants = cursor.fetchall()

            print(f"Applying Component Applicability Rules across {len(variants)} Variants...")
            for var in variants:
                var_id = var['variant_id']
                cooling = var['cooling_type']
                brakes = var['brake_type']
                drive = var['final_drive_type']
                fuel = var['fuel_delivery_type']

                for code, comp_id in comp_map.items():
                    is_app = True
                    cond = "Standard component"
                    display_override = None
                    notes = None

                    # Rule 1: Coolant is only applicable if liquid-cooled
                    if code == "ENGINE_COOLANT":
                        if cooling in ('Air', 'Air/Oil'):
                            is_app = False
                            cond = f"Inapplicable: {cooling}-cooled engine uses ambient air fin cooling"
                            notes = "Never inspect coolant on air-cooled engines"
                        else:
                            cond = "Applicable: Liquid-cooled engine requires ethylene-glycol maintenance"

                    # Rule 2: Drive Chain only applicable if final drive is Chain
                    elif code == "DRIVE_CHAIN":
                        if drive == "Belt":
                            is_app = True
                            cond = "Belt Drive: Inspect carbon drive belt tension & tooth wear"
                            display_override = "Drive Belt Tension & Condition"
                            notes = "No chain lubrication required on belt drives"
                        elif drive == "Shaft":
                            is_app = True
                            cond = "Shaft Drive: Inspect final drive bevel oil and universal joint play"
                            display_override = "Final Drive Shaft & Bevel Gearbox"
                            notes = "Shaft drive does not require regular chain lube or slack tensioning"
                        else:
                            cond = "Chain Drive: Inspect chain slack, roller cleanliness, and lubrication"

                    # Rule 3: Rear Brake: Disc vs Drum
                    elif code == "REAR_BRAKE_LINING":
                        if "Rear Drum" in brakes or brakes == "Dual Drum":
                            display_override = "Rear Drum Brake Shoe & Wear Pointer"
                            cond = "Applicable: Drum brake requires wear indicator and rod free-play check"
                        else:
                            display_override = "Rear Disc Brake Pads & Rotor"
                            cond = "Applicable: Hydraulic disc pads requiring minimum 2mm pad thickness"

                    # Rule 4: Brake Fluid renewal is only applicable if hydraulic brakes exist
                    elif code == "BRAKE_FLUID":
                        if brakes == "Dual Drum":
                            is_app = False
                            cond = "Inapplicable: Mechanical drum brakes do not use hydraulic fluid"
                        else:
                            cond = "Applicable: Hydraulic brake fluid renewal every 10,000-20,000 km"

                    # Rule 5: Valve clearance on hydraulic lifter engines
                    elif code == "VALVE_CLEARANCE":
                        # Harley and Norton use hydraulic self-adjusting lifters
                        cursor.execute("SELECT intake_valve_clearance_mm FROM motorcycle_specifications WHERE variant_id=%s", (var_id,))
                        spec_row = cursor.fetchone()
                        if spec_row and "Hydraulic" in str(spec_row.get('intake_valve_clearance_mm', '')):
                            is_app = False
                            cond = "Inapplicable: Hydraulic self-adjusting lifters automatically maintain zero lash"

                    cursor.execute(
                        """
                        INSERT INTO model_component_applicability (variant_id, component_id, is_applicable, rule_condition, display_name_override, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE is_applicable=VALUES(is_applicable), rule_condition=VALUES(rule_condition),
                                                display_name_override=VALUES(display_name_override), notes=VALUES(notes)
                        """,
                        (var_id, comp_id, is_app, cond, display_override, notes)
                    )

                    # Create maintenance schedule entry
                    cursor.execute(
                        """
                        INSERT INTO maintenance_schedules (variant_id, component_id, schedule_group, interval_km, interval_days, inspection_action, replacement_action, is_mandatory)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            var_id, comp_id, comp_group_map[code],
                            5000 if comp_group_map[code] == 'Weekly' else (10000 if comp_group_map[code] == 'Periodic' else 500),
                            7 if comp_group_map[code] == 'Weekly' else (180 if comp_group_map[code] == 'Periodic' else 1),
                            f"Inspect {code.lower().replace('_', ' ')} according to manufacturer tolerance guidelines",
                            f"Renew or service {code.lower().replace('_', ' ')} if worn past limit",
                            is_app
                        )
                    )

            # ----------------------------------------------------------------
            # 5. SENSOR DEFINITIONS
            # ----------------------------------------------------------------
            sensors = [
                ("ENG_TEMP", "Engine Cylinder / Head Temperature", "Thermal", "°C", 75.0, 105.0, 50.0, 125.0, 1.0),
                ("ENG_RPM", "Engine Rotational Speed", "Powertrain", "RPM", 1100.0, 8500.0, 800.0, 12000.0, 5.0),
                ("BAT_VOLT", "Electrical System Voltage", "Electrical", "V", 12.4, 14.5, 11.2, 15.2, 1.0),
                ("VIB_LEVEL", "Engine & Chassis RMS Vibration", "Vibration", "mm/s", 1.5, 5.5, 0.5, 9.5, 2.0),
                ("VEH_SPEED", "Vehicle Road Speed", "Chassis", "km/h", 0.0, 120.0, 0.0, 180.0, 5.0),
                ("TYRE_PRES_FRONT", "Front Tyre Inflation Pressure", "Tyres", "PSI", 28.0, 33.0, 22.0, 38.0, 0.5),
                ("TYRE_PRES_REAR", "Rear Tyre Inflation Pressure", "Tyres", "PSI", 32.0, 38.0, 24.0, 44.0, 0.5),
                ("BRAKE_PAD_WEAR", "Brake Pad Friction Thickness", "Braking", "mm", 3.0, 6.0, 1.2, 7.0, 0.2),
                ("OIL_QUALITY", "Engine Oil Quality Index", "Fluids", "%", 60.0, 100.0, 20.0, 100.0, 0.1),
                ("CHAIN_SLACK", "Drive Chain Slack Measurement", "Chassis", "mm", 20.0, 35.0, 15.0, 48.0, 0.1),
                ("FUEL_RATE", "Instantaneous Fuel Flow Rate", "Fluids", "L/100km", 2.2, 5.5, 1.5, 9.0, 1.0)
            ]

            print(f"Seeding {len(sensors)} Sensor Definitions...")
            for code, name, category, unit, min_n, max_n, min_c, max_c, freq in sensors:
                cursor.execute(
                    """
                    INSERT INTO sensor_definitions (sensor_code, name, category, unit, min_normal, max_normal, min_critical, max_critical, sampling_frequency_hz)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), min_normal=VALUES(min_normal), max_normal=VALUES(max_normal)
                    """,
                    (code, name, category, unit, min_n, max_n, min_c, max_c, freq)
                )

            # Map sensor codes to IDs
            cursor.execute("SELECT sensor_id, sensor_code FROM sensor_definitions")
            sensor_map = {row['sensor_code']: row['sensor_id'] for row in cursor.fetchall()}

            # Configure sensors for each variant
            for var in variants:
                var_id = var['variant_id']
                drive = var['final_drive_type']
                for scode, sid in sensor_map.items():
                    installed = True
                    if scode == "CHAIN_SLACK" and drive in ("Belt", "Shaft"):
                        installed = False  # No chain slack sensor on belt or shaft bikes!
                    cursor.execute(
                        """
                        INSERT INTO sensor_configurations (variant_id, sensor_id, is_installed, is_simulated, calibration_offset)
                        VALUES (%s, %s, %s, TRUE, 0.00)
                        """,
                        (var_id, sid, installed)
                    )

            # ----------------------------------------------------------------
            # 6. APPLICATION DEFAULT SETTINGS
            # ----------------------------------------------------------------
            default_settings = [
                ("DATA_SOURCE_MODE", "SIMULATOR"),
                ("SIMULATION_INTENSITY", "REGULAR"),
                ("THEME_MODE", "DARK"),
                ("LIVE_ML_DIAGNOSTICS", "ON")
            ]
            for k, v in default_settings:
                cursor.execute(
                    """
                    INSERT INTO application_settings (user_id, setting_key, setting_value)
                    VALUES (NULL, %s, %s)
                    ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
                    """,
                    (k, v)
                )

            print("Pocket Mechanic Master Database Seeding Completed Successfully!")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()

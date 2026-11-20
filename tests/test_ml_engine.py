import unittest
from modules.ml_engine import run_ml_inference

class TestMachineLearningEngine(unittest.TestCase):
    def test_nominal_vs_fault_inference(self):
        healthy_features = {
            'odometer_km': 6500, 'engine_hours': 180, 'ambient_temp': 30, 'vehicle_speed': 45,
            'engine_rpm': 3200, 'engine_temp': 88.5, 'battery_voltage': 14.2, 'vibration_level': 2.8,
            'tyre_pressure_front': 29.0, 'tyre_pressure_rear': 33.0, 'brake_pad_thickness': 4.5,
            'oil_quality_index': 88.0, 'chain_slack_mm': 26.0, 'fuel_rate': 3.1
        }
        res_healthy = run_ml_inference(healthy_features, model_name="Random_Forest")
        self.assertEqual(res_healthy['predicted_condition'], "Normal")
        self.assertEqual(res_healthy['fault_label'], "Nominal")
        self.assertGreater(res_healthy['confidence'], 0.80)
        self.assertGreater(res_healthy['remaining_life_km'], 5000.0)

        critical_features = {
            'odometer_km': 18500, 'engine_hours': 450, 'ambient_temp': 34, 'vehicle_speed': 40,
            'engine_rpm': 3100, 'engine_temp': 124.0, 'battery_voltage': 11.2, 'vibration_level': 8.8,
            'tyre_pressure_front': 28.0, 'tyre_pressure_rear': 21.0, 'brake_pad_thickness': 1.1,
            'oil_quality_index': 22.0, 'chain_slack_mm': 49.0, 'fuel_rate': 5.5
        }
        res_critical = run_ml_inference(critical_features, model_name="Random_Forest")
        self.assertIn(res_critical['predicted_condition'], ["Attention Required", "Urgent Attention Required"])
        self.assertNotEqual(res_critical['fault_label'], "Nominal")
        self.assertLess(res_critical['remaining_life_km'], 1500.0)

    def test_live_trace_generation(self):
        features = {
            'odometer_km': 5000, 'engine_hours': 120, 'ambient_temp': 28, 'vehicle_speed': 30,
            'engine_rpm': 2500, 'engine_temp': 86.0, 'battery_voltage': 14.1, 'vibration_level': 2.4,
            'tyre_pressure_front': 29.0, 'tyre_pressure_rear': 33.0, 'brake_pad_thickness': 4.8,
            'oil_quality_index': 92.0, 'chain_slack_mm': 27.0, 'fuel_rate': 2.8
        }
        res = run_ml_inference(features, model_name="Decision_Tree")
        self.assertTrue(len(res['live_trace']) >= 5)
        self.assertIn("PCA", res['live_trace'][2]['detail'])

if __name__ == '__main__':
    unittest.main()

import unittest
from modules.recommendations import MaintenanceRecommendationEngine

class TestRecommendationEngine(unittest.TestCase):
    def test_brake_safety_recommendation(self):
        ml_mock = {
            "predicted_condition": "Urgent Attention Required",
            "fault_label": "Brake_Thinning",
            "confidence": 0.94,
            "confidence_pct": 94.0,
            "model_used": "Random Forest",
            "remaining_life_km": 420.0
        }
        telemetry_mock = {
            "readings": {
                "ENG_TEMP": 88.0,
                "BRAKE_PAD_WEAR": 1.1,
                "BAT_VOLT": 14.1,
                "VIB_LEVEL": 2.5
            },
            "anomalies": ["BRAKE_PAD_WEAR"]
        }

        rec = MaintenanceRecommendationEngine.generate_recommendations(
            motorcycle_id=1,
            ml_result=ml_mock,
            telemetry=telemetry_mock
        )

        self.assertEqual(rec['overall_condition'], "Urgent Attention Required")
        self.assertEqual(rec['overall_priority'], "Critical")
        self.assertEqual(rec['status_color'], "red")
        self.assertTrue(rec['immediate_inspection_required'])
        self.assertIn("friction", rec['urgent_summary'].lower())

if __name__ == '__main__':
    unittest.main()

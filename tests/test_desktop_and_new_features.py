import unittest
import json
from app import create_app
from database.models import User
from database.connection import get_db_connection

class TestDesktopAndNewFeatures(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Find or use the default local user
        self.user = User.get_default_local_user()
        self.assertIsNotNone(self.user, "A local user must exist in MySQL for desktop testing.")

        # Get their active bike
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT motorcycle_id FROM motorcycles WHERE user_id = %s AND is_active = TRUE LIMIT 1",
                    (self.user.id,)
                )
                bike = cursor.fetchone()
                self.bike_id = bike['motorcycle_id'] if bike else None
        finally:
            conn.close()

    def test_health_check_endpoint(self):
        """Desktop launcher health probe endpoint."""
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('app'), 'Pocket Mechanic')

    def test_garage_page_authenticated(self):
        """Garage fleet & specifications overview."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            if self.bike_id:
                sess['active_motorcycle_id'] = self.bike_id

        res = self.client.get('/garage')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Garage & Motorcycle Specifications", res.data)
        self.assertIn(b"Technical Specifications", res.data)

    def test_settings_page_authenticated(self):
        """Settings, local database health, and rider profiles."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            if self.bike_id:
                sess['active_motorcycle_id'] = self.bike_id

        res = self.client.get('/settings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Settings & Local Data Management", res.data)
        self.assertIn(b"Offline MySQL Storage Diagnostics", res.data)
        self.assertIn(b"pocket_mechanic_db", res.data)

    def test_schedule_page_authenticated(self):
        """Maintenance schedule & inspection checklists."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            if self.bike_id:
                sess['active_motorcycle_id'] = self.bike_id

        res = self.client.get('/schedule')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Maintenance Schedule & Inspection Checklists", res.data)
        self.assertIn(b"Pre-Ride Safety Checklist", res.data)

    def test_offline_data_export(self):
        """Verifies JSON data backup contains complete vehicle and diagnostic history."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)

        res = self.client.get('/api/data/export')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/json')
        data = json.loads(res.data)
        self.assertEqual(data.get('application'), 'Pocket Mechanic Desktop')
        self.assertIn('rider', data)
        self.assertIn('motorcycles', data)
        self.assertIn('diagnostic_tickets', data)
        self.assertIn('maintenance_records', data)

    def test_log_quick_inspection_api(self):
        """Verifies digital inspection checklist logs to maintenance records in MySQL."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            if self.bike_id:
                sess['active_motorcycle_id'] = self.bike_id

        payload = {
            "motorcycle_id": self.bike_id,
            "checklist_title": "Automated Test Inspection",
            "notes": "Verified chain tension, brake pads, and tyre pressures.",
            "odometer_reading_km": 5200
        }
        res = self.client.post('/api/history/log-inspection', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('record_id', data)

    def test_update_motorcycle_api(self):
        """Verifies updating odometer and motorcycle details."""
        if not self.bike_id:
            return
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            sess['active_motorcycle_id'] = self.bike_id

        payload = {
            "current_odometer_km": 5350,
            "colour": "Matte Obsidian"
        }
        res = self.client.post(f'/api/motorcycles/update/{self.bike_id}', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

if __name__ == '__main__':
    unittest.main()

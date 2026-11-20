import unittest
from app import create_app
from database.connection import get_db_connection

class TestEndToEndFlow(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Clean up existing test user if present
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE email = 'moksh.test@pocketmechanic.local'")
        finally:
            conn.close()

    def test_full_user_lifecycle(self):
        # 1. Register User & Bike
        reg_data = {
            "full_name": "Moksh Suthar",
            "email": "moksh.test@pocketmechanic.local",
            "city": "Pune",
            "state": "Maharashtra",
            "licence_number": "MH12-2022009876",
            "password": "Password@123",
            "confirm_password": "Password@123",
            "manufacturer_id": "22", # Royal Enfield
            "model_id": "1",          # Classic 350
            "manufacturing_year": "2023",
            "colour": "Halcyon Black",
            "registration_number": "MH 12 AB 9999"
        }
        res_reg = self.client.post('/auth/register', data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b"Classic 350", res_reg.data)
        self.assertIn(b"Moksh Suthar", res_reg.data)

        # 2. Check Garage Dashboard
        res_home = self.client.get('/dashboard')
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b"Halcyon Black", res_home.data)
        self.assertIn(b"MH 12 AB 9999", res_home.data)

        # 3. Execute Diagnostic Session
        diag_payload = {
            "component_code": "BRAKE_PADS",
            "problem_category": "Braking Dynamics",
            "problem_description": "Front brake lever travel feels excessive",
            "model_name": "Random_Forest"
        }
        res_diag = self.client.post('/api/diagnostics/execute', json=diag_payload)
        self.assertEqual(res_diag.status_code, 200)
        diag_json = res_diag.get_json()
        self.assertTrue(diag_json['success'])
        self.assertIn("ticket_id", diag_json)
        ticket_id = diag_json['ticket_id']
        self.assertGreater(ticket_id, 0)
        self.assertIn(diag_json['predicted_condition'], ["Normal", "Attention Required", "Urgent Attention Required"])
        self.assertGreater(diag_json['ml_engine']['confidence_pct'], 50.0)

        # 4. View Diagnostic Report
        res_rep = self.client.get(f'/diagnostics/report/{ticket_id}')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b"Official Diagnostic Document", res_rep.data)
        self.assertIn(b"Royal Enfield Classic 350", res_rep.data)

        # 5. Chat with Wrenchy AI
        chat_payload = {
            "message": "Why does my front brake feel spongy?",
            "conversation_id": None
        }
        res_chat = self.client.post('/api/wrenchy/chat', json=chat_payload)
        self.assertEqual(res_chat.status_code, 200)
        chat_json = res_chat.get_json()
        self.assertIn("reply", chat_json)
        self.assertTrue(len(chat_json['reply']) > 20)

        # 6. Ticket Lifecycle: Resolve and Reopen
        res_res = self.client.post(f'/api/diagnostics/ticket/{ticket_id}/status', json={"status": "Resolved"})
        self.assertEqual(res_res.status_code, 200)
        res_reop = self.client.post(f'/api/diagnostics/ticket/{ticket_id}/status', json={"status": "Reopened"})
        self.assertEqual(res_reop.status_code, 200)

        # 7. Add Maintenance Service Record
        rec_payload = {
            "service_type": "Front Brake Pad Replacement",
            "service_date": "2026-11-20",
            "odometer_reading_km": 5200,
            "service_center": "Royal Enfield Authorized Service",
            "total_cost": 1850,
            "description": "Replaced worn front brake pads with OEM Brembo sintered pads. Fresh DOT 4 fluid bleed.",
            "ticket_id": ticket_id
        }
        res_rec = self.client.post('/api/history/add-record', json=rec_payload)
        self.assertEqual(res_rec.status_code, 200)
        rec_json = res_rec.get_json()
        self.assertTrue(rec_json['success'])

        print("End-to-End User Lifecycle & Diagnostic Workflow successfully verified!")

if __name__ == '__main__':
    unittest.main()

import unittest
from app import create_app
from database.connection import get_db_connection

class TestDiagnosticsEndToEnd(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_welcome_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pocket Mechanic", response.data)
        self.assertIn(b"Intelligent Motorcycle", response.data)

    def test_login_page(self):
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rider Authentication", response.data)

    def test_register_page(self):
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Part A: Rider Credentials", response.data)
        self.assertIn(b"Part B: Motorcycle Registration", response.data)

if __name__ == '__main__':
    unittest.main()

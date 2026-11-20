import unittest
from database.connection import encrypt_licence, decrypt_licence, mask_licence, get_db_connection
from database.models import User
from werkzeug.security import generate_password_hash, check_password_hash

class TestAuthAndSecurity(unittest.TestCase):
    def test_licence_encryption_and_masking(self):
        original = "MH12-2023004921"
        encrypted = encrypt_licence(original)
        self.assertNotEqual(original, encrypted)
        decrypted = decrypt_licence(encrypted)
        self.assertEqual(original, decrypted)
        masked = mask_licence(original)
        self.assertTrue(masked.startswith("MH12"))
        self.assertTrue(masked.endswith("4921"))
        self.assertIn("••••", masked)

    def test_password_hashing(self):
        pwd = "Motorcycle@2026!"
        h = generate_password_hash(pwd)
        self.assertTrue(check_password_hash(h, pwd))
        self.assertFalse(check_password_hash(h, "wrongpassword"))

    def test_user_query_isolation(self):
        user = User.get_by_email("nonexistent@example.com")
        self.assertIsNone(user)

if __name__ == '__main__':
    unittest.main()

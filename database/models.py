from flask_login import UserMixin
from database.connection import get_db_connection, decrypt_licence, mask_licence

class User(UserMixin):
    def __init__(self, user_id, full_name, email, city, state, encrypted_licence, licence_last4):
        self.id = user_id
        self.user_id = user_id
        self.full_name = full_name
        self.email = email
        self.city = city
        self.state = state
        self.encrypted_licence = encrypted_licence
        self.licence_last4 = licence_last4

    @property
    def masked_licence(self):
        decrypted = decrypt_licence(self.encrypted_licence)
        return mask_licence(decrypted)

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, full_name, email, city, state, encrypted_licence, licence_last4
                    FROM users WHERE user_id = %s
                    """,
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    return User(
                        row['user_id'],
                        row['full_name'],
                        row['email'],
                        row['city'],
                        row['state'],
                        row['encrypted_licence'],
                        row['licence_last4']
                    )
                return None
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT u.user_id, u.full_name, u.email, u.city, u.state, u.encrypted_licence, u.licence_last4,
                           c.password_hash
                    FROM users u
                    JOIN user_credentials c ON u.user_id = c.user_id
                    WHERE LOWER(u.email) = LOWER(%s)
                    """,
                    (email.strip(),)
                )
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_default_local_user():
        """Returns the default local user for seamless local desktop usage (no forced login)."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Prefer user with most recent login
                cursor.execute(
                    """
                    SELECT u.user_id, u.full_name, u.email, u.city, u.state, u.encrypted_licence, u.licence_last4
                    FROM users u
                    JOIN user_credentials c ON u.user_id = c.user_id
                    WHERE c.last_login_at IS NOT NULL
                    ORDER BY c.last_login_at DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                # 2. Otherwise pick first registered user
                if not row:
                    cursor.execute(
                        """
                        SELECT user_id, full_name, email, city, state, encrypted_licence, licence_last4
                        FROM users
                        ORDER BY user_id ASC
                        LIMIT 1
                        """
                    )
                    row = cursor.fetchone()

                if row:
                    return User(
                        row['user_id'],
                        row['full_name'],
                        row['email'],
                        row['city'],
                        row['state'],
                        row['encrypted_licence'],
                        row['licence_last4']
                    )
                return None
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        """Returns all registered local riders for the profile switch list."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT u.user_id, u.full_name, u.email, u.city, u.state, u.licence_last4,
                           COUNT(m.motorcycle_id) as bike_count
                    FROM users u
                    LEFT JOIN motorcycles m ON u.user_id = m.user_id AND m.is_active = TRUE
                    GROUP BY u.user_id, u.full_name, u.email, u.city, u.state, u.licence_last4
                    ORDER BY u.user_id ASC
                    """
                )
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_last_authenticated_user():
        """Returns the most recently logged-in user and their primary motorcycle for the Welcome page."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT u.user_id, u.full_name, u.email, c.last_login_at,
                           m.motorcycle_id, m.custom_make, m.custom_model, m.colour, m.registration_number,
                           mm.name as model_name, mfg.name as mfg_name
                    FROM users u
                    JOIN user_credentials c ON u.user_id = c.user_id
                    LEFT JOIN motorcycles m ON u.user_id = m.user_id AND m.is_active = TRUE
                    LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                    LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                    WHERE c.last_login_at IS NOT NULL
                    ORDER BY c.last_login_at DESC
                    LIMIT 1
                    """
                )
                return cursor.fetchone()
        finally:
            conn.close()

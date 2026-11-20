import os
import json
import pymysql
import pymysql.cursors
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

# Initialize Fernet cipher
_fernet = Fernet(Config.ENCRYPTION_KEY.encode() if isinstance(Config.ENCRYPTION_KEY, str) else Config.ENCRYPTION_KEY)

# SQLAlchemy engine & session
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **Config.SQLALCHEMY_ENGINE_OPTIONS
)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db_connection():
    """Returns a direct PyMySQL connection with DictCursor."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def encrypt_licence(licence_number: str) -> str:
    """Encrypts driving licence number at rest using AES-Fernet."""
    if not licence_number:
        return ""
    clean = licence_number.strip().upper()
    return _fernet.encrypt(clean.encode()).decode()

def decrypt_licence(encrypted_licence: str) -> str:
    """Decrypts driving licence number."""
    if not encrypted_licence:
        return ""
    try:
        return _fernet.decrypt(encrypted_licence.encode()).decode()
    except Exception:
        return "[ENCRYPTION_ERROR]"

def mask_licence(licence_number: str) -> str:
    """Masks licence for UI display, e.g. MH12-••••-3492."""
    if not licence_number:
        return "N/A"
    clean = licence_number.strip().upper()
    if len(clean) <= 4:
        return "••••" + clean
    return f"{clean[:4]}-••••-{clean[-4:]}"

def log_audit(user_id, action, entity_type, entity_id, details=None, ip_address="127.0.0.1"):
    """Records an audit log entry in MySQL."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            details_json = json.dumps(details) if details is not None else None
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details_json, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, action, entity_type, str(entity_id), details_json, ip_address)
            )
    finally:
        conn.close()

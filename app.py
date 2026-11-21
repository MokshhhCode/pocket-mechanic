import os
from flask import Flask, session, request, jsonify
from flask_login import LoginManager, current_user, login_user
from config import Config
from database.models import User
from database.connection import get_db_connection

from modules.auth import auth_bp
from modules.dashboard import dashboard_bp
from modules.motorcycle import motorcycle_bp
from modules.diagnostics import diagnostics_bp
from modules.history import history_bp
from modules.telemetry import telemetry_bp
from modules.wrenchy import wrenchy_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please sign in to access Pocket Mechanic."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Health check endpoint for native desktop launcher & process monitoring
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "app": "Pocket Mechanic",
            "version": "1.0.0",
            "mode": "desktop-local"
        })

    # Register Modular Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(motorcycle_bp)
    app.register_blueprint(diagnostics_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(wrenchy_bp)

    # Global Template Context Processor (Exposes Dev Toolbar settings & active motorcycle)
    @app.context_processor
    def inject_global_context():
        # Read persistent theme preference from session, cookie, or default DARK
        client_cookie_theme = request.cookies.get('pm_theme', '').upper()
        session_theme = session.get('THEME_MODE', '').upper()
        active_theme = session_theme if session_theme in ("LIGHT", "DARK") else (client_cookie_theme if client_cookie_theme in ("LIGHT", "DARK") else None)

        dev_settings = {
            "DATA_SOURCE_MODE": "SIMULATOR",
            "SIMULATION_INTENSITY": "REGULAR",
            "THEME_MODE": active_theme or "DARK",
            "LIVE_ML_DIAGNOSTICS": "ON"
        }
        active_bike_summary = None
        user_bikes_list = []

        if current_user.is_authenticated:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # User settings (NULL defaults loaded first, user-specific overrides second)
                    cursor.execute(
                        """
                        SELECT setting_key, setting_value FROM application_settings
                        WHERE user_id = %s OR user_id IS NULL
                        ORDER BY (user_id IS NOT NULL) ASC, updated_at ASC
                        """,
                        (current_user.id,)
                    )
                    db_theme = None
                    for r in cursor.fetchall():
                        dev_settings[r['setting_key']] = r['setting_value']
                        if r['setting_key'] == 'THEME_MODE':
                            db_theme = r['setting_value'].upper()

                    # If user has an explicit theme preference from session or cookie, respect it
                    if active_theme in ("LIGHT", "DARK"):
                        dev_settings["THEME_MODE"] = active_theme
                        session['THEME_MODE'] = active_theme
                        # Sync DB if it differs
                        if db_theme != active_theme:
                            cursor.execute(
                                """
                                INSERT INTO application_settings (user_id, setting_key, setting_value)
                                VALUES (%s, 'THEME_MODE', %s)
                                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), updated_at = CURRENT_TIMESTAMP
                                """,
                                (current_user.id, active_theme)
                            )
                    else:
                        db_t = dev_settings.get("THEME_MODE", "DARK").upper()
                        if db_t not in ("LIGHT", "DARK"):
                            db_t = "DARK"
                        dev_settings["THEME_MODE"] = db_t
                        session['THEME_MODE'] = db_t

                    # User bikes
                    cursor.execute(
                        """
                        SELECT m.motorcycle_id, m.registration_number, m.colour,
                               mm.name as model_name, mfg.name as mfg_name
                        FROM motorcycles m
                        LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                        LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                        LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                        WHERE m.user_id = %s AND m.is_active = TRUE
                        ORDER BY m.created_at DESC
                        """,
                        (current_user.id,)
                    )
                    user_bikes_list = cursor.fetchall()

                    active_id = session.get('active_motorcycle_id')
                    if active_id:
                        cursor.execute(
                            """
                            SELECT m.motorcycle_id, m.registration_number, m.colour, m.manufacturing_year,
                                   mm.name as model_name, mfg.name as mfg_name, mfg.logo_slug
                            FROM motorcycles m
                            LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                            LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                            LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                            WHERE m.motorcycle_id = %s
                            """,
                            (active_id,)
                        )
                        active_bike_summary = cursor.fetchone()
            finally:
                conn.close()
        else:
            if active_theme in ("LIGHT", "DARK"):
                session['THEME_MODE'] = active_theme
                dev_settings["THEME_MODE"] = active_theme
            else:
                session['THEME_MODE'] = dev_settings["THEME_MODE"]

        return {
            "dev_settings": dev_settings,
            "active_bike_summary": active_bike_summary,
            "user_bikes_list": user_bikes_list
        }

    # Automatically synchronize theme cookie with active session theme on every request
    @app.after_request
    def set_theme_cookie(response):
        theme = session.get('THEME_MODE')
        if theme in ('LIGHT', 'DARK'):
            if request.cookies.get('pm_theme') != theme.lower():
                response.set_cookie('pm_theme', theme.lower(), max_age=31536000, samesite='Lax', path='/')
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=True)

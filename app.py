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

    # Seamless Local-First Authentication: Auto-login local rider without login wall
    @app.before_request
    def auto_authenticate_local_rider():
        if app.config.get('TESTING'):
            return

        endpoint = request.endpoint or ""
        # Don't auto-login if the user is explicitly on auth screens or welcome or fetching static assets/health
        if endpoint in ('dashboard.welcome', 'health_check') or endpoint.startswith('auth.') or endpoint.startswith('static'):
            return

        if not current_user.is_authenticated:
            default_user = User.get_default_local_user()
            if default_user:
                login_user(default_user, remember=True)
                if 'active_motorcycle_id' not in session:
                    conn = get_db_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(
                                "SELECT motorcycle_id FROM motorcycles WHERE user_id = %s AND is_active = TRUE ORDER BY motorcycle_id ASC LIMIT 1",
                                (default_user.id,)
                            )
                            bike = cursor.fetchone()
                            if bike:
                                session['active_motorcycle_id'] = bike['motorcycle_id']
                    finally:
                        conn.close()

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
        dev_settings = {
            "DATA_SOURCE_MODE": "SIMULATOR",
            "SIMULATION_INTENSITY": "REGULAR",
            "THEME_MODE": "DARK",
            "LIVE_ML_DIAGNOSTICS": "ON"
        }
        active_bike_summary = None
        user_bikes_list = []

        if current_user.is_authenticated:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # User settings
                    cursor.execute(
                        "SELECT setting_key, setting_value FROM application_settings WHERE user_id = %s OR user_id IS NULL",
                        (current_user.id,)
                    )
                    for r in cursor.fetchall():
                        dev_settings[r['setting_key']] = r['setting_value']

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

        return {
            "dev_settings": dev_settings,
            "active_bike_summary": active_bike_summary,
            "user_bikes_list": user_bikes_list
        }

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=True)

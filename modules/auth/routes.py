import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_db_connection, encrypt_licence, log_audit
from database.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email address and password.", "danger")
            return render_template('auth/login.html')

        user_row = User.get_by_email(email)
        if not user_row or not check_password_hash(user_row['password_hash'], password):
            flash("Invalid email or password credentials. Please try again.", "danger")
            return render_template('auth/login.html')

        user = User(
            user_row['user_id'],
            user_row['full_name'],
            user_row['email'],
            user_row['city'],
            user_row['state'],
            user_row['encrypted_licence'],
            user_row['licence_last4']
        )
        login_user(user, remember=True)

        # Update last login timestamp in MySQL
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE user_credentials SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                    (user.id,)
                )
                # Select user's first active motorcycle and store in session
                cursor.execute(
                    "SELECT motorcycle_id FROM motorcycles WHERE user_id = %s AND is_active = TRUE LIMIT 1",
                    (user.id,)
                )
                bike = cursor.fetchone()
                if bike:
                    session['active_motorcycle_id'] = bike['motorcycle_id']
        finally:
            conn.close()

        log_audit(user.id, "USER_LOGIN", "users", user.id, {"email": user.email})
        return redirect(url_for('dashboard.home'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        # Part A: User Details
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        licence = request.form.get('licence_number', '').strip().upper()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Part B: Motorcycle Details
        mfg_id = request.form.get('manufacturer_id')
        model_id = request.form.get('model_id')
        custom_make = request.form.get('custom_make', '').strip()
        custom_model = request.form.get('custom_model', '').strip()
        mfg_year = request.form.get('manufacturing_year')
        colour = request.form.get('colour', '').strip()
        reg_number = request.form.get('registration_number', '').strip().upper()

        # Validations
        if not full_name or not email or not password or not licence or not reg_number:
            flash("All required personal and motorcycle registration fields must be completed.", "danger")
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.register'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('auth.register'))

        # Check existing email
        if User.get_by_email(email):
            flash("An account with this email address already exists. Please sign in.", "warning")
            return redirect(url_for('auth.login'))

        # Security: Encrypt licence at rest, store last 4 for verification
        encrypted_licence_val = encrypt_licence(licence)
        licence_last4_val = licence[-4:] if len(licence) >= 4 else licence
        pwd_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Insert User
                cursor.execute(
                    """
                    INSERT INTO users (full_name, email, city, state, encrypted_licence, licence_last4)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (full_name, email, city, state, encrypted_licence_val, licence_last4_val)
                )
                user_id = cursor.lastrowid

                # 2. Insert Credentials
                cursor.execute(
                    """
                    INSERT INTO user_credentials (user_id, password_hash, last_login_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    """,
                    (user_id, pwd_hash)
                )

                # 3. Insert Motorcycle
                variant_id = None
                if model_id and model_id.isdigit():
                    cursor.execute("SELECT variant_id FROM motorcycle_variants WHERE model_id = %s LIMIT 1", (int(model_id),))
                    v_row = cursor.fetchone()
                    if v_row:
                        variant_id = v_row['variant_id']

                cursor.execute(
                    """
                    INSERT INTO motorcycles (user_id, variant_id, custom_make, custom_model, manufacturing_year, colour, registration_number, current_odometer_km, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 5000, TRUE)
                    """,
                    (
                        user_id, variant_id,
                        custom_make if not variant_id else None,
                        custom_model if not variant_id else None,
                        int(mfg_year) if mfg_year and mfg_year.isdigit() else 2023,
                        colour or "Obsidian Black",
                        reg_number
                    )
                )
                bike_id = cursor.lastrowid

                # 4. Insert Default User Settings
                settings = [
                    (user_id, "DATA_SOURCE_MODE", "SIMULATOR"),
                    (user_id, "SIMULATION_INTENSITY", "REGULAR"),
                    (user_id, "THEME_MODE", "DARK"),
                    (user_id, "LIVE_ML_DIAGNOSTICS", "ON")
                ]
                cursor.executemany(
                    "INSERT INTO application_settings (user_id, setting_key, setting_value) VALUES (%s, %s, %s)",
                    settings
                )

            log_audit(user_id, "USER_REGISTERED", "users", user_id, {"email": email, "bike_id": bike_id})

            # Auto-login newly registered user
            user = User(user_id, full_name, email, city, state, encrypted_licence_val, licence_last4_val)
            login_user(user)
            session['active_motorcycle_id'] = bike_id
            flash("Registration complete! Welcome to Pocket Mechanic.", "success")
            return redirect(url_for('dashboard.home'))

        except Exception as e:
            flash(f"Registration failed due to a database error: {e}", "danger")
            return redirect(url_for('auth.register'))
        finally:
            conn.close()

    # GET request: load manufacturers catalogue for searchable dropdown
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT manufacturer_id, name, country FROM manufacturers WHERE is_active = TRUE ORDER BY name ASC")
            manufacturers = cursor.fetchall()
    finally:
        conn.close()

    return render_template('auth/register.html', manufacturers=manufacturers)

@auth_bp.route('/logout')
@login_required
def logout():
    uid = current_user.id
    log_audit(uid, "USER_LOGOUT", "users", uid)
    logout_user()
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('dashboard.welcome'))

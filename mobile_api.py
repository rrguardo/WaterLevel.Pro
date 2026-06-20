import hashlib
import logging

import requests
from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user

import db
import email_tools
import settings

mobile_api_bp = Blueprint('mobile_api', __name__)

RECAPTCHA_SECRET_KEY = settings.APP_RECAPTCHA_SECRET_KEY


def _validate_recaptcha(response_token):
    if settings.DEV_MODE or not RECAPTCHA_SECRET_KEY:
        return True
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': response_token,
    }
    resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    return resp.json().get('success', False)


@mobile_api_bp.route('/login', methods=['POST'])
def mobile_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')
    recaptcha_token = data.get('recaptcha_token', '')
    remember = data.get('remember', False)

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    if not settings.DEV_MODE:
        if not recaptcha_token:
            return jsonify({"error": "recaptcha_token is required"}), 400
        if not _validate_recaptcha(recaptcha_token):
            return jsonify({"error": "reCAPTCHA verification failed"}), 403

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user_data = db.try_login(email, password_hash)

    if not user_data or user_data.passw != password_hash:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user_data.confirmed:
        return jsonify({"error": "Email not confirmed. Check your inbox."}), 403

    user = db.User(user_data.id, user_data.email, user_data.passw, user_data.is_admin)
    login_user(user, remember=remember)

    return jsonify({
        "success": True,
        "user": {
            "id": user_data.id,
            "email": user_data.email,
            "is_admin": bool(user_data.is_admin),
        },
    })


@mobile_api_bp.route('/register', methods=['POST'])
def mobile_register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')
    recaptcha_token = data.get('recaptcha_token', '')

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    if not settings.DEV_MODE:
        if not recaptcha_token:
            return jsonify({"error": "recaptcha_token is required"}), 400
        if not _validate_recaptcha(recaptcha_token):
            return jsonify({"error": "reCAPTCHA verification failed"}), 403

    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError:
        return jsonify({"error": "Invalid email address"}), 400

    if not db.valid_4register(email):
        return jsonify({"error": "Email already registered or pending confirmation"}), 409

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if not db.add_user(email, password_hash):
        return jsonify({"error": "Failed to create user"}), 500

    email_tools.send_register_email(email)

    return jsonify({
        "success": True,
        "message": "Registration successful. Check your email to confirm.",
    }), 201


@mobile_api_bp.route('/me', methods=['GET'])
@login_required
def mobile_me():
    user_data = db.get_user_by_id(current_user.id)
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.username,
            "is_admin": current_user.is_admin,
            "phone": user_data.phone if user_data else None,
        },
    })


@mobile_api_bp.route('/logout', methods=['POST'])
@login_required
def mobile_logout():
    logout_user()
    return jsonify({"success": True})


@mobile_api_bp.route('/devices', methods=['GET'])
@login_required
def mobile_devices():
    devices = current_user.get_devices()
    result = []
    for d in devices:
        result.append({
            "public_key": d.public_key,
            "name": d.name,
            "type": d.type,
            "type_name": d.long_name,
            "can_admin": bool(d.can_admin),
        })
    return jsonify({"devices": result})


@mobile_api_bp.route('/settings', methods=['GET'])
@login_required
def mobile_get_settings():
    settings_data = db.User.get_user_settings(current_user.id)
    return jsonify({"settings": settings_data})


@mobile_api_bp.route('/settings', methods=['PUT'])
@login_required
def mobile_update_settings():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    setting_name = data.get('setting_name', '').strip()
    setting_value = data.get('setting_value', '').strip()

    if not setting_name:
        return jsonify({"error": "setting_name is required"}), 400

    current_user.set_setting(setting_name, setting_value)
    return jsonify({"success": True})

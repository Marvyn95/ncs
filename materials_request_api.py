import json
from flask import request, jsonify
from __init__ import app, db, bcrypt
from functools import wraps


with open('../config.json') as config_file:
    config = json.load(config_file)


@app.route('/api/get_api_key', methods=['POST'])
def get_api_key():
    data = request.get_json() or {}
    api_user = db.ApiUsers.find_one({"email": data.get("email")})
    if not api_user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    if not bcrypt.check_password_hash(api_user.get("password"), data.get("password")):
        return jsonify({"status": "error", "message": "Invalid password"}), 401
    api_key = app.config['API_KEY']
    return jsonify({"status": "success", "api_key": api_key}), 200

# API key decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = str(request.headers.get('x-api-key'))
        if not api_key:
            return jsonify({"status": "error", "message": "API key is missing in request header, Access denied"}), 401
        if api_key != app.config['API_KEY']:
            return jsonify({"status": "error", "message": "Invalid API key, Access denied"}), 403
        return f(*args, **kwargs)
    return decorated_function

# api user registration
@app.route('/api/register', methods=['POST'])
@require_api_key
def api_register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    admin_password = data.get("admin_password")

    print(email, password)

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400

    if db.ApiUsers.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Email already registered"}), 400

    if admin_password != config.get("ADMIN_PASSWORD"):
        return jsonify({"status": "error", "message": "Invalid admin password"}), 403

    result = db.ApiUsers.insert_one({
        "email": email,
        "password": bcrypt.generate_password_hash(password.strip()).decode("utf-8")
    })
    
    return jsonify({"status": "success",
                    "email": email,
                    "message": "User registered successfully",
                    "user_id": str(result.inserted_id),
                }), 200

# get all current schemes
@app.route('/api/current_schemes', methods=['GET'])
@require_api_key
def current_schemes():
    schemes = list(db.Schemes.find())
    for scheme in schemes:
        scheme["_id"] = str(scheme["_id"])
    return jsonify({"status": "success", "schemes": schemes, "count": len(schemes)})

from flask import Flask, request, jsonify, g
from flask_cors import CORS  # Add CORS support
import sqlite3
from functools import wraps
import os
from example import verify_user, create_session, verify_session, get_user_roles

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing username or password"}), 400
        
    user_id = verify_user(data["username"], data["password"])
    if not user_id:
        return jsonify({"error": "Invalid credentials"}), 401
        
    session_token = create_session(user_id)
    roles = get_user_roles(user_id)
    
    return jsonify({
        "user_id": user_id,
        "session_token": session_token,
        "roles": roles
    })

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = verify_session(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        return f(user_id, *args, **kwargs)
    return decorated

@app.route("/api/user", methods=["GET"])
@auth_required
def get_user_info(user_id):
    conn = sqlite3.connect("auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, first_name, last_name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "roles": get_user_roles(user_id)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
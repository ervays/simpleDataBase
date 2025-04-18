from flask import Flask, request, jsonify, g
from flask_cors import CORS  # Add CORS support
import sqlite3
from functools import wraps
import os
from example import verify_user, create_user, create_session, verify_session, get_user_roles

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure database schema is updated
try:
    from db_update import apply_schema_updates
    apply_schema_updates()
except Exception as e:
    print(f"Warning: Could not apply schema updates: {e}")

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

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = verify_session(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        # Check if user has admin role
        roles = get_user_roles(user_id)
        if "admin" not in roles:
            return jsonify({"error": "Admin privileges required"}), 403
        
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

@app.route("/api/users", methods=["POST"])
@admin_required
def create_new_user(admin_id):
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["username", "password", "email", "first_name", "last_name"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if username already exists
    conn = sqlite3.connect("auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (data["username"],))
    existing_user = cursor.fetchone()
    conn.close()
    
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409
    
    try:
        # Create new user
        new_user_id = create_user(
            data["username"],
            data["password"],
            data["email"],
            data["first_name"],
            data["last_name"]
        )
        
        # Assign default role (user)
        conn = sqlite3.connect("auth.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roles WHERE name = 'user'")
        role_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", 
                      (new_user_id, role_id))
        
        # Assign admin role if specified
        if data.get("is_admin", False):
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            admin_role_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", 
                         (new_user_id, admin_role_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "User created successfully",
            "user_id": new_user_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======= NEW API ENDPOINTS FOR TASKS AND REQUESTS =======

# Get all tasks for a user
@app.route("/api/tasks", methods=["GET"])
@auth_required
def get_tasks(user_id):
    conn = sqlite3.connect("auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get tasks where the user is an owner
    cursor.execute("""
        SELECT t.id, t.description, t.created_at
        FROM tasks t
        JOIN task_owners to_rel ON t.id = to_rel.task_id
        WHERE to_rel.user_id = ?
        ORDER BY t.created_at DESC
    """, (user_id,))
    
    tasks = []
    for row in cursor.fetchall():
        # Get all owners for each task
        cursor.execute("""
            SELECT u.id, u.username, u.first_name, u.last_name
            FROM users u
            JOIN task_owners to_rel ON u.id = to_rel.user_id
            WHERE to_rel.task_id = ?
        """, (row["id"],))
        
        owners = []
        for owner in cursor.fetchall():
            owners.append({
                "id": owner["id"],
                "username": owner["username"],
                "name": f"{owner['first_name']} {owner['last_name']}"
            })
        
        tasks.append({
            "id": row["id"],
            "description": row["description"],
            "created_at": row["created_at"],
            "owners": owners
        })
    
    conn.close()
    return jsonify({"tasks": tasks})

# Create a new task
@app.route("/api/tasks", methods=["POST"])
@auth_required
def create_task(user_id):
    data = request.get_json()
    
    if not data or "description" not in data:
        return jsonify({"error": "Missing description"}), 400
    
    # Default to current user as owner if not specified
    owner_ids = data.get("owner_ids", [user_id])
    
    # Ensure current user is included in owners
    if user_id not in owner_ids:
        owner_ids.append(user_id)
    
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()
    
    try:
        # Create the task
        cursor.execute(
            "INSERT INTO tasks (description) VALUES (?)",
            (data["description"],)
        )
        task_id = cursor.lastrowid
        
        # Add owners
        for owner_id in owner_ids:
            cursor.execute(
                "INSERT INTO task_owners (task_id, user_id) VALUES (?, ?)",
                (task_id, owner_id)
            )
        
        conn.commit()
        
        return jsonify({
            "message": "Task created successfully",
            "task_id": task_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Get all requests for a user
@app.route("/api/requests", methods=["GET"])
@auth_required
def get_requests(user_id):
    conn = sqlite3.connect("auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get requests made by this user
    cursor.execute("""
        SELECT r.id, r.description, r.created_at, 
               u.id as solicitor_id, u.username as solicitor_username,
               u.first_name as solicitor_first_name, u.last_name as solicitor_last_name
        FROM requests r
        JOIN users u ON r.solicitor_id = u.id
        WHERE r.solicitor_id = ?
        ORDER BY r.created_at DESC
    """, (user_id,))
    
    requests = []
    for row in cursor.fetchall():
        requests.append({
            "id": row["id"],
            "description": row["description"],
            "created_at": row["created_at"],
            "solicitor": {
                "id": row["solicitor_id"],
                "username": row["solicitor_username"],
                "name": f"{row['solicitor_first_name']} {row['solicitor_last_name']}"
            }
        })
    
    conn.close()
    return jsonify({"requests": requests})

# Create a new request
@app.route("/api/requests", methods=["POST"])
@auth_required
def create_request(user_id):
    data = request.get_json()
    
    if not data or "description" not in data:
        return jsonify({"error": "Missing description"}), 400
    
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()
    
    try:
        # Create the request with the current user as solicitor
        cursor.execute(
            "INSERT INTO requests (solicitor_id, description) VALUES (?, ?)",
            (user_id, data["description"])
        )
        request_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            "message": "Request created successfully",
            "request_id": request_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Get all users (for selecting task owners)
@app.route("/api/users", methods=["GET"])
@auth_required
def get_all_users(user_id):
    conn = sqlite3.connect("auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, first_name, last_name
        FROM users
        ORDER BY username
    """)
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row["id"],
            "username": row["username"],
            "name": f"{row['first_name']} {row['last_name']}"
        })
    
    conn.close()
    return jsonify({"users": users})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
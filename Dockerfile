FROM python:3.9-slim

# Install required dependencies
RUN apt-get update && apt-get install -y sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY schema.sql /app/
COPY example.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create and initialize the database with schema
RUN sqlite3 auth.db < schema.sql

# Create init script for adding admin user
RUN echo 'import sqlite3, hashlib, os, sys\n\
from example import create_user, get_db_connection\n\
\n\
# Create admin user\n\
user_id = create_user("admin", "admin", "admin@example.com", "Admin", "User")\n\
\n\
# Get database connection\n\
conn = get_db_connection()\n\
\n\
# Assign admin role\n\
try:\n\
    cursor = conn.cursor()\n\
    cursor.execute("SELECT id FROM roles WHERE name = \'admin\'")\n\
    role_id = cursor.fetchone()[\'id\']\n\
    cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))\n\
    conn.commit()\n\
    print("Admin user created successfully!")\n\
except Exception as e:\n\
    conn.rollback()\n\
    print(f"Error creating admin user: {e}")\n\
finally:\n\
    conn.close()\n\
' > create_admin.py

# Create API server script
RUN echo 'from flask import Flask, request, jsonify, g\n\
import sqlite3\n\
from functools import wraps\n\
import os\n\
from example import verify_user, create_session, verify_session, get_user_roles\n\
\n\
app = Flask(__name__)\n\
\n\
@app.route("/api/login", methods=["POST"])\n\
def login():\n\
    data = request.get_json()\n\
    if not data or "username" not in data or "password" not in data:\n\
        return jsonify({"error": "Missing username or password"}), 400\n\
        \n\
    user_id = verify_user(data["username"], data["password"])\n\
    if not user_id:\n\
        return jsonify({"error": "Invalid credentials"}), 401\n\
        \n\
    session_token = create_session(user_id)\n\
    roles = get_user_roles(user_id)\n\
    \n\
    return jsonify({\n\
        "user_id": user_id,\n\
        "session_token": session_token,\n\
        "roles": roles\n\
    })\n\
\n\
def auth_required(f):\n\
    @wraps(f)\n\
    def decorated(*args, **kwargs):\n\
        token = request.headers.get("Authorization")\n\
        if not token:\n\
            return jsonify({"error": "Authentication required"}), 401\n\
        \n\
        user_id = verify_session(token)\n\
        if not user_id:\n\
            return jsonify({"error": "Invalid or expired session"}), 401\n\
        \n\
        return f(user_id, *args, **kwargs)\n\
    return decorated\n\
\n\
@app.route("/api/user", methods=["GET"])\n\
@auth_required\n\
def get_user_info(user_id):\n\
    conn = sqlite3.connect("auth.db")\n\
    conn.row_factory = sqlite3.Row\n\
    cursor = conn.cursor()\n\
    cursor.execute("SELECT id, username, email, first_name, last_name FROM users WHERE id = ?", (user_id,))\n\
    user = cursor.fetchone()\n\
    conn.close()\n\
    \n\
    if not user:\n\
        return jsonify({"error": "User not found"}), 404\n\
        \n\
    return jsonify({\n\
        "id": user["id"],\n\
        "username": user["username"],\n\
        "email": user["email"],\n\
        "first_name": user["first_name"],\n\
        "last_name": user["last_name"],\n\
        "roles": get_user_roles(user_id)\n\
    })\n\
\n\
if __name__ == "__main__":\n\
    app.run(host="0.0.0.0", port=5000)\n\
' > api_server.py

# Create requirements.txt if it doesn't exist
RUN touch requirements.txt && \
    echo "Flask==2.0.1\n\
Werkzeug==2.0.1\n\
itsdangerous==2.0.1\n\
click==8.0.1\n\
Jinja2==3.0.1\n\
MarkupSafe==2.0.1\n" > requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Initialize admin user
RUN python create_admin.py

# Expose port for the API
EXPOSE 5000

# Start the API server when the container launches
CMD ["python", "api_server.py"]
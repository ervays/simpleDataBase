import sqlite3, hashlib, os, sys
from example import create_user, get_db_connection

# Create admin user
user_id = create_user("admin", "admin", "admin@example.com", "Admin", "User")

# Get database connection
conn = get_db_connection()

# Assign admin role
try:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
    role_id = cursor.fetchone()['id']
    cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
    conn.commit()
    print("Admin user created successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error creating admin user: {e}")
finally:
    conn.close()
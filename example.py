import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import uuid

# Database connection
def get_db_connection():
    conn = sqlite3.connect('auth.db')
    conn.row_factory = sqlite3.Row
    return conn

# User management functions
def create_user(username, password, email=None, first_name=None, last_name=None):
    """Create a new user with a hashed password"""
    # Generate a salt and hash the password
    salt = os.urandom(32)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    # Combine salt and hash for storage
    storage = salt + password_hash
    hex_hash = storage.hex()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (username, hex_hash, email, first_name, last_name)
        )
        user_id = cursor.lastrowid
        
        # Assign default 'user' role
        cursor.execute("SELECT id FROM roles WHERE name = 'user'")
        role_id = cursor.fetchone()['id']
        cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()

def verify_user(username, password):
    """Verify a user's login credentials"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ? AND is_active = 1", (username,))
        user = cursor.fetchone()
        
        if not user:
            return None
            
        stored_password = bytes.fromhex(user['password_hash'])
        salt = stored_password[:32]  # Get the salt
        key = stored_password[32:]   # Get the hash
        
        # Hash the provided password with the same salt
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        # Compare the hashes
        if new_hash == key:
            # Update last login time
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
            conn.commit()
            return user['id']
        return None
    finally:
        conn.close()

# Session management functions
def create_session(user_id, expires_in_days=1):
    """Create a new session for a user"""
    session_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=expires_in_days)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
            (user_id, session_token, expires_at)
        )
        conn.commit()
        return session_token
    finally:
        conn.close()

def verify_session(session_token):
    """Verify if a session is valid and not expired"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP",
            (session_token,)
        )
        session = cursor.fetchone()
        return session['user_id'] if session else None
    finally:
        conn.close()

# Role management functions
def get_user_roles(user_id):
    """Get all roles for a user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.name FROM roles r 
               JOIN user_roles ur ON r.id = ur.role_id 
               WHERE ur.user_id = ?""",
            (user_id,)
        )
        return [row['name'] for row in cursor.fetchall()]
    finally:
        conn.close()

def has_role(user_id, role_name):
    """Check if a user has a specific role"""
    return role_name in get_user_roles(user_id)

# Example usage
if __name__ == "__main__":
    # Create a new user
    user_id = create_user("testuser", "securepassword", "test@example.com", "Test", "User")
    print(f"Created user with ID: {user_id}")
    
    # Verify the user's credentials
    verified_id = verify_user("testuser", "securepassword")
    print(f"Verified user ID: {verified_id}")
    
    # Create a session
    if verified_id:
        session = create_session(verified_id)
        print(f"Created session token: {session}")
        
        # Check user roles
        roles = get_user_roles(verified_id)
        print(f"User roles: {roles}")
        
        # Verify session
        user_id = verify_session(session)
        print(f"Session verified for user ID: {user_id}")
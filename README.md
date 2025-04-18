# Simple Authentication Database

This repository contains a simple SQLite database schema for user authentication. It provides basic functionality for user management, role-based access control, and session tracking.

## Schema Structure

### Tables

1. **users** - Stores user credentials and personal information
   - `id`: Unique identifier (auto-incremented)
   - `username`: Unique username
   - `password_hash`: Password hash (NOT plaintext password!)
   - `email`: User's email address
   - `first_name`, `last_name`: User's name
   - `is_active`: User account status
   - `created_at`: Account creation timestamp
   - `last_login`: Last login timestamp

2. **roles** - Defines available roles in the system
   - `id`: Role identifier
   - `name`: Unique role name
   - `description`: Role description

3. **user_roles** - Maps users to roles (many-to-many relationship)
   - `user_id`: Reference to user
   - `role_id`: Reference to role

4. **sessions** - Tracks user authentication sessions
   - `id`: Session identifier
   - `user_id`: Reference to user
   - `session_token`: Unique session token
   - `expires_at`: Session expiration timestamp
   - `created_at`: Session creation timestamp

## Usage

### Creating the Database

Use the following commands to create the database:

```bash
# Create a new SQLite database
sqlite3 auth.db < schema.sql
```

### Python Example

Check the `example.py` file for a demonstration of how to interact with the database using Python.

## Security Notes

- Always store password hashes, never plaintext passwords
- Use a strong hashing algorithm like bcrypt or Argon2
- Implement proper session management
- Consider adding additional security features like rate limiting, multi-factor authentication, etc.
import sqlite3
import os

def apply_schema_updates():
    """Apply schema updates from the schema_update.sql file"""
    print("Applying database schema updates...")
    
    # Check if database exists
    if not os.path.exists("auth.db"):
        print("Error: Database file auth.db not found")
        return False
    
    # Connect to the database
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()
    
    try:
        # Read the schema update file
        with open("schema_update.sql", "r") as f:
            schema_sql = f.read()
        
        # Execute the schema update
        cursor.executescript(schema_sql)
        conn.commit()
        print("Schema updates applied successfully")
        return True
    except Exception as e:
        print(f"Error applying schema updates: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    apply_schema_updates()
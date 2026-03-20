#!/usr/bin/env python3
"""Test SQLite database write permissions"""
import sqlite3
import os

def test_sqlite_write():
    test_db = "data/test_write.db"

    # Ensure directory exists
    os.makedirs("data", exist_ok=True)

    # Clean up if exists
    if os.path.exists(test_db):
        os.remove(test_db)

    try:
        # Try to create and write to database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Create table
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

        # Insert data
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()

        # Read back
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()

        print(f"✓ Successfully wrote and read from database: {result}")

        conn.close()

        # Clean up
        os.remove(test_db)

        return True

    except Exception as e:
        print(f"✗ Failed to write to database: {e}")
        return False

if __name__ == "__main__":
    success = test_sqlite_write()
    exit(0 if success else 1)
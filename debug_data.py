#!/usr/bin/env python3
"""
Debug Data - Utility script for debugging data issues.
"""

import sqlite3
from pathlib import Path


def debug_data():
    """Debug the data in the database."""
    
    print("=" * 80)
    print("DEBUGGING DATA")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "db"
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nTables in database: {tables}\n")
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            except sqlite3.OperationalError as e:
                print(f"{table}: Error - {e}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    debug_data()

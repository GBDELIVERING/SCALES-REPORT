#!/usr/bin/env python3
"""
Find Columns - Utility to discover available data columns in the database.
"""

import sqlite3
from pathlib import Path


def find_data_columns():
    """Find and display all available columns in the database."""
    
    print("=" * 80)
    print("FINDING DATA COLUMNS")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "db"
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database.")
            return
        
        print(f"\nFound {len(tables)} tables:\n")
        
        for (table_name,) in tables:
            print(f"\n--- {table_name} ---")
            
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_id, col_name, col_type, not_null, default, pk = col
                    pk_marker = " [PK]" if pk else ""
                    null_marker = " NOT NULL" if not_null else ""
                    default_marker = f" DEFAULT {default}" if default else ""
                    print(f"  {col_name}: {col_type}{pk_marker}{null_marker}{default_marker}")
                    
            except sqlite3.OperationalError as e:
                print(f"  Error reading table: {e}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    find_data_columns()

#!/usr/bin/env python3
"""
Inspect Raw Data - Debug utility to examine raw data from the scales system.
Shows the first N rows to help diagnose parsing issues.
"""

import sqlite3
from pathlib import Path
import requests

# Import shared configuration
from export_scales_reports import DB_TABLE_NAMES


def inspect_raw_data(num_rows=30, service_url="http://localhost:9999"):
    """Inspect raw data from database or service."""
    
    print(f"First {num_rows} rows of raw data:")
    print("=" * 80)
    
    raw_rows = []
    db_path = Path(__file__).parent / "db"
    
    # Try web service first
    try:
        response = requests.get(f"{service_url}/transactions", timeout=10)
        if response.ok:
            data = response.text.strip().split('\n')
            raw_rows = data[:num_rows]
    except requests.exceptions.RequestException:
        pass
    
    # Fallback to database
    if not raw_rows and db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Try common table names (using shared configuration)
            for table_name in DB_TABLE_NAMES:
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT {num_rows}")
                    raw_rows = cursor.fetchall()
                    if raw_rows:
                        columns = [desc[0] for desc in cursor.description]
                        print(f"Table: {table_name}")
                        print(f"Columns: {columns}")
                        print("-" * 80)
                        break
                except sqlite3.OperationalError:
                    continue
            
            conn.close()
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
    
    # Display rows
    if raw_rows:
        for i, row in enumerate(raw_rows):
            print(f"\nRow {i}:")
            if isinstance(row, (tuple, list)):
                for j, val in enumerate(row):
                    print(f"  [{j}] {val}")
            else:
                print(f"  [{0}] {row}")
    else:
        print("No data found.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    inspect_raw_data()

#!/usr/bin/env python3
"""
Check Dates - Utility to check and validate date ranges in the data.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def check_dates():
    """Check date ranges in the database."""
    
    print("=" * 80)
    print("CHECKING DATE RANGES")
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
        
        # Look for date columns in each table
        for table in tables:
            print(f"\nTable: {table}")
            
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                date_columns = []
                for col in columns:
                    col_name = col[1].lower()
                    col_type = (col[2] or '').lower()
                    
                    # Check if column might be a date
                    if 'date' in col_name or 'time' in col_name or 'date' in col_type:
                        date_columns.append(col[1])
                
                if date_columns:
                    print(f"  Date columns found: {date_columns}")
                    
                    for date_col in date_columns:
                        try:
                            cursor.execute(f"""
                                SELECT MIN({date_col}), MAX({date_col}), COUNT(*)
                                FROM {table}
                                WHERE {date_col} IS NOT NULL
                            """)
                            min_date, max_date, count = cursor.fetchone()
                            print(f"    {date_col}: {min_date} to {max_date} ({count} records)")
                        except sqlite3.OperationalError:
                            pass
                else:
                    print("  No date columns found")
                    
            except sqlite3.OperationalError as e:
                print(f"  Error: {e}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_dates()

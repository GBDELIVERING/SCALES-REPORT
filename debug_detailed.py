#!/usr/bin/env python3
"""
Debug Detailed - Detailed debugging of data parsing issues.
"""

import sqlite3
from pathlib import Path


def debug_detailed():
    """Provide detailed debugging information."""
    
    print("=" * 80)
    print("DETAILED DATA DEBUG")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "db"
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check SQLite version
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"\nSQLite version: {version}")
        
        # Get database info
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchall()
        print(f"Database info: {db_info}")
        
        # Check page size and other settings
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        print(f"Page size: {page_size}")
        
        # List all tables with detailed info
        cursor.execute("""
            SELECT name, type, sql 
            FROM sqlite_master 
            WHERE type IN ('table', 'index', 'view')
            ORDER BY type, name
        """)
        objects = cursor.fetchall()
        
        print(f"\nDatabase objects ({len(objects)}):")
        for name, obj_type, sql in objects:
            print(f"\n  {obj_type.upper()}: {name}")
            if sql:
                # Truncate long SQL
                sql_preview = sql[:200] + "..." if len(sql) > 200 else sql
                print(f"    {sql_preview}")
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    debug_detailed()

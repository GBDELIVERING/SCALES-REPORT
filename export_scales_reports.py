#!/usr/bin/env python3
"""
Export Scales Reports - Enhanced reporting for scales transaction data.
Connects to EasyWebService and generates reports from transaction data.
"""

import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import csv
import os

# Shared configuration: table names to search in the database
# Used across multiple scripts for consistency
DB_TABLE_NAMES = ['TRANSACTIONS', 'TRANS', 'SALES', 'WEIGHING', 'SCALE_DATA', 'ITEM']


class ScalesReportExporter:
    """Handles fetching and processing scales transaction data."""
    
    def __init__(self, service_url="http://localhost:9999"):
        self.service_url = service_url
        self.db_path = Path(__file__).parent / "db"
        
    def connect_to_service(self):
        """Test connection to EasyWebService."""
        try:
            response = requests.get(f"{self.service_url}/status", timeout=5)
            if response.ok:
                print(f"✓ Connected to EasyWebService at {self.service_url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        # Fallback - check if we can connect at all
        try:
            response = requests.get(self.service_url, timeout=5)
            print(f"✓ Connected to EasyWebService at {self.service_url}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Could not connect to EasyWebService: {e}")
            print("  → Ensure the EasyWebService is running at the configured URL")
            print("  → Will attempt to use local database as fallback")
            return False
    
    def fetch_raw_transaction_data(self, start_date, end_date):
        """Fetch raw transaction data from the service or database."""
        print("\n[1] Fetching raw transaction data...")
        
        raw_rows = []
        
        # Try fetching from web service first
        try:
            params = {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
            response = requests.get(
                f"{self.service_url}/transactions",
                params=params,
                timeout=30
            )
            if response.ok:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                if isinstance(data, list):
                    raw_rows = data
                elif isinstance(data, str):
                    raw_rows = data.strip().split('\n')
        except requests.exceptions.RequestException:
            pass
        
        # If no data from service, try local database
        if not raw_rows and self.db_path.exists():
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                # Try to get transaction data from common table names
                for table_name in DB_TABLE_NAMES:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        raw_rows = cursor.fetchall()
                        if raw_rows:
                            # Get column names
                            self.column_names = [desc[0] for desc in cursor.description]
                            break
                    except sqlite3.OperationalError:
                        continue
                
                conn.close()
            except sqlite3.DatabaseError as e:
                print(f"  ⚠ Database error: {e}")
        
        print(f"  ✓ Retrieved {len(raw_rows)} rows (raw)")
        return raw_rows
    
    def parse_and_clean_data(self, raw_rows):
        """Parse raw data rows, filtering out metadata and invalid rows."""
        print("\n[2] Parsing and cleaning data...")
        
        valid_rows = []
        skipped_count = 0
        
        for i, row in enumerate(raw_rows):
            # Convert row to string for checking
            row_str = str(row) if not isinstance(row, str) else row
            row_str_stripped = row_str.strip()
            
            # Skip filter/metadata rows - these contain "Filter:" prefix
            # This is the key fix: Row 0 often contains filter metadata like:
            # "Filter: Date From=2026-04-01 00:00:00,Date To=2026-04-15 00:00:00"
            if self._is_metadata_row(row_str):
                skipped_count += 1
                continue
            
            # Skip empty rows
            if not row_str_stripped or row_str_stripped in ['None', 'null']:
                skipped_count += 1
                continue
            
            # Skip header rows (if they contain column names)
            if self._is_header_row(row_str):
                skipped_count += 1
                continue
            
            # Parse the row data
            parsed_row = self._parse_row(row)
            if parsed_row:
                valid_rows.append(parsed_row)
            else:
                skipped_count += 1
        
        if skipped_count > 0:
            print(f"  ⚠ Skipped {skipped_count} metadata/invalid rows")
        
        if valid_rows:
            print(f"  ✓ Found {len(valid_rows)} valid data rows")
        else:
            print("  ✗ No valid data rows found")
            print("  ✗ Could not parse transaction data")
        
        return valid_rows
    
    def _is_metadata_row(self, row_str):
        """Check if a row is a metadata/filter row that should be skipped."""
        row_lower = row_str.lower()
        
        # Check for filter metadata patterns
        metadata_patterns = [
            'filter:',
            'date from=',
            'date to=',
            'report generated',
            'query:',
            'parameters:',
            '--- ',
            '==='
        ]
        
        for pattern in metadata_patterns:
            if pattern in row_lower:
                return True
        
        return False
    
    def _is_header_row(self, row_str):
        """Check if a row is a header row."""
        row_lower = row_str.lower()
        
        # Common header indicators
        header_patterns = [
            'itemid',
            'pludescr', 
            'transactionid',
            'transaction_id',
            'barcode',
            'column'
        ]
        
        # If the row contains multiple header-like words, it's probably a header
        matches = sum(1 for pattern in header_patterns if pattern in row_lower)
        return matches >= 2
    
    def _parse_row(self, row):
        """Parse a single data row into a structured dictionary."""
        if isinstance(row, (tuple, list)):
            # Already structured data from database
            if hasattr(self, 'column_names') and len(self.column_names) == len(row):
                return dict(zip(self.column_names, row))
            return {'data': row}
        
        if isinstance(row, dict):
            return row
        
        if isinstance(row, str):
            # Try to parse as CSV
            try:
                parts = next(csv.reader([row]))
                if len(parts) > 1:
                    return {'data': parts}
            except csv.Error:
                pass
            
            # Try to parse as delimiter-separated
            for delimiter in ['\t', '|', ';', ',']:
                parts = row.split(delimiter)
                if len(parts) > 1:
                    return {'data': [p.strip() for p in parts]}
            
            # Single value
            if row.strip():
                return {'data': [row.strip()]}
        
        return None
    
    def generate_report(self, data, report_type="summary"):
        """Generate a report from the parsed data."""
        print(f"\n[3] Generating {report_type} report...")
        
        if not data:
            print("  ✗ No data available for report generation")
            return None
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_records': len(data),
            'report_type': report_type,
            'data': data
        }
        
        print(f"  ✓ Report generated with {len(data)} records")
        return report
    
    def save_report(self, report, output_path=None):
        """Save report to file."""
        if not report:
            return False
        
        if output_path is None:
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"scales_report_{timestamp}.csv"
        
        print(f"\n[4] Saving report to {output_path}...")
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if report['data']:
                    # Get all unique keys from the data
                    all_keys = set()
                    for row in report['data']:
                        all_keys.update(row.keys())
                    
                    writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                    writer.writeheader()
                    writer.writerows(report['data'])
            
            print(f"  ✓ Report saved successfully")
            return True
        except IOError as e:
            print(f"  ✗ Failed to save report: {e}")
            return False


def main():
    """Main entry point for the scales report exporter."""
    print("=" * 70)
    print("GENERATING ENHANCED SCALES REPORTS")
    print("=" * 70)
    
    # Default date range: first of month to today
    today = datetime.now()
    start_date = today.replace(day=1)
    end_date = today
    
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    exporter = ScalesReportExporter()
    
    # Connect to service
    exporter.connect_to_service()
    
    # Fetch data
    raw_data = exporter.fetch_raw_transaction_data(start_date, end_date)
    
    if not raw_data:
        print("\n✗ No raw data retrieved. Check connection and date range.")
        return 1
    
    # Parse and clean
    clean_data = exporter.parse_and_clean_data(raw_data)
    
    if not clean_data:
        print("\n✗ Could not process transaction data. Check data format.")
        return 1
    
    # Generate report
    report = exporter.generate_report(clean_data)
    
    # Save report
    if report:
        exporter.save_report(report)
    
    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())

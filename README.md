# SCALES-REPORT

A reporting tool for scales transaction data that connects to EasyWebService.

## Requirements

- Python 3.7+
- requests library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Generate Reports

```bash
python export_scales_reports.py
```

This will:
1. Connect to EasyWebService at http://localhost:9999
2. Fetch transaction data for the current month
3. Parse and clean the data (skipping metadata/filter rows)
4. Generate a CSV report in the `reports/` directory

### Utility Scripts

- `inspect_raw.py` - View raw data rows for debugging
- `find_columns.py` - Discover available database columns
- `debug_data.py` - Debug data issues
- `debug_detailed.py` - Detailed debugging information
- `check_dates.py` - Check date ranges in the data

### Windows Batch File

```cmd
run_export.bat
```

## Troubleshooting

### "No valid data rows found"

This typically occurs when:
1. The data contains filter/metadata rows that need to be skipped
2. The data format has changed

The `export_scales_reports.py` script automatically skips rows that contain:
- Filter metadata (e.g., "Filter: Date From=...")
- Empty rows
- Header rows

### Inspecting Raw Data

Use `inspect_raw.py` to see what the raw data looks like:

```bash
python inspect_raw.py
```

This will show the first 30 rows of raw data, helping identify parsing issues.

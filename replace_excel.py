#!/usr/bin/env python3
"""Replace the original Excel file with the updated temp file."""
import shutil
from pathlib import Path

EXCEL_FILE = Path("results/excel/classified_resumes.xlsx")
TEMP_FILE = Path("results/excel/classified_resumes_temp.xlsx")

if __name__ == "__main__":
    if not TEMP_FILE.exists():
        print("Temporary file not found. Please run update_excel_format_safe.py first.")
        exit(1)
    
    try:
        if EXCEL_FILE.exists():
            EXCEL_FILE.unlink()
        shutil.move(TEMP_FILE, EXCEL_FILE)
        print(f"Success! Excel file replaced: {EXCEL_FILE}")
        print("The file now has the new format with:")
        print("  - Full Name, Email, Mobile Number, Domain, Skills, Experience, Resume Link, Date Received")
        print("  - Formatted headers with blue background")
        print("  - Auto-adjusted column widths")
    except PermissionError:
        print("Error: Excel file is still open. Please close it and try again.")
    except Exception as e:
        print(f"Error: {e}")


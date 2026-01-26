"""
Quick script to create database.db with canonical_firms table
from the msgpack file for Email Engine integration
"""

import sqlite3
import os
from pathlib import Path

# Paths
data_dir = Path(__file__).parent / "data"
msgpack_file = Path(__file__).parent / "cpp_inference_engine" / "cpp" / "data" / "canonical_firms.msgpack"
db_file = data_dir / "database.db"

def create_database_from_msgpack():
    """Create database.db with canonical_firms table from msgpack file"""
    
    # Check if msgpack file exists
    if not msgpack_file.exists():
        print(f"Error: {msgpack_file} not found")
        print("Trying alternative: reading from Excel file...")
        return create_database_from_excel()
    
    try:
        import msgpack
        
        # Read msgpack file
        print(f"Reading {msgpack_file}...")
        with open(msgpack_file, 'rb') as f:
            data = msgpack.unpackb(f.read(), raw=False)
        
        # Create database
        print(f"Creating {db_file}...")
        os.makedirs(data_dir, exist_ok=True)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canonical_firms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firm TEXT NOT NULL,
                domain TEXT NOT NULL,
                UNIQUE(firm, domain)
            )
        """)
        
        # Insert data
        print("Inserting firms...")
        count = 0
        if isinstance(data, dict):
            for firm, domain_value in data.items():
                try:
                    # Handle different domain formats
                    if isinstance(domain_value, dict):
                        # If domain is a dict, extract the actual domain string
                        domain = domain_value.get('domain', '') if isinstance(domain_value, dict) else str(domain_value)
                    elif isinstance(domain_value, list) and len(domain_value) > 0:
                        # If domain is a list, take first item
                        domain = str(domain_value[0])
                    else:
                        domain = str(domain_value) if domain_value else ''
                    
                    cursor.execute(
                        "INSERT OR IGNORE INTO canonical_firms (firm, domain) VALUES (?, ?)",
                        (firm, domain)
                    )
                    count += 1
                except Exception as e:
                    # Skip errors, continue with next firm
                    pass
        
        conn.commit()
        conn.close()
        
        print(f"[SUCCESS] Created database with {count} firms!")
        return True
        
    except ImportError:
        print("msgpack not installed. Trying alternative method...")
        return create_database_from_excel()
    except Exception as e:
        print(f"Error: {e}")
        return create_database_from_excel()

def create_database_from_excel():
    """Create database from Excel file as fallback"""
    excel_file = data_dir / "LP and GP data.xlsx"
    
    if not excel_file.exists():
        print(f"Error: {excel_file} not found")
        print("\nYou need to either:")
        print("1. Install msgpack: pip install msgpack")
        print("2. Run the full pipeline: poetry run python -m email_prediction.pipeline")
        return False
    
    try:
        import pandas as pd
        
        print(f"Reading {excel_file}...")
        # Try to read the Excel file and extract unique firms
        df = pd.read_excel(excel_file)
        
        # Look for firm/company column
        firm_col = None
        for col in df.columns:
            if 'firm' in col.lower() or 'company' in col.lower():
                firm_col = col
                break
        
        if not firm_col:
            print("Could not find firm column in Excel file")
            return False
        
        # Get unique firms
        firms = df[firm_col].dropna().unique()
        
        # Create database
        print(f"Creating {db_file}...")
        os.makedirs(data_dir, exist_ok=True)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canonical_firms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firm TEXT NOT NULL,
                domain TEXT NOT NULL DEFAULT '',
                UNIQUE(firm)
            )
        """)
        
        # Insert firms (without domain for now)
        print("Inserting firms...")
        for firm in firms:
            if firm and isinstance(firm, str):
                cursor.execute(
                    "INSERT OR IGNORE INTO canonical_firms (firm, domain) VALUES (?, ?)",
                    (firm, '')
                )
        
        conn.commit()
        count = cursor.execute("SELECT COUNT(*) FROM canonical_firms").fetchone()[0]
        conn.close()
        
        print(f"✅ Created database with {count} firms (domains will be empty)")
        print("Note: For full functionality, run the complete pipeline to get domains")
        return True
        
    except ImportError:
        print("pandas not installed. Install with: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating database.db for Email Engine...")
    print("=" * 50)
    success = create_database_from_msgpack()
    if success:
        print("\n[SUCCESS] Database created successfully!")
        print(f"Location: {db_file}")
    else:
        print("\n[FAILED] Failed to create database")
        print("\nTo create the full database, run:")
        print("  cd post_irp")
        print("  poetry install")
        print("  poetry run python -m email_prediction.pipeline")


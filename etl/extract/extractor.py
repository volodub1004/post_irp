import os
import pandas as pd

# Constants
# ------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
EXCEL_FILE = os.path.join(DATA_DIR, "LP and GP data.xlsx")

# Extract Functions
# ------------------------------------------


def extract_excel_data(sheet_name: str) -> pd.DataFrame:
    """Extract data from an Excel sheet.

    Args:
        sheet_name (str): The name of the sheet to extract data from.

    Returns:
        pd.DataFrame: DataFrame containing the extracted data.
    Raises:
        FileNotFoundError: If the Excel file does not exist.
    """
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)

    print(f"Read from {sheet_name}")
    return df

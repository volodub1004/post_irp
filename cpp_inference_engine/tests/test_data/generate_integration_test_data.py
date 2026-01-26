from db.db import read_table
from db.models import TableName
from pathlib import Path
import pandas as pd

# Read clean data
lp_clean = read_table(TableName.COMBINED_CLEAN)

# Get test ids from prediction pipeline
script_dir = Path(__file__).resolve().parent
std_test = pd.read_csv(script_dir / "test_std_ids.csv")
comp_test = pd.read_csv(script_dir / "test_comp_ids.csv")

# Concatenate ids
test_ids = std_test["test_ids"].to_list() + comp_test["test_ids"].to_list()

# Get domains
lp_clean["domain"] = lp_clean["email"].str.extract(r"@(.+)$")[0].str.lower()

# To csv
test_data = lp_clean[lp_clean["id"].isin(test_ids)]
test_data[["id", "investor", "firm", "email", "domain"]].to_csv(
    script_dir / "integration_test_data.csv", index=False
)

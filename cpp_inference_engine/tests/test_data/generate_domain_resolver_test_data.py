from db.db import read_table
from db.models import TableName
from pathlib import Path
import pandas as pd

# Read clean data
lp_clean = read_table(TableName.COMBINED_CLEAN)

# Get domains
lp_clean["domain"] = lp_clean["email"].str.extract(r"@(.+)$")[0].str.lower()

# Normalize firm names
lp_clean["firm"] = (
    lp_clean["firm"].astype(str).str.replace(" ", "", regex=False).str.lower()
)

# Count occurrences per (firm, domain)
counts = (
    lp_clean.groupby(["firm", "domain"], as_index=False)
    .size()
    .rename(columns={"size": "n"})
)

# Pick most-used domain per firm
most = (
    counts.sort_values(["firm", "n", "domain"], ascending=[True, False, True])
    .groupby("firm", as_index=False)
    .head(1)[["firm", "domain"]]
    .reset_index(drop=True)
)

# To csv
script_dir = Path(__file__).resolve().parent
most[["firm", "domain"]].to_csv(
    script_dir / "domain_resolver_test_data.csv", index=False
)

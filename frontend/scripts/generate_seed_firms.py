from db.db import read_table
from db.models import TableName
import pandas as pd

lp = read_table(table=TableName.LP)
gp = read_table(table=TableName.GP)

# Combine both into one DataFrame
df = pd.concat([lp, gp], ignore_index=True)
df["domain"] = df["email"].str.extract("@(.*)$")[0].str.lower()

# Ensure consistent column names
df = df.rename(columns={"firm": "firm_name", "domain_name": "domain"})

# Drop empty or invalid values
df = df.dropna(subset=["firm_name", "domain"])

# Group by firm and aggregate unique domains into sorted lists
firm_to_domains: dict[str, list[str]] = (
    df.groupby("firm_name")["domain"]
    .apply(lambda x: sorted(set(map(str.lower, x))))  # deduplicate + normalize case
    .to_dict()
)

output_path = "prisma/seed_firms.sql"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("-- Auto-generated SQL seed for Firm and Domain tables\n")
    f.write("BEGIN;\n")  # wrap all inserts in a single transaction
    f.write("TRUNCATE TABLE \"Domain\" RESTART IDENTITY CASCADE;\n")
    f.write("TRUNCATE TABLE \"Firm\" RESTART IDENTITY CASCADE;\n\n")

    # Insert firms in one statement
    f.write("-- Insert firms\n")
    firm_values = []
    for firm in firm_to_domains.keys():
        safe_firm = firm.replace("'", "''")
        firm_values.append(f"('{safe_firm}')")

    f.write("INSERT INTO \"Firm\" (name) VALUES\n")
    f.write(",\n".join(firm_values))
    f.write(";\n\n")

    # Insert domains in batches
    f.write("-- Insert domains\n")
    batch_size = 5000  # adjust if needed for memory or psql limits
    domain_rows = []
    firm_id = 1
    for firm, domains in firm_to_domains.items():
        for domain in domains:
            safe_domain = domain.replace("'", "''")
            domain_rows.append(f"('{safe_domain}', {firm_id})")
        firm_id += 1

    # Write domains in batches
    for i in range(0, len(domain_rows), batch_size):
        batch = domain_rows[i:i + batch_size]
        f.write("INSERT INTO \"Domain\" (domain, \"firmId\") VALUES\n")
        f.write(",\n".join(batch))
        f.write(";\n")

    f.write("COMMIT;\n")

print(f"SQL seed written to {output_path}")
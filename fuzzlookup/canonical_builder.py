from db.db import read_table, write_table, init_db
from db.models import TableName


def build_canonical_firms() -> None:
    """Builds firm and domain pairs list from the clean combined data base
    and writes the result back to the canonical firms database.

    Args:
        None
    Returns:
        None
    """
    init_db()

    # Domain extractor splitter
    def extract_domain(email: str) -> str:
        return email.split("@")[1].strip().lower()

    # Read clean data
    df = read_table(TableName.COMBINED_CLEAN, columns=["firm", "email"]).copy()
    # Extract domains
    df["domain"] = df["email"].apply(extract_domain)

    # Normalize firm names
    df["firm"] = df["firm"].astype(str).str.lower()

    # Count occurrences per (firm, domain)
    counts = (
        df.groupby(["firm", "domain"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )

    # Pick most used domain per firm
    most = (
        counts.sort_values(["firm", "n", "domain"], ascending=[True, False, True])
        .groupby("firm", as_index=False)
        .head(1)[["firm", "domain"]]
        .reset_index(drop=True)
    )

    write_table(TableName.CANONICAL_FIRMS, most)
    print(f"Saved {len(most)} firm -> domain pairs (most-used per firm).")


if __name__ == "__main__":
    build_canonical_firms()

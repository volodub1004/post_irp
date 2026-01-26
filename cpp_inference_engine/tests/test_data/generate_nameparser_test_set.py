import pandas as pd
import re
from nameparser import HumanName
from pathlib import Path


def clean_generic(series: pd.Series) -> pd.Series:
    mask = series.notna()
    cleaned = series[mask].astype(str).str.strip().str.lower()
    cleaned = (
        cleaned.str.replace(r"[.,;:!?)}\]]+$", "", regex=True)
        .str.replace(r"\s{2,}", " ", regex=True)
        .str.replace(r"[\"'<>]", "", regex=True)
    )
    return series.where(~mask, cleaned)


def parse_name(name: str) -> dict:
    n = HumanName(name)

    return {
        "normalized_name": name,
        "first": n.first,
        "middle": n.middle,
        "last": n.last,
        "has_middle_name": bool(n.middle),
        "has_multiple_first_names": len(n.first.split()) > 1,
        "has_multiple_middle_names": len(n.middle.split()) > 1,
        "has_multiple_last_names": len(n.last.split()) > 1,
    }


def main():
    # Resolve script directory
    script_dir = Path(__file__).resolve().parent
    df = pd.read_excel(script_dir / "raw_names.xlsx")  # Must have column 'Name'

    # Keep only rows where Name fully matches allowed characters
    df = df[df["Name"].str.fullmatch(r"[A-Za-z\s\-]+")]
    df["Name"] = df["Name"].str.replace("-", " ", regex=False)

    df["normalized_name"] = clean_generic(df["Name"])

    parsed = df["normalized_name"].apply(parse_name).apply(pd.Series)

    output = pd.concat([df["Name"], parsed], axis=1)
    output.to_csv(script_dir / "nameparser_test_set.csv", index=False, encoding="utf-8")
    print("Saved to nameparser_test_set.csv")


if __name__ == "__main__":
    main()

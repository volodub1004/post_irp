import requests
import csv
import time
import pandas as pd
from pathlib import Path
from statistics import mean

# Test generated with help from CoPilot. Mimic cpp and pybindings test
API_BASE = "http://localhost:8000"
TOP_K = 3

# CSV path and row definition
CSV_PATH = Path(__file__).parent / "test_data/integration_test_data.csv"


def pick_random_non_failed_ids(
    n: int = 3, random_state: int | None = None
) -> list[int]:
    # Read ids and tes data
    test = pd.read_csv(CSV_PATH)

    # Ensure domain column exists
    if "domain" not in test.columns:
        test["domain"] = (
            test["email"].astype(str).str.extract(r"@([^@\s>]+)")[0].str.lower()
        )

    # Random sample
    sample = test.sample(n=min(n, len(test)), random_state=random_state)
    sample = (
        sample.assign(row_id=sample["id"].astype(int))
        .rename(columns={"investor": "name", "email": "label_email"})
        .loc[:, ["row_id", "name", "firm", "label_email", "domain"]]
    )

    return sample.to_dict(orient="records")


def benchmark():
    rows = pick_random_non_failed_ids()
    for i, row in enumerate(rows):
        payload = {
            "name": row["name"],
            "firm": row["firm"],
            "domain": row["domain"],
            "top_k": TOP_K,
        }

        # Predict
        t0 = time.perf_counter()
        r = requests.post(
            f"{API_BASE}/predict/catboost_verified", json=payload, timeout=30
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        if r.status_code != 200:
            print(f"[ERROR] {r.status_code} on row {row['row_id']}: {r.text}")
            continue

        preds = r.json()
        print(
            f"\nRow {i} (row_id={row['row_id']}), latency={latency_ms:.1f} ms, top_k={len(preds)}"
        )

        for j, p in enumerate(preds, 1):
            print(
                f"  #{j}: email={p.get('email')} "
                f"score={p.get('score'):.4f} "
                f"verif_status={p.get('verification_status')} "
                f"verif_score={p.get('verification_score')}"
            )


if __name__ == "__main__":
    benchmark()

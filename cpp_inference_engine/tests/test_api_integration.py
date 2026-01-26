import requests
import csv
import time
from pathlib import Path
from statistics import mean

# Test generated with help from CoPilot. Mimic cpp and pybindings test
API_BASE = "http://localhost:8000"
TOP_K = 3

# CSV path and row definition
CSV_PATH = Path(__file__).parent / "test_data/integration_test_data.csv"


class RankingStats:
    def __init__(self):
        self.correct_at_1 = 0
        self.recall_at_k = 0
        self.reciprocal_sum = 0
        self.failed_ids = []
        self.latencies_ms = []
        self.total = 0

    def add(self, predictions, label, row_id):
        self.total += 1
        found = False
        for i, pred in enumerate(predictions):
            if pred["email"] == label:
                if i == 0:
                    self.correct_at_1 += 1
                if i < TOP_K:
                    self.recall_at_k += 1
                self.reciprocal_sum += 1 / (i + 1)
                found = True
                break
        if not found:
            self.failed_ids.append(row_id)

    def report(self, model_name):
        print(f"\n--- {model_name.upper()} API Results ---")
        print(f"Accuracy@1: {self.correct_at_1 / self.total:.4f}")
        print(f"Recall@{TOP_K}: {self.recall_at_k / self.total:.4f}")
        print(f"MRR: {self.reciprocal_sum / self.total:.4f}")
        print(f"Avg Latency (ms): {mean(self.latencies_ms):.2f}")
        print(f"Failures: {len(self.failed_ids)} / {self.total}")
        with open(f"failed_ids_{model_name}.csv", "w") as f:
            f.write("failed_ids\n")
            for fid in self.failed_ids:
                f.write(f"{fid}\n")


def load_test_data(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "row_id": int(row["id"]),
                "name": row["investor"],
                "firm": row["firm"],
                "label_email": row["email"],
                "domain": row["domain"],
            }
            for row in reader
        ]


def benchmark(model_route, rows):
    stats = RankingStats()
    for i, row in enumerate(rows):
        payload = {
            "name": row["name"],
            "firm": row["firm"],
            "domain": row["domain"],
            "top_k": TOP_K,
        }
        start = time.time()
        r = requests.post(f"{API_BASE}/predict/{model_route}", json=payload)
        latency = (time.time() - start) * 1000
        stats.latencies_ms.append(latency)

        if r.status_code != 200:
            print(f"[ERROR] {r.status_code} on row {row['row_id']}")
            stats.failed_ids.append(row["row_id"])
            continue

        preds = r.json()
        stats.add(preds, row["label_email"], row["row_id"])

        if i % 5000 == 0 and i > 0:
            print(f"{i} predictions complete")

    stats.report(model_route)


if __name__ == "__main__":
    rows = load_test_data(CSV_PATH)
    benchmark("catboost", rows)

import csv
import time
from pathlib import Path
from statistics import mean
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "cpp"))
from email_predictor import (
    CatBoostEmailPredictionEngine,
    CatBoostTemplatePredictor,
)

# Setup
BASE_PATH = Path(__file__).parent.resolve()
TOP_K = 3
CSV_PATH = BASE_PATH / "test_data/integration_test_data.csv"

std_model_path = BASE_PATH / "../cpp/model/std_catboost_model.cbm"
complex_model_path = BASE_PATH / "../cpp/model/comp_catboost_model.cbm"

std_template_path = BASE_PATH / "../cpp/data/std_candidate_templates.msgpack"
complex_template_path = BASE_PATH / "../cpp/data/complex_candidate_templates.msgpack"
firm_map_path = BASE_PATH / "../cpp/data/firm_template_map.msgpack"


# Load CSV
def load_test_data(path):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)


# Metrics - Replicates tests in cpp
class RankingStats:
    def __init__(self, k):
        self.k = k
        self.total = 0
        self.correct_at_1 = 0
        self.recall_at_k = 0
        self.mrr_sum = 0.0
        self.failed_ids = []
        self.latencies_ms = []

    def add(self, preds, label, duration_ms, row_id):
        self.total += 1
        self.latencies_ms.append(duration_ms)

        found = False
        for i, pred in enumerate(preds):
            if pred.email.strip().lower() == label.strip().lower():
                if i == 0:
                    self.correct_at_1 += 1
                if i < self.k:
                    self.recall_at_k += 1
                self.mrr_sum += 1 / (i + 1)
                found = True
                break

        if not found:
            self.failed_ids.append(row_id)

    def report(self):
        print(f"Total: {self.total}")
        print(f"Accuracy@1: {self.correct_at_1 / self.total:.4f}")
        print(f"Recall@{self.k}: {self.recall_at_k / self.total:.4f}")
        print(f"MRR: {self.mrr_sum / self.total:.4f}")
        print(f"Avg latency: {mean(self.latencies_ms):.2f} ms")

        failed_path = BASE_PATH / ("failed_ids_catboost.csv")
        with open(failed_path, "w") as f:
            f.write("failed_ids\n")
            for row_id in self.failed_ids:
                f.write(f"{row_id}\n")


# Main Test
def run_test():
    print("Loading models...")

    std_predictor = CatBoostTemplatePredictor(str(std_model_path))

    comp_predictor = CatBoostTemplatePredictor(str(complex_model_path))

    engine = CatBoostEmailPredictionEngine(
        std_predictor,
        comp_predictor,
        str(std_template_path),
        str(complex_template_path),
        str(firm_map_path),
    )

    test_data = load_test_data(CSV_PATH)
    stats = RankingStats(k=TOP_K)

    for i, row in enumerate(test_data):
        start = time.perf_counter()
        preds = engine.predict(
            row["investor"], row["firm"], TOP_K, row["domain"] or None
        )
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        stats.add(preds, row["email"], duration_ms, int(row["id"]))

        if (i + 1) % 5000 == 0:
            print(f"Processed {i+1}/{len(test_data)} rows")

    stats.report()


if __name__ == "__main__":
    run_test()

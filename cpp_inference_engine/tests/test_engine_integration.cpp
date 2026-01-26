#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <gtest/gtest.h>
#include <numeric>
#include <sstream>
#include <unordered_set>

#include "email_predictor/catboost_template_predictor.hpp"
#include "email_predictor/email_prediction_engine.hpp"
#include "email_predictor/light_gbm_template_predictor.hpp"

using namespace email_predictor;
namespace fs = std::filesystem;

static std::filesystem::path base_path =
    std::filesystem::path(__FILE__).parent_path();
static const std::string complex_model_path =
    base_path / "../cpp/model/comp_lightgbm_model.txt";
static const std::string std_template_path =
    base_path / "../cpp/data/std_candidate_templates.msgpack";
static const std::string complex_template_path =
    base_path / "../cpp/data/complex_candidate_templates.msgpack";
static const std::string firm_map_path =
    base_path / "../cpp/data/firm_template_map.msgpack";
static const std::string csv_path =
    base_path / "test_data/integration_test_data.csv";

// Struct to hold input/output for a single test row
struct TestRow {
  int row_id;
  std::string investor;
  std::string firm;
  std::string label_email;
  std::string domain;
};

// Load test data from a CSV
std::vector<TestRow> load_test_data(const std::string &csv_path) {
  std::vector<TestRow> rows;
  std::ifstream file(csv_path);
  if (!file.is_open())
    throw std::runtime_error("Unable to open test CSV file");

  std::string line;
  std::getline(file, line); // skip header
  while (std::getline(file, line)) {
    std::stringstream ss(line);
    std::string id, investor, firm, email, domain;

    std::getline(ss, id, ',');
    std::getline(ss, investor, ',');
    std::getline(ss, firm, ',');
    std::getline(ss, email, ',');
    std::getline(ss, domain, ',');

    rows.push_back({std::stoi(id), investor, firm, email, domain});
  }
  return rows;
}

// Ranking metrics accumulator
struct RankingStats {
  int correct_at_1 = 0;
  int total = 0;
  int recall_at_k = 0;
  double reciprocal_sum = 0.0;
  std::vector<double> latencies_ms;
  std::vector<int> failed_ids;
  std::vector<std::tuple<int, int, int>> failed_template_ids;

  void add_prediction(const std::vector<EmailPredictionResult> &preds,
                      const std::string &label,
                      std::chrono::duration<double, std::milli> duration,
                      int row_id, std::size_t k = 3) {
    ++total;
    latencies_ms.push_back(duration.count());

    bool found = false;
    for (std::size_t i = 0; i < preds.size(); ++i) {
      if (preds[i].email == label) {
        if (i == 0)
          ++correct_at_1;
        if (i < k)
          ++recall_at_k;
        reciprocal_sum += 1.0 / (i + 1);
        found = true;
        break;
      }
    }
    if (!found) {
      reciprocal_sum += 0.0;
      failed_ids.push_back(row_id);
      failed_template_ids.push_back(
          {preds[0].template_id, preds[1].template_id, preds[2].template_id});
    }
  }

  void report(bool catboost = false, std::ostream &out = std::cout,
              std::size_t k = 3) const {
    double acc1 = static_cast<double>(correct_at_1) / total;
    double recall = static_cast<double>(recall_at_k) / total;
    double mrr = reciprocal_sum / total;

    double avg_latency =
        std::accumulate(latencies_ms.begin(), latencies_ms.end(), 0.0) /
        latencies_ms.size();

    out << "Accuracy@1: " << acc1 << "\n";
    out << "Recall@" << k << ": " << recall << "\n";
    out << "MRR: " << mrr << "\n";
    out << "Avg Latency (ms): " << avg_latency << "\n";

    // Write failed ids to csv
    std::filesystem::path base_path =
        std::filesystem::path(__FILE__).parent_path();
    const std::string failed_ids_path =
        catboost ? "failed_ids_catboost.csv" : "failed_ids_lightgbm.csv";
    std::ofstream fout(base_path / failed_ids_path);
    if (!fout)
      throw std::runtime_error("Failed to open file");
    fout << "failed_ids\n";

    for (std::size_t i = 0; i < failed_ids.size(); ++i) {
      fout << failed_ids[i];
      if (i != failed_ids.size() - 1) {
        fout << "\n";
      }
    }

    // Write failing template ids to csv
    const std::string failed_templates_path =
        catboost ? "failed_template_catboost.csv"
                 : "failed_template_lightgbm.csv";
    std::ofstream fout2(base_path / failed_templates_path);
    if (!fout2)
      throw std::runtime_error("Failed to open file");
    fout2 << "failed_templates\n";

    for (std::size_t i = 0; i < failed_template_ids.size(); ++i) {
      const auto [first, second, third] = failed_template_ids[i];
      fout2 << first << "," << second << "," << third;
      if (i != failed_template_ids.size() - 1) {
        fout2 << "\n";
      }
    }
  }
};

// GTest entry point
TEST(EmailPredictionEngineIntegrationTest, PredictsCorrectTemplates_CatBoost) {
  const std::string std_model_path =
      base_path / "../cpp/model/std_catboost_model.cbm";
  const std::string complex_model_path =
      base_path / "../cpp/model/comp_catboost_model.cbm";

  ASSERT_TRUE(fs::exists(std_model_path));
  ASSERT_TRUE(fs::exists(complex_model_path));
  ASSERT_TRUE(fs::exists(std_template_path));
  ASSERT_TRUE(fs::exists(complex_template_path));
  ASSERT_TRUE(fs::exists(firm_map_path));
  ASSERT_TRUE(fs::exists(csv_path));

  EmailPredictionEngine<CatBoostTemplatePredictor> engine(
      std::make_shared<CatBoostTemplatePredictor>(std_model_path),
      std::make_shared<CatBoostTemplatePredictor>(complex_model_path),
      std_template_path, complex_template_path, firm_map_path);

  auto rows = load_test_data(csv_path);
  ASSERT_GT(rows.size(), 0);

  RankingStats stats;

  int count = 0;

  for (const auto &row : rows) {
    auto start = std::chrono::steady_clock::now();

    auto preds = engine.predict(row.investor, row.firm, 3, row.domain);

    auto end = std::chrono::steady_clock::now();
    stats.add_prediction(preds, row.label_email, end - start, row.row_id, 3);

    ++count;
    if (count % 5000 == 0) {
      std::cout << count << " predictions out of " << rows.size() << std::endl;
    }
  }

  stats.report(true);
  EXPECT_GT(stats.total, 0);
}

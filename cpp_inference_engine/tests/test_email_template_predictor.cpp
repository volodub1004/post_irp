#include <filesystem>
#include <gtest/gtest.h>

#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/light_gbm_template_predictor.hpp"

using namespace email_predictor;
using namespace email_predictor::features::builder;

TEST(LightGBMTemplatePredictorTest, ModelLoadsSuccessfully) {
  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  EXPECT_NO_THROW({
    LightGBMTemplatePredictor predictor(base_path / "test_data/lgbm_model.txt");
  });
}

TEST(LightGBMTemplatePredictorTest, PredictScoresReturnsCorrectSize) {
  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  LightGBMTemplatePredictor predictor(base_path / "test_data/lgbm_model.txt");

  std::vector<float> flat_matrix;
  for (int i = 0; i < 5; ++i) {
    for (int i = 0; i < 27; ++i) {
      flat_matrix.push_back(0.0f);
    }

    // Add features
    flat_matrix[(i * 27)] = 1.0f;      // multi_domain
    flat_matrix[(i * 27) + 19] = 5;    // firm support count
    flat_matrix[(i * 27) + 20] = 0.3f; // firm support pct
    flat_matrix[(i * 27) + 21] = 1.0f; // template_is_top_template
    flat_matrix[(i * 27) + 26] = 0.0f; // firm_is_single_template
  }

  auto scores = predictor.predict_scores(flat_matrix);
  ASSERT_EQ(scores.size(), flat_matrix.size() / 27);
  for (double score : scores) {
    EXPECT_GE(score, -10.0); // allow for arbitrary scoring range
    EXPECT_LE(score, 10.0);
  }
}

TEST(LightGBMTemplatePredictorTest, PredictTopTemplatesReturnsSortedTopK) {
  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  LightGBMTemplatePredictor predictor(base_path / "test_data/lgbm_model.txt");

  std::vector<float> flat_matrix;
  std::vector<int> template_ids = {101, 102, 103, 104, 105};
  std::vector<data_loaders::CandidateTemplate> templates(5);
  for (int i = 0; i < 5; ++i) {
    for (int i = 0; i < 27; ++i) {
      flat_matrix.push_back(0.0f);
    }
    // Add features
    flat_matrix[(i * 27) + 2] = 0.0f;      // multi_domain
    flat_matrix[(i * 27) + 19] = i;        // firm support count
    flat_matrix[(i * 27) + 20] = 0.1f * i; // firm support pct

    templates[i] = data_loaders::CandidateTemplate{
        .template_id = template_ids[i],
        .token_seq =
            data_loaders::parse_token_sequence({"f_0", "last_original_0"}),
        .support_count = 0,
        .coverage_pct = 0.0f,
        .in_mined_rules = false,
        .max_rule_confidence = 0.0f,
        .avg_rule_confidence = 0.0f,
        .uses_middle_name = false,
        .uses_multiple_firsts = false,
        .uses_multiple_middles = false,
        .uses_multiple_lasts = false};
  }

  auto top = predictor.predict_top_templates(flat_matrix, templates, 3);
  ASSERT_EQ(top.size(), 3);
  for (std::size_t i = 1; i < top.size(); ++i) {
    EXPECT_GE(top[i - 1].score, top[i].score); // sorted descending
  }
}

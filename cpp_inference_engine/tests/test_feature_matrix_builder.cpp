#include "data_loader/templates_loader.hpp"
#include "email_predictor/features/builder/feature_matrix_builder.hpp"

#include <gtest/gtest.h>
#include <string>
#include <unordered_map>

using namespace email_predictor;
using namespace data_loaders;
using namespace email_predictor::features::builder;

TEST(FeatureMatrixBuilderTest, MinimalCase) {
  std::vector<CandidateTemplate> templates = {CandidateTemplate{
      .template_id = 1,
      .token_seq =
          data_loaders::parse_token_sequence({"f_0", "last_original_0"}),
      .support_count = 10,
      .coverage_pct = 0.25f,
      .in_mined_rules = true,
      .max_rule_confidence = 0.9f,
      .avg_rule_confidence = 0.7f,
      .uses_middle_name = false,
      .uses_multiple_firsts = false,
      .uses_multiple_middles = false,
      .uses_multiple_lasts = false}};

  std::unordered_map<std::string, FirmStats> stats = {
      {"TestFirm", FirmStats{.num_templates = 1,
                             .num_investors = 10,
                             .diversity_ratio = 0.1f,
                             .is_single_template = true,
                             .is_shared_infra = false,
                             .firm_is_multi_domain = false}}};

  std::unordered_map<std::string, std::unordered_map<int, FirmTemplateUsage>>
      usage = {{"TestFirm",
                {{1, FirmTemplateUsage{.support_count = 4,
                                       .coverage_pct = 0.4f,
                                       .is_top_template = true}}}}};

  // Decompose name
  name_decomposer::NameDecomposer name_struct("John Smith");
  auto flags = features::InvestorFeatureExtractor::extract("John Smith");

  auto rows = build_feature_rows(name_struct, flags, "TestFirm", templates,
                                 stats, usage);
  ASSERT_EQ(rows.size(), 27);

  EXPECT_FLOAT_EQ(rows[1], 0.0f);   // is shared infra
  EXPECT_FLOAT_EQ(rows[2], 0.0f);   // is multi domain
  EXPECT_FLOAT_EQ(rows[3], 0.0f);   // has_german_char
  EXPECT_FLOAT_EQ(rows[4], 0.0f);   // nfkd_normalized
  EXPECT_FLOAT_EQ(rows[5], 1.0f);   // has_nickname
  EXPECT_FLOAT_EQ(rows[6], 0.0f);   // has_multiple_first_names
  EXPECT_FLOAT_EQ(rows[7], 0.0f);   // has_middle_name
  EXPECT_FLOAT_EQ(rows[8], 0.0f);   // has_multiple_middle_names
  EXPECT_FLOAT_EQ(rows[9], 0.0f);   // has_multiple_last_names
  EXPECT_FLOAT_EQ(rows[10], 10.0f); // template_support_count
  EXPECT_FLOAT_EQ(rows[12], 1.0f);  // template_in_mined_rules
  EXPECT_FLOAT_EQ(rows[13], 0.9f);  // template_max_rule_confidence
  EXPECT_FLOAT_EQ(rows[14], 0.7f);  // template_avg_rule_confidence
  EXPECT_FLOAT_EQ(rows[19], 4.0f);  // firm_support_count
  EXPECT_FLOAT_EQ(rows[23], 1.0f);  // firm_num_templates
  EXPECT_FLOAT_EQ(rows[24], 10.0f); // firm_num_investors
  EXPECT_FLOAT_EQ(rows[25], 0.1f);  // firm_diversity_ratio
  EXPECT_FLOAT_EQ(rows[26], 1.0f);  // firm_is_single_template
}

TEST(FeatureMatrixBuilderTest, ClashDetected) {
  std::vector<CandidateTemplate> templates = {CandidateTemplate{
      .template_id = 42,
      .token_seq =
          data_loaders::parse_token_sequence({"m_0", "last_original_0"}),
      .support_count = 20,
      .coverage_pct = 0.5f,
      .in_mined_rules = true,
      .max_rule_confidence = 0.95f,
      .avg_rule_confidence = 0.85f,
      .uses_middle_name = true, // trigger clash
      .uses_multiple_firsts = false,
      .uses_multiple_middles = false,
      .uses_multiple_lasts = false

  }};

  std::unordered_map<std::string, FirmStats> stats = {
      {"ClashFirm", FirmStats{.num_templates = 2,
                              .num_investors = 20,
                              .diversity_ratio = 0.1f,
                              .is_single_template = false,
                              .is_shared_infra = true,
                              .firm_is_multi_domain = true}}};

  std::unordered_map<std::string, std::unordered_map<int, FirmTemplateUsage>>
      usage;

  // Decompose name
  name_decomposer::NameDecomposer name_struct("Alice Beth Carter");
  auto flags = features::InvestorFeatureExtractor::extract("Alice Beth Carter");
  auto rows = build_feature_rows(name_struct, flags, "ClashFirm", templates,
                                 stats, usage);

  ASSERT_EQ(rows.size(), 27);

  EXPECT_FLOAT_EQ(rows[1], 1.0f);  // firm_is_shared_infra
  EXPECT_FLOAT_EQ(rows[2], 1.0f);  // firm_is_multi_domain
  EXPECT_FLOAT_EQ(rows[22], 1.0f); // template_name_characteristic_clash
}

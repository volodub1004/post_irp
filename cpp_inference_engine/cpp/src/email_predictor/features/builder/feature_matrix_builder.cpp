#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/features/investor_feature_extractor.hpp"
#include "email_predictor/name_decomposer/name_decomposer.hpp"
#include "email_predictor/template_prediction.hpp"

#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace email_predictor::features::builder {

std::vector<float> build_feature_rows(
    const name_decomposer::NameDecomposer &investor_name,
    const email_predictor::features::InvestorFeatureExtractor::Flags &flags,
    std::string_view firm_name,
    const std::vector<data_loaders::CandidateTemplate> &templates,
    const std::unordered_map<std::string, data_loaders::FirmStats> &firm_stats,
    const std::unordered_map<
        std::string, std::unordered_map<int, data_loaders::FirmTemplateUsage>>
        &firm_template_usage_map) {
  std::vector<float> flat_matrix;
  flat_matrix.reserve(templates.size() * FEATURES_PER_ROW);

  // Cache name structure flags
  const bool name_has_middle = investor_name.has_middle_name();
  const bool name_has_multiple_firsts =
      investor_name.has_multiple_first_names();
  const bool name_has_multiple_middles =
      investor_name.has_multiple_middle_names();
  const bool name_has_multiple_lasts = investor_name.has_multiple_last_names();

  // Firm-level metadata lookup
  const auto firm_stats_it = firm_stats.find(std::string(firm_name));
  const bool has_firm_stats = firm_stats_it != firm_stats.end();
  const data_loaders::FirmStats &stats =
      has_firm_stats ? firm_stats_it->second
                     : []() -> const data_loaders::FirmStats & {
    static const data_loaders::FirmStats
        dummy_stats{}; // Lambda to return static because can't have a reference
                       // to a temporary.
    return dummy_stats;
  }();

  const auto usage_map_it =
      firm_template_usage_map.find(std::string(firm_name));
  const bool has_usage_map = usage_map_it != firm_template_usage_map.end();
  const auto &firm_template_usage = has_usage_map ? usage_map_it->second : []()
      -> const std::unordered_map<int, data_loaders::FirmTemplateUsage> & {
    static const std::unordered_map<int, data_loaders::FirmTemplateUsage>
        empty_map{}; // Lambda to return static because can't have a reference
                     // to a temporary.
    return empty_map;
  }();

  // Templates are already ordered and deterministic from vector
  for (const auto &tmpl : templates) {
    // Template usage lookup
    const auto usage_it = firm_template_usage.find(tmpl.template_id);
    const bool in_firm_templates = usage_it != firm_template_usage.end();

    int firm_support_count = 0;
    float firm_coverage_pct = 0.0f;
    bool is_top_template = false;

    // Calculate usage states
    if (in_firm_templates) {
      const auto &usage = usage_it->second;
      firm_support_count = usage.support_count;
      firm_coverage_pct = usage.coverage_pct;
      is_top_template = usage.is_top_template;
    }

    // Clash calculation
    const bool clash =
        (tmpl.uses_middle_name && name_has_middle) ||
        (tmpl.uses_multiple_firsts && name_has_multiple_firsts) ||
        (tmpl.uses_multiple_middles && name_has_multiple_middles) ||
        (tmpl.uses_multiple_lasts && name_has_multiple_lasts);

    // Encoding features in same order as were provided in training
    flat_matrix.emplace_back(static_cast<float>(in_firm_templates));
    flat_matrix.emplace_back(static_cast<float>(stats.is_shared_infra));
    flat_matrix.emplace_back(static_cast<float>(stats.firm_is_multi_domain));
    flat_matrix.emplace_back(static_cast<float>(flags.has_german_char));
    flat_matrix.emplace_back(static_cast<float>(flags.has_nfkd_normalized));
    flat_matrix.emplace_back(static_cast<float>(flags.has_nickname));
    flat_matrix.emplace_back(static_cast<float>(name_has_multiple_firsts));
    flat_matrix.emplace_back(static_cast<float>(name_has_middle));
    flat_matrix.emplace_back(static_cast<float>(name_has_multiple_middles));
    flat_matrix.emplace_back(static_cast<float>(name_has_multiple_lasts));
    flat_matrix.emplace_back(static_cast<float>(tmpl.support_count));
    flat_matrix.emplace_back(static_cast<float>(tmpl.coverage_pct));
    flat_matrix.emplace_back(static_cast<float>(tmpl.in_mined_rules));
    flat_matrix.emplace_back(static_cast<float>(tmpl.max_rule_confidence));
    flat_matrix.emplace_back(static_cast<float>(tmpl.avg_rule_confidence));
    flat_matrix.emplace_back(static_cast<float>(tmpl.uses_middle_name));
    flat_matrix.emplace_back(static_cast<float>(tmpl.uses_multiple_firsts));
    flat_matrix.emplace_back(static_cast<float>(tmpl.uses_multiple_middles));
    flat_matrix.emplace_back(static_cast<float>(tmpl.uses_multiple_lasts));
    flat_matrix.emplace_back(static_cast<float>(firm_support_count));
    flat_matrix.emplace_back(static_cast<float>(firm_coverage_pct));
    flat_matrix.emplace_back(static_cast<float>(is_top_template));
    flat_matrix.emplace_back(static_cast<float>(clash));
    flat_matrix.emplace_back(static_cast<float>(stats.num_templates));
    flat_matrix.emplace_back(static_cast<float>(stats.num_investors));
    flat_matrix.emplace_back(static_cast<float>(stats.diversity_ratio));
    flat_matrix.emplace_back(static_cast<float>(stats.is_single_template));
  }

  return flat_matrix;
}

} // namespace email_predictor::features::builder

#pragma once

#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/features/investor_feature_extractor.hpp"
#include "email_predictor/name_decomposer/name_decomposer.hpp"

namespace email_predictor::features::builder {

/**
 * @brief Builds a feature matrix for all candidate templates given an investor
 * and firm.
 *
 * This function constructs one row per candidate template, extracting features
 * from the investor name, template structure, and firm-level usage statistics.
 *
 * This function assumes candidate templates are sorted and are in matching
 * order to training matrices.
 *
 * @param investor_name Decomposed name with flags.
 * @param flags Structural name flags.
 * @param firm_name The canonical firm name, pre-matched to known firms.
 * @param templates All global candidate templates indexed by template ID.
 * @param firm_stats Per-firm summary statistics (template count, diversity,
 * etc.).
 * @param firm_template_usage_map Mapping of firm to template usage metadata.
 * @return A flat matrix of float encoded features, one per candidate template.
 *
 * @note Check Feature builder in email_prediction Python pipeline and
 * notebooks/writeups for details on feature engineering.
 */
std::vector<float> build_feature_rows(
    const name_decomposer::NameDecomposer &investor_name,
    const email_predictor::features::InvestorFeatureExtractor::Flags &flags,
    std::string_view firm_name,
    const std::vector<data_loaders::CandidateTemplate> &templates,
    const std::unordered_map<std::string, data_loaders::FirmStats> &firm_stats,
    const std::unordered_map<
        std::string, std::unordered_map<int, data_loaders::FirmTemplateUsage>>
        &firm_template_usage_map);

} // namespace email_predictor::features::builder

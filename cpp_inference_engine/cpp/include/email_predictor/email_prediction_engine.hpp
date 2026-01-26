#pragma once

#include <memory>
#include <optional>
#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/catboost_template_predictor.hpp"
#include "email_predictor/domain_resolver/domain_resolver.hpp"
#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/light_gbm_template_predictor.hpp"
#include "email_predictor/name_decomposer/name_decomposer.hpp"
#include "third_party/enrichment/rocket_reach_client.hpp"
#include "third_party/verification/hunter_client.hpp"

namespace email_predictor {

/**
 * @brief Represents a single prediction result from the email template engine.
 */
struct EmailPredictionResult {
  std::string email; ///< Fully constructed email address.
  double score;      ///< LightGBM prediction score.
  int template_id;   ///< ID of the predicted template.
  std::optional<third_party::verification::VerificationResult>
      verification_result; ///< Third party api score.
  std::optional<third_party::enrichment::EnrichmentResult>
      enrichment_result; ///< Third party enrichment results.
  // Need for explicit instantiation. For some reason docker builder needs to
  // see full TU when building the templated optional params. CoPilot helped
  // with debugging this.
  ~EmailPredictionResult();
};

/**
 * @brief Main engine class for predicting investor email addresses from names
 * and firms.
 *
 * This class loads a trained LightGBM model, template metadata, and firm
 * statistics. It provides a high-level API for predicting the most likely email
 * templates for a given investor name and firm, and (optionally) constructing a
 * full email address using a known domain.
 */
template <class Pred> class EmailPredictionEngine {
public:
  /**
   * @brief Constructs the prediction engine and loads model and metadata.
   *
   * @param std_predictor Constructed predictor model for standard names.
   * @param complex_predictor Constructed predictor model for complex names.
   * @param std_candidate_templates_path Path to the MessagePack file containing
   * standard name template definitions.
   * @param complex_candidate_templates_path Path to the MessagePack file
   * containing complex name template definitions.
   * @param firm_template_map_path Path to the MessagePack file containing
   * firm-template mappings and stats.
   * @param canonical_firms_path Optional path to the MessagePack file
   * containing firm-domain mappings and stats.
   * @param firm_cache_path Optional path to the MessagePack file containing
   * fuzzy firm matches cache.
   * @param hunter_api_key Optional key for Hunter.io api.
   * @param rocket_api_key Optional key for RocketReach api.
   *
   * @throws std::runtime_error if model or metadata loading fails.
   */
  EmailPredictionEngine(
      std::shared_ptr<Pred> std_predictor,
      std::shared_ptr<Pred> complex_predictor,
      const std::string &std_candidate_templates_path,
      const std::string &complex_candidate_templates_path,
      const std::string &firm_template_map_path,
      const std::optional<std::string> &canonical_firms_path = std::nullopt,
      const std::optional<std::string> &firm_cache_path = std::nullopt,
      std::optional<std::string> hunter_api_key = std::nullopt,
      std::optional<std::string> rocket_api_key = std::nullopt);

  /**
   * @brief Predicts the best matching templates for a given investor and firm.
   * @param investor_name Full name of the investor.
   * @param firm_name Canonical firm name.
   * @param top_k Number of top results to return.
   * @param domain Optional domain string to append to local part.
   * @return A vector of prediction results, optionally including full email
   * address.
   */
  std::vector<EmailPredictionResult>
  predict(const std::string &investor_name, const std::string &firm_name,
          std::size_t top_k = 3,
          std::optional<std::string> domain = std::nullopt) const;

private:
  std::shared_ptr<Pred> std_predictor_;
  std::shared_ptr<Pred> complex_predictor_;
  std::optional<third_party::verification::HunterClient> verification_pipeline_;
  std::optional<third_party::enrichment::RocketReachClient>
      enrichment_pipeline_;
  std::vector<data_loaders::CandidateTemplate> std_templates_;
  std::vector<data_loaders::CandidateTemplate> complex_templates_;
  std::unordered_map<std::string, data_loaders::FirmStats> firm_stats_;
  std::unordered_map<std::string,
                     std::unordered_map<int, data_loaders::FirmTemplateUsage>>
      firm_usage_map_;
  std::optional<domain_resolver::DomainResolver> domain_resolver_;
};

// Explicit instantiation for the predictor classes
template class EmailPredictionEngine<LightGBMTemplatePredictor>;
template class EmailPredictionEngine<CatBoostTemplatePredictor>;

} // namespace email_predictor

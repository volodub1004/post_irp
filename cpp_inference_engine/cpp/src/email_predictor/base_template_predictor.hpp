#pragma once

#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/template_prediction.hpp"

namespace email_predictor {

/**
 * @brief Compile time base for email template predictors.
 *
 * Defines the core interface for ranking and scoring candidate email templates
 * using structured feature data. Implementations of this interface may use
 * different underlying machine learning models (e.g., LightGBM, CatBoost).
 */
template <class Derived> class BaseTemplatePredictor {
public:
  /**
   * @brief Predicts and ranks the top-k email templates based on input
   * features.
   *
   * @param flat_matrix Float encoded flat feature matrix.
   * @param templates Metadata for the corresponding candidate templates.
   * @param top_k The number of top-ranked predictions to return (default is 3).
   * @return A sorted vector of TemplatePrediction objects with scores and
   * metadata.
   */
  std::vector<TemplatePrediction> predict_top_templates(
      const std::vector<float> &flat_matrix,
      const std::vector<data_loaders::CandidateTemplate> &templates,
      std::size_t top_k = 3) const {
    return derived().predict_top_templates_impl(flat_matrix, templates, top_k);
  }

protected:
  // Reference to derived instance
  const Derived &derived() const { return static_cast<const Derived &>(*this); }
};

} // namespace email_predictor

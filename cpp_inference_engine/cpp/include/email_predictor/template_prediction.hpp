#pragma once

#include <cstddef>

#include "data_loader/templates_loader.hpp"

namespace email_predictor {

// constexpr for compile time optimization
constexpr int FEATURES_PER_ROW = 27;

/**
 * @brief Structure representing a top k email template prediction result.
 */
struct TemplatePrediction {
  std::size_t index; ///< Index in the input row vector.
  double score;      ///< Prediction score returned by LightGBM.
  int template_id;   ///< Unique identifier for the template.
  const data_loaders::CandidateTemplate
      *metadata; ///< Pointer to metadata for the predicted template.
};

} // namespace email_predictor

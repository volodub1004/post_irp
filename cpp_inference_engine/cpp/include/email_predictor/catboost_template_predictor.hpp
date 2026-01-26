#pragma once

#include <string>
#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/base_template_predictor.hpp"
#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/template_prediction.hpp"

// CatBoost headers - CoPilot was used to help build and include relevant
// headers for catboost.
#include "catboost/libs/model_interface/c_api.h"

namespace email_predictor {
/**
 * @brief Predicts ranking scores for candidate email templates using a CatBoost
 * model.
 */
class CatBoostTemplatePredictor
    : public BaseTemplatePredictor<CatBoostTemplatePredictor> {
public:
  /**
   * @brief Constructs the predictor by loading a CatBoost model from file.
   * @param model_path Path to the CatBoost binary model (.cbm).
   * @throws std::runtime_error if model loading fails.
   */
  explicit CatBoostTemplatePredictor(const std::string &model_path);

  /**
   * @brief Destructor to release CatBoost model resources.
   */
  ~CatBoostTemplatePredictor();

  /**
   * \copydoc BaseTemplatePredictor::predict_top_templates
   */
  std::vector<TemplatePrediction> predict_top_templates(
      const std::vector<float> &flat_matrix,
      const std::vector<data_loaders::CandidateTemplate> &templates,
      std::size_t top_k = 3) const;

private:
  ModelCalcerHandle *model_{nullptr}; ///< Loaded CatBoost model
};

} // namespace email_predictor

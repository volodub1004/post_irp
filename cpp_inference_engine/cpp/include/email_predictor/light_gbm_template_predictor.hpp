#pragma once

// LightGBM headers
#include <LightGBM/c_api.h>

#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/base_template_predictor.hpp"
#include "email_predictor/features/builder/feature_matrix_builder.hpp"
#include "email_predictor/template_prediction.hpp"

namespace email_predictor {

/**
 * @brief Predicts ranking scores for candidate email templates using a LightGBM
 * model.
 *
 * This class loads a LightGBM model at runtime and provides methods for
 * generating prediction scores and selecting top k ranked templates based on
 * feature vectors derived from investor and firm context.
 */
class LightGBMTemplatePredictor
    : public BaseTemplatePredictor<LightGBMTemplatePredictor> {
public:
  /**
   * @brief Constructs the predictor by loading a LightGBM model from file.
   * @param model_path Path to the LightGBM.txt.
   * @throws std::runtime_error if model loading fails.
   */
  explicit LightGBMTemplatePredictor(const std::string &model_path);

  /**
   * @brief Releases LightGBM model resources.
   */
  ~LightGBMTemplatePredictor();

  /**
   * @brief Predicts raw LightGBM scores for each input feature row.
   * @param flat_matrix Float encoded flat feature matrix.
   * @return A vector of raw prediction scores.
   * @throws std::runtime_error if prediction fails due to model or shape
   * mismatch.
   */
  std::vector<double>
  predict_scores(const std::vector<float> &flat_matrix) const;

  /**
   * \copydoc BaseTemplatePredictor::predict_top_templates
   */
  std::vector<TemplatePrediction> predict_top_templates(
      const std::vector<float> &flat_matrix,
      const std::vector<data_loaders::CandidateTemplate> &templates,
      std::size_t top_k = 3) const;

private:
  BoosterHandle booster_{nullptr}; ///< Handle to the loaded LightGBM model.
  int num_iterations_{0}; ///< Number of boosting rounds in the loaded model.
};

} // namespace email_predictor

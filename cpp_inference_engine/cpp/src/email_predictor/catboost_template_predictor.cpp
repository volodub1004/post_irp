#include "email_predictor/catboost_template_predictor.hpp"

namespace email_predictor {

CatBoostTemplatePredictor::CatBoostTemplatePredictor(
    const std::string &model_path) {
  // Load model
  model_ = ModelCalcerCreate();
  if (!model_) {
    throw std::runtime_error("Failed to create CatBoost model handle.");
  }
  if (!LoadFullModelFromFile(model_, model_path.c_str())) {
    throw std::runtime_error("Failed to load CatBoost model from file: " +
                             model_path);
  }
}

CatBoostTemplatePredictor::~CatBoostTemplatePredictor() {
  // Free resources
  if (model_) {
    ModelCalcerDelete(model_);
  }
}

std::vector<TemplatePrediction>
CatBoostTemplatePredictor::predict_top_templates(
    const std::vector<float> &flat_matrix,
    const std::vector<data_loaders::CandidateTemplate> &templates,
    std::size_t top_k) const {

  if (flat_matrix.size() != templates.size() * FEATURES_PER_ROW) {
    throw std::invalid_argument("Mismatched rows and templates size.");
  }

  const std::size_t num_rows = flat_matrix.size() / FEATURES_PER_ROW;

  // Convert flat vector into float** layout
  std::vector<const float *> float_ptrs;
  float_ptrs.reserve(num_rows);
  for (std::size_t i = 0; i < num_rows; ++i) {
    float_ptrs.push_back(&flat_matrix[i * FEATURES_PER_ROW]);
  }

  std::vector<double> predictions(num_rows);

  // Perform prediction
  if (!CalcModelPredictionFlat(model_,             // ModelCalcerHandle*
                               num_rows,           // Number of rows (objects)
                               float_ptrs.data(),  // floatFeatures: float**
                               FEATURES_PER_ROW,   // Features per row
                               predictions.data(), // Output buffer
                               predictions.size()  // Output size
                               )) {
    throw std::runtime_error("CatBoost prediction failed.");
  }

  // Package results
  std::vector<TemplatePrediction> results;
  results.reserve(num_rows);

  for (std::size_t i = 0; i < num_rows; ++i) {
    results.emplace_back(
        TemplatePrediction{.index = i,
                           .score = predictions[i],
                           .template_id = templates[i].template_id,
                           .metadata = &templates[i]});
  }

  // Partial sort to get top-k by descending score
  std::partial_sort(
      results.begin(),
      results.begin() +
          static_cast<std::vector<TemplatePrediction>::difference_type>(
              std::min(top_k, results.size())),
      results.end(),
      [](const TemplatePrediction &a, const TemplatePrediction &b) noexcept {
        return a.score > b.score;
      });

  if (results.size() > top_k) {
    results.resize(top_k);
  }

  return results;
}

} // namespace email_predictor

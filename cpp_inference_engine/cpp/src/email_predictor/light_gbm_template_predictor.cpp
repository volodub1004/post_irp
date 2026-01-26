#include "email_predictor/light_gbm_template_predictor.hpp"

#include <LightGBM/c_api.h>
#include <algorithm>
#include <cstring>
#include <numeric>
#include <stdexcept>

namespace email_predictor {
LightGBMTemplatePredictor::LightGBMTemplatePredictor(
    const std::string &model_path) {
  // Load model
  if (LGBM_BoosterCreateFromModelfile(model_path.c_str(), &num_iterations_,
                                      &booster_) != 0 ||
      booster_ == nullptr) {
    throw std::runtime_error("Failed to load LightGBM model from: " +
                             model_path);
  }
}

LightGBMTemplatePredictor::~LightGBMTemplatePredictor() {
  if (booster_) {
    // Free
    LGBM_BoosterFree(booster_);
  }
}

std::vector<double> LightGBMTemplatePredictor::predict_scores(
    const std::vector<float> &flat_matrix) const {
  if (flat_matrix.empty()) {
    return {}; // Empty
  }

  // Encode feature matrix
  const size_t num_rows = flat_matrix.size() / FEATURES_PER_ROW;

  std::vector<double> predictions(num_rows);
  int64_t out_len = 0;

  const int err = LGBM_BoosterPredictForMat(
      booster_,                                      // BoosterHandle
      static_cast<const void *>(flat_matrix.data()), // feature matrix
      C_API_DTYPE_FLOAT32,                           // data type
      static_cast<int32_t>(num_rows),                // number of rows
      static_cast<int32_t>(FEATURES_PER_ROW),        // number of columns
      1,                                             // row major
      C_API_PREDICT_NORMAL,                          // prediction type
      0,                                             // start iteration
      num_iterations_,   // number of boosting iterations
      "",                // extra parameters
      &out_len,          // number of output rows
      predictions.data() // output buffer
  );

  if (err != 0) {
    throw std::runtime_error("LightGBM prediction failed with error code: " +
                             std::to_string(err));
  }

  // Only resize if necessary
  if (static_cast<size_t>(out_len) != num_rows) {
    predictions.resize(
        static_cast<size_t>(out_len)); // Shouldn't happen, for robustness
  }

  return predictions;
}

std::vector<TemplatePrediction>
LightGBMTemplatePredictor::predict_top_templates(
    const std::vector<float> &flat_matrix,
    const std::vector<data_loaders::CandidateTemplate> &templates,
    std::size_t top_k) const {
  if (flat_matrix.empty() || templates.empty()) {
    return {};
  }

  // Input validation to prevent out of bounds exception
  if (flat_matrix.size() != templates.size() * FEATURES_PER_ROW) {
    throw std::invalid_argument(
        "Size mismatch between rows and candidate templates.");
  }

  const auto scores = predict_scores(flat_matrix);

  // Build results
  std::vector<TemplatePrediction> results;
  results.reserve(scores.size());

  // Assumes candidate templates are sorted by template ID.
  for (std::size_t i = 0; i < scores.size(); ++i) {
    const auto &tmpl = templates[i];

    results.emplace_back(TemplatePrediction{.index = i,
                                            .score = scores[i],
                                            .template_id = tmpl.template_id,
                                            .metadata = &tmpl});
  }

  // Only sort what we need
  const std::size_t sort_size = std::min(top_k, results.size());
  std::partial_sort(
      results.begin(),
      results.begin() +
          static_cast<std::vector<TemplatePrediction>::difference_type>(
              sort_size),
      results.end(),
      [](const TemplatePrediction &a, const TemplatePrediction &b) noexcept {
        return a.score > b.score;
      });

  // Resize only if necessary
  if (results.size() > top_k) {
    results.resize(top_k);
  }

  return results;
}

} // namespace email_predictor
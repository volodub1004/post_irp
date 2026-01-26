/**
 * @file bindings.cpp
 * @brief Python bindings for the Email Prediction Engine using pybind11.
 *
 * This module exposes:
 * - LightGBMTemplatePredictor
 * - CatBoostTemplatePredictor
 * - LightGBMEmailPredictionEngine
 * - CatBoostEmailPredictionEngine
 * - EmailPredictionResult
 *
 * Usage example (in Python):
 *     from email_predictor import CatBoostEmailPredictionEngine,
 * CatBoostTemplatePredictor
 *
 *     std = CatBoostTemplatePredictor("model_std.cbm")
 *     comp = CatBoostTemplatePredictor("model_comp.cbm")
 *     engine = CatBoostEmailPredictionEngine(std, comp,
 * "std_templates.msgpack", "complex_templates.msgpack", "firm_map.msgpack")
 *     results = engine.predict("Jane Doe", "Blackstone",
 * domain="blackstone.com")
 *
 * Note: CoPilot was used to assist in the creation of this code. Especially in
 * debugging and doing optional parameters.
 */

#include <memory>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "email_predictor/catboost_template_predictor.hpp"
#include "email_predictor/email_prediction_engine.hpp"
#include "email_predictor/light_gbm_template_predictor.hpp"

namespace py = pybind11;
using namespace email_predictor;
using namespace third_party::enrichment;
using namespace third_party::verification;

PYBIND11_MODULE(email_predictor, m) {
  m.doc() = R"pbdoc(
    Python bindings for the Email Prediction Engine.

    This module provides a high-performance interface for predicting likely email templates
    from name + firm inputs, based on LightGBM or CatBoost models trained on investor data.

    Classes:
        - EmailPredictionEngine
        - BaseTemplatePredictor (abstract)
        - LightGBMTemplatePredictor
        - CatBoostTemplatePredictor
        - EmailPredictionResult
    )pbdoc";

  // VerificationResult
  py::class_<VerificationResult>(m, "VerificationResult", R"pbdoc(
Result of an email verification lookup.

Attributes:
    email (str): The email address that was verified.
    status (str): Provider status label (e.g., "valid", "invalid", "unknown").
    score (int): Confidence score in [0, 100].
    is_deliverable (bool): True if provider marks this address as deliverable.
    raw_json (str): Full raw JSON response from the verification API.
)pbdoc")
      .def_readonly("email", &VerificationResult::email)
      .def_readonly("status", &VerificationResult::status)
      .def_readonly("score", &VerificationResult::score)
      .def_readonly("is_deliverable", &VerificationResult::is_deliverable)
      .def_readonly("raw_json", &VerificationResult::raw_json);

  // EnrichmentResult
  py::class_<EnrichmentResult>(m, "EnrichmentResult", R"pbdoc(
Enriched contact information (e.g., RocketReach).

Attributes:
    email (str): The email that was queried or predicted.
    name (str): Full name of the contact.
    job_title (str): Current job title or role.
    linkedin_url (str): LinkedIn profile URL, if available.
    location (str): Contact's location string.
    phone (str): Primary phone number, if available.
    raw_json (str): Full raw JSON response from the enrichment API.
)pbdoc")
      .def_readonly("email", &EnrichmentResult::email)
      .def_readonly("name", &EnrichmentResult::name)
      .def_readonly("job_title", &EnrichmentResult::job_title)
      .def_readonly("linkedin_url", &EnrichmentResult::linkedin_url)
      .def_readonly("location", &EnrichmentResult::location)
      .def_readonly("phone", &EnrichmentResult::phone)
      .def_readonly("raw_json", &EnrichmentResult::raw_json);

  // Prediction result struct
  py::class_<EmailPredictionResult>(m, "EmailPredictionResult", R"pbdoc(
        Struct containing the result of a predicted email.

        Attributes:
            email (str): Full predicted email address.
            score (float): Model confidence score.
            template_id (int): ID of the matched email template.
            verification_result (VerificationResult | None): Verification payload if available.
            enrichment_result (EnrichmentResult | None): Enrichment payload if available.
    )pbdoc")
      .def_readonly("email", &EmailPredictionResult::email)
      .def_readonly("score", &EmailPredictionResult::score)
      .def_readonly("template_id", &EmailPredictionResult::template_id)
      .def_property_readonly(
          "verification_result",
          [](const EmailPredictionResult &s) -> const VerificationResult * {
            return s.verification_result ? &*s.verification_result : nullptr;
          },
          py::return_value_policy::reference_internal)
      .def_property_readonly(
          "enrichment_result",
          [](const EmailPredictionResult &s) -> const EnrichmentResult * {
            return s.enrichment_result ? &*s.enrichment_result : nullptr;
          },
          py::return_value_policy::reference_internal);

  // LightGBM predictor
  py::class_<LightGBMTemplatePredictor,
             std::shared_ptr<LightGBMTemplatePredictor>>(
      m, "LightGBMTemplatePredictor", R"pbdoc(
        Template predictor using LightGBM model.
    )pbdoc")
      .def(py::init<const std::string &>(), py::arg("model_path"));

  // CatBoost predictor
  py::class_<CatBoostTemplatePredictor,
             std::shared_ptr<CatBoostTemplatePredictor>>(
      m, "CatBoostTemplatePredictor", R"pbdoc(
        Template predictor using CatBoost model.
    )pbdoc")
      .def(py::init<const std::string &>(), py::arg("model_path"));

  // LightGBM EmailPredictionEngine
  py::class_<EmailPredictionEngine<LightGBMTemplatePredictor>,
             std::shared_ptr<EmailPredictionEngine<LightGBMTemplatePredictor>>>(
      m, "LightGBMEmailPredictionEngine", R"pbdoc(
    Main engine for predicting investor email addresses using LightGBM predictors.

    This engine uses two LightGBM predictors (standard and complex name models), and loads template
    and firm metadata from MessagePack files.

    Example:
        std = LightGBMTemplatePredictor("std_model.txt")
        comp = LightGBMTemplatePredictor("comp_model.txt")
        engine = LightGBMEmailPredictionEngine(std, comp, "std_templates.msgpack", "complex_templates.msgpack", "firm_map.msgpack")
        results = engine.predict("Alice Smith", "Sequoia Capital", domain="sequoiacap.com")
)pbdoc")
      .def(py::init<std::shared_ptr<LightGBMTemplatePredictor>,
                    std::shared_ptr<LightGBMTemplatePredictor>,
                    const std::string &, const std::string &,
                    const std::string &, std::optional<std::string>,
                    std::optional<std::string>, std::optional<std::string>,
                    std::optional<std::string>>(),
           py::arg("std_predictor"), py::arg("complex_predictor"),
           py::arg("std_candidate_templates_path"),
           py::arg("complex_candidate_templates_path"),
           py::arg("firm_template_map_path"),
           py::arg("canonical_firms_path") = std::nullopt,
           py::arg("firm_cache_path") = std::nullopt,
           py::arg("hunter_api_key") = std::nullopt,
           py::arg("rocket_reach_api_key") = std::nullopt,
           R"pbdoc(
            Construct a LightGBMEmailPredictionEngine with LightGBM predictors.

            Args:
                std_predictor (LightGBMTemplatePredictor): Predictor for standard names.
                complex_predictor (LightGBMTemplatePredictor): Predictor for complex names.
                std_candidate_templates_path (str): Path to standard template definitions.
                complex_candidate_templates_path (str): Path to complex template definitions.
                firm_template_map_path (str): Path to firm-template usage stats.
                canonical_firms_path (str): Path to firm-domain mappings.
                firm_cache_path (str): Path to fuzzy match firm cache.
                hunter_api_key (str): Hunter.io API key for verification.
                rocket_reach_api_key (str): Rocket Reach API key for enrichment.
         )pbdoc")
      .def("predict",
           &EmailPredictionEngine<LightGBMTemplatePredictor>::predict,
           py::arg("investor_name"), py::arg("firm_name"), py::arg("top_k") = 3,
           py::arg("domain") = std::nullopt,
           R"pbdoc(
            Predict the most likely email templates.

            Args:
                investor_name (str): Full name of the investor.
                firm_name (str): Canonical firm name.
                top_k (int): Number of top predictions to return. Default is 3.
                domain (str, optional): If provided, constructs full emails using it. Resolves manually if not.

            Returns:
                List[EmailPredictionResult]: Ranked template predictions.
         )pbdoc");

  // CatBoost EmailPredictionEngine
  py::class_<EmailPredictionEngine<CatBoostTemplatePredictor>,
             std::shared_ptr<EmailPredictionEngine<CatBoostTemplatePredictor>>>(
      m, "CatBoostEmailPredictionEngine", R"pbdoc(
    Main engine for predicting investor email addresses using CatBoost predictors.

    This engine uses two CatBoost predictors (standard and complex name models), and loads template
    and firm metadata from MessagePack files.

    Example:
        std = CatBoostTemplatePredictor("std_model.cbm")
        comp = CatBoostTemplatePredictor("comp_model.cbm")
        engine = CatBoostEmailPredictionEngine(std, comp, "std_templates.msgpack", "complex_templates.msgpack", "firm_map.msgpack")
        results = engine.predict("Alice Smith", "Sequoia Capital", domain="sequoiacap.com")
)pbdoc")
      .def(py::init<std::shared_ptr<CatBoostTemplatePredictor>,
                    std::shared_ptr<CatBoostTemplatePredictor>,
                    const std::string &, const std::string &,
                    const std::string &, std::optional<std::string>,
                    std::optional<std::string>, std::optional<std::string>,
                    std::optional<std::string>>(),
           py::arg("std_predictor"), py::arg("complex_predictor"),
           py::arg("std_candidate_templates_path"),
           py::arg("complex_candidate_templates_path"),
           py::arg("firm_template_map_path"),
           py::arg("canonical_firms_path") = std::nullopt,
           py::arg("firm_cache_path") = std::nullopt,
           py::arg("hunter_api_key") = std::nullopt,
           py::arg("rocket_reach_api_key") = std::nullopt,
           R"pbdoc(
            Construct a CatBoostEmailPredictionEngine with CatBoost predictors.

            Args:
                std_predictor (CatBoostTemplatePredictor): Predictor for standard names.
                complex_predictor (CatBoostTemplatePredictor): Predictor for complex names.
                std_candidate_templates_path (str): Path to standard template definitions.
                complex_candidate_templates_path (str): Path to complex template definitions.
                firm_template_map_path (str): Path to firm-template usage stats.
                canonical_firms_path (str): Path to firm-domain mappings.
                firm_cache_path (str): Path to fuzzy match firm cache.
                hunter_api_key (str): Hunter.io API key for verification.
                rocket_reach_api_key (str): Rocket Reach API key for enrichment.
         )pbdoc")
      .def("predict",
           &EmailPredictionEngine<CatBoostTemplatePredictor>::predict,
           py::arg("investor_name"), py::arg("firm_name"), py::arg("top_k") = 3,
           py::arg("domain") = std::nullopt,
           R"pbdoc(
            Predict the most likely email templates.

            Args:
                investor_name (str): Full name of the investor.
                firm_name (str): Canonical firm name.
                top_k (int): Number of top predictions to return. Default is 3.
                domain (str, optional): If provided, constructs full emails using it. Resolves manually if not.

            Returns:
                List[EmailPredictionResult]: Ranked template predictions.
         )pbdoc");
}

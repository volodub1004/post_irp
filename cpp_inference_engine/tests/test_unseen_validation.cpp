#include <algorithm>
#include <chrono>
#include <filesystem>
#include <gtest/gtest.h>
#include <iostream>
#include <numeric>
#include <unordered_set>

#include "email_predictor/catboost_template_predictor.hpp"
#include "email_predictor/email_prediction_engine.hpp"

using namespace email_predictor;
namespace fs = std::filesystem;

static std::filesystem::path base_path =
    std::filesystem::path(__FILE__).parent_path();
static const std::string std_template_path =
    base_path / "../cpp/data/std_candidate_templates.msgpack";
static const std::string complex_template_path =
    base_path / "../cpp/data/complex_candidate_templates.msgpack";
static const std::string firm_map_path =
    base_path / "../cpp/data/firm_template_map.msgpack";
static const std::string std_model_path =
    base_path / "../cpp/model/std_catboost_model.cbm";
static const std::string complex_model_path =
    base_path / "../cpp/model/comp_catboost_model.cbm";

static const std::vector<std::tuple<std::string, std::string, std::string>>
    test_cases = {
        {"gc&h investments", "Jon Yorke", "cooley.com"},
        {"gc&h investments", "William Haddad", "cooley.com"},
        {"cvc", "Huwaida Hassan", "cvc.com"},
        {"cvc", "Daisuke Takatsuki", "cvc.com"},
        {"ardian", "Pierre Lamour", "ardian.com"},
        {"ardian", "Anthony Vanden-Maagdenberg", "ardian.com"},
        {"monroe capital", "Michael Hayes", "monroecap.com"},
        {"monroe capital", "Dimitri Stathopoulos", "monroecap.com"},
        {"partners group", "Shunsuke Tanahashi", "partnersgroup.com"},
        {"partners group", "Hannes Eichelberger", "partnersgroup.com"},
        {"hps investment partners", "Matthieu Boulanger", "hpspartners.com"},
        {"hps investment partners", "Jad' Mouawad", "hpspartners.com"},
        {"warburg pincus", "Nick Xue", "warburgpincus.com"},
        {"warburg pincus", "Nikunj Kothari", "warburgpincus.com"},
        {"bridgepoint", "Tiyam Afshari", "bridgepoint.eu"},
        {"bridgepoint", "Katie Cotterell", "bridgepoint.eu"},
        {"harbourvest partners", "Hannes Valtonen", "harbourvest.com"},
        {"harbourvest partners", "Tao Guo", "harbourvest.com"},
        {"brown brothers harriman", "Alexandra Toskovich", "bbh.com"},
        {"brown brothers harriman", "Alan O'Sullivan", "bbh.com"},
        {"ta associates", "Harry Mahadevan", "ta.com"},
        {"ta associates", "Jacob Creiger-Combs", "ta.com"},
        {"brown advisory", "Maneesh Bajaj", "brownadvisory.com"},
        {"brown advisory", "William Pollard-Clark", "brownadvisory.com"},
};

TEST(UnseenValidationTest, PredictFromUnseenInvestors) {
  ASSERT_TRUE(fs::exists(std_model_path));
  ASSERT_TRUE(fs::exists(complex_model_path));
  ASSERT_TRUE(fs::exists(std_template_path));
  ASSERT_TRUE(fs::exists(complex_template_path));
  ASSERT_TRUE(fs::exists(firm_map_path));

  // Catboost seems to perform the best
  EmailPredictionEngine<CatBoostTemplatePredictor> engine(
      std::make_shared<CatBoostTemplatePredictor>(std_model_path),
      std::make_shared<CatBoostTemplatePredictor>(complex_model_path),
      std_template_path, complex_template_path, firm_map_path);

  // Predict each investor and print results
  for (const auto &[firm, investor, domain] : test_cases) {
    // Predict
    auto preds = engine.predict(investor, firm, 3, domain);

    std::cout << investor << " at " << firm
              << " top three predictions (in order) :" << std::endl;
    for (size_t i = 0; i < preds.size(); ++i) {
      std::cout << i << ". " << preds[i].email << std::endl;
    }

    std::cout << std::endl;
  }
}
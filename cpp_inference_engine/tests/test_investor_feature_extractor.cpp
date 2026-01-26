#include "email_predictor/features/investor_feature_extractor.hpp"
#include <gtest/gtest.h>

using namespace email_predictor::features;

TEST(InvestorFeatureExtractorTest, DetectsGermanCharacters) {
  auto flags = InvestorFeatureExtractor::extract("Jürgen Müller");
  EXPECT_TRUE(flags.has_german_char);
  EXPECT_TRUE(flags.has_nfkd_normalized); // Stripped back to ascii so no longer
                                          // has german char
  EXPECT_FALSE(flags.has_nickname);
}

TEST(InvestorFeatureExtractorTest, DetectsNFKDNormalization) {
  auto flags = InvestorFeatureExtractor::extract("Élodie"); // É -> E
  EXPECT_TRUE(flags.has_nfkd_normalized);
  EXPECT_FALSE(flags.has_german_char);
  EXPECT_FALSE(flags.has_nickname);
}

TEST(InvestorFeatureExtractorTest, DetectsNicknames) {
  auto flags = InvestorFeatureExtractor::extract("William Gates");
  EXPECT_TRUE(flags.has_nickname); // "william" is in NICKNAME_MAP
  EXPECT_FALSE(flags.has_german_char);
  EXPECT_FALSE(flags.has_nfkd_normalized);
}

TEST(InvestorFeatureExtractorTest, MixedCaseAndSpacingHandled) {
  auto flags = InvestorFeatureExtractor::extract("  MICHAEL   Öztürk ");
  EXPECT_TRUE(flags.has_german_char);     // ö
  EXPECT_TRUE(flags.has_nickname);        // michael -> mike
  EXPECT_TRUE(flags.has_nfkd_normalized); // German char picked up
}

TEST(InvestorFeatureExtractorTest, HandlesNonMatchesGracefully) {
  auto flags = InvestorFeatureExtractor::extract("Trevor Johnson");
  EXPECT_FALSE(flags.has_german_char);
  EXPECT_FALSE(flags.has_nfkd_normalized);
  EXPECT_FALSE(flags.has_nickname);
}

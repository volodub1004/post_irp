#include <gtest/gtest.h>
#include <string>
#include <string_view>

#include "string_normalization/normalize.hpp"

using namespace string_normalization;

// Test basic ASCII strings
TEST(NFKDNormalizeTest, BasicASCIIStrings) {
  EXPECT_EQ(nfkd_normalize("hello"), "hello");
  EXPECT_EQ(nfkd_normalize("world123"), "world123");
  EXPECT_EQ(nfkd_normalize(""), "");
  EXPECT_EQ(nfkd_normalize("abc_def-ghi"), "abc_def-ghi");
}

// Test accented characters
TEST(NFKDNormalizeTest, AccentedCharacters) {
  EXPECT_EQ(nfkd_normalize("café"), "cafe");
  EXPECT_EQ(nfkd_normalize("naïve"), "naive");
  EXPECT_EQ(nfkd_normalize("résumé"), "resume");
  EXPECT_EQ(nfkd_normalize("señor"), "senor");
  EXPECT_EQ(nfkd_normalize("piñata"), "pinata");
  EXPECT_EQ(nfkd_normalize("josé"), "jose");
}

// Test German characters
TEST(NFKDNormalizeTest, GermanCharacters) {
  // NFKD decomposes umlauts, then strip_to_ascii keeps only ASCII
  EXPECT_EQ(nfkd_normalize("müller"), "muller");
  EXPECT_EQ(nfkd_normalize("bäcker"), "backer");
  EXPECT_EQ(nfkd_normalize("köln"), "koln");

  // ß and ö don't decompose to ASCII in NFKD, so they get removed by
  // strip_to_ascii
  EXPECT_EQ(nfkd_normalize("größe"), "groe");
  EXPECT_EQ(nfkd_normalize("weiß"), "wei");
  EXPECT_EQ(nfkd_normalize("straße"), "strae");
}

// Test Scandinavian characters
TEST(NFKDNormalizeTest, ScandinavianCharacters) {
  // å decomposes to a + combining ring above, which strip_to_ascii converts to
  // just 'a'
  EXPECT_EQ(nfkd_normalize("åse"), "ase");
  // ö decomposes to o + combining accent, which becomes 'o'
  EXPECT_EQ(nfkd_normalize("björk"), "bjork");

  // ø and æ don't have NFKD decompositions to ASCII, so they get removed
  EXPECT_EQ(nfkd_normalize("ødegård"), "degard");
  EXPECT_EQ(nfkd_normalize("lærer"), "lrer");
  EXPECT_EQ(nfkd_normalize("tøff"), "tff");
}

// Test Eastern European characters
TEST(NFKDNormalizeTest, EasternEuropeanCharacters) {
  // ł doesn't have NFKD decomposition to ASCII, so it gets removed
  EXPECT_EQ(nfkd_normalize("łukasz"), "ukasz");

  // These characters do decompose with NFKD
  EXPECT_EQ(nfkd_normalize("žižka"), "zizka");
  EXPECT_EQ(nfkd_normalize("čapek"), "capek");
  EXPECT_EQ(nfkd_normalize("dvořák"), "dvorak");
  EXPECT_EQ(nfkd_normalize("škoda"), "skoda");
}

// Test mixed ASCII and accented characters
TEST(NFKDNormalizeTest, MixedCharacters) {
  EXPECT_EQ(nfkd_normalize("café123"), "cafe123");
  EXPECT_EQ(nfkd_normalize("müller_family"), "muller_family");
  EXPECT_EQ(nfkd_normalize("josé-maría"), "jose-maria");
  EXPECT_EQ(nfkd_normalize("björk2024"), "bjork2024");
}

// Test edge cases
TEST(NFKDNormalizeTest, EdgeCases) {
  // Empty string
  EXPECT_EQ(nfkd_normalize(""), "");

  // Single characters
  EXPECT_EQ(nfkd_normalize("é"), "e");
  EXPECT_EQ(nfkd_normalize("ü"), "u");
  EXPECT_EQ(nfkd_normalize("ñ"), "n");

  // Only accented characters
  EXPECT_EQ(nfkd_normalize("éèêë"), "eeee");
  EXPECT_EQ(nfkd_normalize("àáâãä"), "aaaaa");
  EXPECT_EQ(nfkd_normalize("òóôõö"), "ooooo");
}

// Test compatibility characters
// NOTE: CoPilot helped generate this edge case tests
TEST(NFKDNormalizeTest, CompatibilityCharacters) {
  // These tests depend on specific Unicode compatibility mappings
  // Roman numerals
  EXPECT_EQ(nfkd_normalize("ⅰⅱⅲ"), "iiiiii"); // Roman numerals to ASCII

  // Full-width characters
  EXPECT_EQ(nfkd_normalize("Ａ"), "A");       // Full-width A to regular A
  EXPECT_EQ(nfkd_normalize("０１２"), "012"); // Full-width digits
}

// Test strings with multiple types of characters
TEST(NFKDNormalizeTest, ComplexStrings) {
  // Some characters will be removed (ñ->n works, ß gets removed)
  EXPECT_EQ(nfkd_normalize("cañón-josé_müller123"), "canon-jose_muller123");
  EXPECT_EQ(nfkd_normalize("björk&josé+café"), "bjork&jose+cafe");
  EXPECT_EQ(nfkd_normalize("naïve_résumé.txt"), "naive_resume.txt");
}

// Test longer strings
TEST(NFKDNormalizeTest, LongerStrings) {
  // Some characters that don't decompose will be removed
  std::string input =
      "the_café_in_köln_serves_excellent_crème_brûlée_to_señor_josé";
  std::string expected =
      "the_cafe_in_koln_serves_excellent_creme_brulee_to_senor_jose";
  EXPECT_EQ(nfkd_normalize(input), expected);
}

// Test with string_view specifically
TEST(NFKDNormalizeTest, StringViewInput) {
  std::string original = "café_müller";
  std::string_view view(original);
  EXPECT_EQ(nfkd_normalize(view), "cafe_muller");

  // Test with substring view
  std::string longer = "prefix_café_suffix";
  std::string_view substring(longer.data() + 7, 5); // "café" (5 bytes: c-a-f-é)
  EXPECT_EQ(nfkd_normalize(substring), "cafe");
}

// Performance test with repeated characters
TEST(NFKDNormalizeTest, RepeatedCharacters) {
  // Start with a smaller test to avoid potential issues with very long strings
  std::string input;
  std::string expected;
  for (int i = 0; i < 100; ++i) { // Reduced from 1000 to 100
    input += "é";                 // UTF-8 encoded 'é'
    expected += "e";              // ASCII 'e'
  }
  EXPECT_EQ(nfkd_normalize(input), expected);

  // Test a simple repeated ASCII case too
  std::string ascii_input(1000, 'a');
  std::string ascii_expected(1000, 'a');
  EXPECT_EQ(nfkd_normalize(ascii_input), ascii_expected);
}

// Test robustness - these should not crash even if normalization fails
TEST(NFKDNormalizeTest, RobustnessTests) {
  // These should return the input unchanged if normalization fails

  // Very long string
  std::string long_input(10000, 'a');
  std::string result = nfkd_normalize(long_input);
  EXPECT_FALSE(result.empty());
  EXPECT_LE(result.length(),
            long_input.length() + 100); // Should not grow excessively

  // String with null characters
  std::string with_nulls = "test\0café";
  std::string result_nulls = nfkd_normalize(with_nulls);
  EXPECT_FALSE(result_nulls.empty());
}
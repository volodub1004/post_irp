#include <gtest/gtest.h>

#include "string_normalization/normalize.hpp"

using namespace string_normalization;

TEST(GermanCharNormalizationTest, NoReplacement) {
  EXPECT_EQ(replace_german_chars("hello"), "hello");
  EXPECT_EQ(replace_german_chars("smith"), "smith");
  EXPECT_EQ(replace_german_chars("john doe"), "john doe");
}

TEST(GermanCharNormalizationTest, IndividualReplacements) {
  EXPECT_EQ(replace_german_chars("ü"), "ue");
  EXPECT_EQ(replace_german_chars("ö"), "oe");
  EXPECT_EQ(replace_german_chars("ä"), "ae");
  EXPECT_EQ(replace_german_chars("ß"), "ss");
  EXPECT_EQ(replace_german_chars("ø"), "o");
  EXPECT_EQ(replace_german_chars("å"), "aa");
}

TEST(GermanCharNormalizationTest, MixedString) {
  EXPECT_EQ(replace_german_chars("müller jäger"), "mueller jaeger");
  EXPECT_EQ(replace_german_chars("große straße"), "grosse strasse");
  EXPECT_EQ(replace_german_chars("kåre østergård"), "kaare ostergaard");
}

TEST(GermanCharNormalizationTest, MultibyteBoundarySafety) {
  std::string input = "übermäßige größenmaßstäbe";
  std::string expected = "uebermaessige groessenmassstaebe";
  EXPECT_EQ(replace_german_chars(input), expected);
}

TEST(GermanCharNormalizationTest, AlreadyNormalized) {
  EXPECT_EQ(replace_german_chars("ae"), "ae");
  EXPECT_EQ(replace_german_chars("ss"), "ss");
  EXPECT_EQ(replace_german_chars("oe"), "oe");
}

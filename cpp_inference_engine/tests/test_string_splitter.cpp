#include "string_normalization/splitter.hpp"
#include <gtest/gtest.h>
#include <string_view>

using namespace string_normalization;

TEST(StringViewSplitterTest, BasicSplit) {
  StringViewSplitter splitter("a_b_c", '_');
  std::vector<std::string_view> expected = {"a", "b", "c"};

  std::vector<std::string_view> result;
  while (auto part = splitter.next()) {
    result.push_back(*part);
  }

  EXPECT_EQ(result, expected);
}

TEST(StringViewSplitterTest, EmptyString) {
  StringViewSplitter splitter("", '_');
  EXPECT_FALSE(splitter.next().has_value());
}

TEST(StringViewSplitterTest, NoDelimiter) {
  StringViewSplitter splitter("abc", '_');
  auto result = splitter.next();
  ASSERT_TRUE(result.has_value());
  EXPECT_EQ(*result, "abc");
  EXPECT_FALSE(splitter.next().has_value());
}

TEST(StringViewSplitterTest, LeadingAndTrailingDelimiters) {
  StringViewSplitter splitter("_a_b_", '_');
  std::vector<std::string_view> expected = {"a", "b"};

  std::vector<std::string_view> result;
  while (auto part = splitter.next()) {
    result.push_back(*part);
  }

  EXPECT_EQ(result, expected);
}

TEST(StringViewSplitterTest, ConsecutiveDelimiters) {
  StringViewSplitter splitter("x__y___z", '_');
  std::vector<std::string_view> expected = {"x", "y", "z"};

  std::vector<std::string_view> result;
  while (auto part = splitter.next()) {
    result.push_back(*part);
  }

  EXPECT_EQ(result, expected);
}

TEST(StringViewSplitterTest, SplitAllAndSplitAllStringsMatch) {
  std::string_view input = "alpha_beta_gamma";
  StringViewSplitter splitter1(input, '_');
  StringViewSplitter splitter2(input, '_');

  auto views = splitter1.split_all();
  auto strings = splitter2.split_all_strings();

  ASSERT_EQ(views.size(), strings.size());
  for (size_t i = 0; i < views.size(); ++i) {
    EXPECT_EQ(views[i], strings[i]);
  }
}

TEST(StringViewSplitterTest, SplitAllPreservesEmptyEntries) {
  std::string_view input = "foo__bar___baz";
  StringViewSplitter splitter(input, '_');

  std::vector<std::string_view> expected = {"foo", "bar", "baz"};
  auto result = splitter.split_all();

  EXPECT_EQ(result, expected);
}

TEST(StringViewSplitterTest, SplitAllHandlesLeadingTrailingAndContiguous) {
  std::string_view input = "_a__b_";
  StringViewSplitter splitter(input, '_');

  std::vector<std::string_view> expected = {"a", "b"};
  auto result = splitter.split_all();

  EXPECT_EQ(result, expected);
}

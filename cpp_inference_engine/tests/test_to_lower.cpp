#include "string_normalization/normalize.hpp"
#include <gtest/gtest.h>

using namespace string_normalization;

TEST(ToLowerTest, HandlesAsciiLowering) {
  EXPECT_EQ(to_lower("ABC"), "abc");
  EXPECT_EQ(to_lower("aBc123!"), "abc123!");
  EXPECT_EQ(to_lower(""), "");
  EXPECT_EQ(to_lower("NoChangeNeeded"), "nochangeneeded");
}

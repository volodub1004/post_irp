#include "data_loader/templates_loader.hpp"
#include "email_predictor/local_part_resolver/resolve_email_local_part.hpp"
#include "email_predictor/name_decomposer/name_decomposer.hpp"
#include <gtest/gtest.h>

#include <optional>
#include <string>
#include <vector>

using namespace email_predictor::local_part_resolver;
using namespace email_predictor::name_decomposer;
using namespace data_loaders;

TEST(ResolveEmailLocalPartTest, BasicFullNameResolution) {
  NameDecomposer decomposer("John Michael Smith");

  std::vector<TemplateToken> tokens = {
      TemplateToken{TemplateToken::Group::First, 0, true, false, false, false,
                    false, false, std::nullopt},
      TemplateToken{TemplateToken::Group::Last, 0, true, false, false, false,
                    false, false, std::make_optional<std::string>("_")},
      TemplateToken{TemplateToken::Group::Last, 0, true, false, false, false,
                    false, false, std::nullopt}};

  std::optional<std::string> result =
      resolve_email_local_part(decomposer, tokens);
  ASSERT_TRUE(result.has_value());
  EXPECT_EQ(result.value(), "john_smith");
}

TEST(ResolveEmailLocalPartTest, InitialsOnly) {
  NameDecomposer decomposer("Alice Beatrice Carter");

  std::vector<TemplateToken> tokens = {
      TemplateToken{TemplateToken::Group::First, 0, false, false, false, false,
                    false, true, std::nullopt},
      TemplateToken{TemplateToken::Group::Middle, 0, false, false, false, false,
                    false, true, std::nullopt},
      TemplateToken{TemplateToken::Group::Last, 0, false, false, false, false,
                    false, true, std::nullopt}};

  std::optional<std::string> result =
      resolve_email_local_part(decomposer, tokens);
  ASSERT_TRUE(result.has_value());
  EXPECT_EQ(result.value(), "abc");
}

TEST(ResolveEmailLocalPartTest, InvalidIndexReturnsNullopt) {
  NameDecomposer decomposer("Jane Doe");

  std::vector<TemplateToken> tokens = {
      TemplateToken{TemplateToken::Group::Middle, 1, true, false, false, false,
                    false, false, std::nullopt}};

  std::optional<std::string> result =
      resolve_email_local_part(decomposer, tokens);
  EXPECT_FALSE(result.has_value());
}

TEST(ResolveEmailLocalPartTest, SeparatorOnlyTemplate) {
  NameDecomposer decomposer("Foo Bar");

  std::vector<TemplateToken> tokens = {
      TemplateToken{.separator = std::make_optional<std::string>("-")}};

  std::optional<std::string> result =
      resolve_email_local_part(decomposer, tokens);
  ASSERT_TRUE(result.has_value());
  EXPECT_EQ(result.value(), "-");
}

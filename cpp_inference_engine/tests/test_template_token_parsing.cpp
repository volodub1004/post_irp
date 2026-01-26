#include "data_loader/templates_loader.hpp"

#include <gtest/gtest.h>
#include <string>
#include <vector>

using data_loaders::parse_token_sequence;
using data_loaders::TemplateToken;

TEST(TemplateTokenParsingTest, ParsesBasicNameTokens) {
  auto tokens =
      parse_token_sequence({"f_0", "middle_nfkd_1", "last_nickname_0"});
  ASSERT_EQ(tokens.size(), 3);

  EXPECT_EQ(tokens[0].group, TemplateToken::Group::First);
  EXPECT_FALSE(tokens[0].separator);
  EXPECT_EQ(tokens[0].index, 0);
  EXPECT_EQ(tokens[0].use_nfkd, false);
  EXPECT_EQ(tokens[0].use_nickname, false);
  EXPECT_EQ(tokens[0].use_original, false);
  EXPECT_EQ(tokens[0].use_translit, false);
  EXPECT_EQ(tokens[0].use_surname_particle, false);
  EXPECT_EQ(tokens[0].use_initial, true);

  EXPECT_EQ(tokens[1].group, TemplateToken::Group::Middle);
  EXPECT_FALSE(tokens[1].separator);
  EXPECT_EQ(tokens[1].index, 1);
  EXPECT_EQ(tokens[1].use_nfkd, true);
  EXPECT_EQ(tokens[1].use_nickname, false);
  EXPECT_EQ(tokens[1].use_original, false);
  EXPECT_EQ(tokens[1].use_translit, false);
  EXPECT_EQ(tokens[1].use_surname_particle, false);
  EXPECT_EQ(tokens[2].use_initial, false);

  EXPECT_EQ(tokens[2].group, TemplateToken::Group::Last);
  EXPECT_FALSE(tokens[2].separator);
  EXPECT_EQ(tokens[2].index, 0);
  EXPECT_EQ(tokens[2].use_nfkd, false);
  EXPECT_EQ(tokens[2].use_nickname, true);
  EXPECT_EQ(tokens[2].use_original, false);
  EXPECT_EQ(tokens[2].use_translit, false);
  EXPECT_EQ(tokens[2].use_surname_particle, false);
  EXPECT_EQ(tokens[2].use_initial, false);
}

TEST(TemplateTokenParsingTest, ParsesSeparatorsCorrectly) {
  auto tokens = parse_token_sequence({"_", ".", "-"});
  ASSERT_EQ(tokens.size(), 3);
  for (const auto &t : tokens) {
    EXPECT_TRUE(t.separator);
  }
}

TEST(TemplateTokenParsingTest, HandlesMixedTokens) {
  auto tokens = parse_token_sequence({"f_nfkd_2", "-", "last_nfkd_translit_1"});
  ASSERT_EQ(tokens.size(), 3);

  EXPECT_EQ(tokens[0].group, TemplateToken::Group::First);
  EXPECT_FALSE(tokens[0].separator);
  EXPECT_EQ(tokens[0].index, 2);
  EXPECT_EQ(tokens[0].use_nfkd, true);
  EXPECT_EQ(tokens[0].use_nickname, false);
  EXPECT_EQ(tokens[0].use_original, false);
  EXPECT_EQ(tokens[0].use_translit, false);
  EXPECT_EQ(tokens[0].use_surname_particle, false);
  EXPECT_EQ(tokens[0].use_initial, true);

  EXPECT_TRUE(tokens[1].separator);

  EXPECT_EQ(tokens[2].group, TemplateToken::Group::Last);
  EXPECT_FALSE(tokens[2].separator);
  EXPECT_EQ(tokens[2].index, 1);
  EXPECT_EQ(tokens[2].use_nfkd, true);
  EXPECT_EQ(tokens[2].use_nickname, false);
  EXPECT_EQ(tokens[2].use_original, false);
  EXPECT_EQ(tokens[2].use_translit, true);
  EXPECT_EQ(tokens[2].use_surname_particle, false);
  EXPECT_EQ(tokens[2].use_initial, false);
}

TEST(TemplateTokenParsingTest, InvalidFormatThrows) {
  EXPECT_THROW(parse_token_sequence({"first_badtoken"}), std::runtime_error);
  EXPECT_THROW(parse_token_sequence({"f_"}), std::runtime_error);
  EXPECT_THROW(parse_token_sequence({"first_translit"}), std::runtime_error);
  EXPECT_THROW(parse_token_sequence({"first_nfkd_translit"}),
               std::runtime_error); // no index
}

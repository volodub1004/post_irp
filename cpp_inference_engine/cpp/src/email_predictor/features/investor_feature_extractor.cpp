#include "email_predictor/features/investor_feature_extractor.hpp"
#include "email_predictor/features/name_feature_constants.hpp"
#include "string_normalization/normalize.hpp"

#include <algorithm>
#include <string_view>

namespace email_predictor::features {

InvestorFeatureExtractor::Flags
InvestorFeatureExtractor::extract(std::string_view full_name) {
  if (full_name.empty()) {
    return {}; // defensive
  }

  Flags flags;

  // Convert to lowercase once
  const std::string lower = string_normalization::to_lower(full_name);

  // Parse UTF-8 characters once
  const auto chars = parse_utf8_chars(lower);

  // Check for German characters
  flags.has_german_char = has_german_characters(chars);

  // Check if NFKD normalization alters the name
  flags.has_nfkd_normalized = would_nfkd_normalize(lower);

  // Check for nickname in first token
  const std::string first_token = extract_first_token(lower);
  if (!first_token.empty()) {
    flags.has_nickname = !find_nicknames(first_token).empty();
  }

  return flags;
}

bool InvestorFeatureExtractor::has_german_characters(
    const std::vector<std::string_view> &name_chars) noexcept {
  // Convert german chars and check difference
  for (const auto &ch : name_chars) {
    auto replaced = string_normalization::replace_german_chars(ch);
    if (replaced != ch) {
      return true; // found char
    }
  }

  return false;
}

bool InvestorFeatureExtractor::would_nfkd_normalize(
    std::string_view lower_name) {
  // NFKD normalize
  const std::string norm_ascii =
      string_normalization::nfkd_normalize(lower_name);
  return norm_ascii != lower_name;
}

std::string
InvestorFeatureExtractor::extract_first_token(std::string_view lower_name) {
  const size_t start = lower_name.find_first_not_of(' ');
  if (start == std::string::npos) {
    return {};
  }

  // Return first name
  const size_t end = lower_name.find(' ', start);
  return std::string(lower_name.substr(start, end - start));
}

std::vector<std::string_view>
InvestorFeatureExtractor::parse_utf8_chars(std::string_view s) {
  std::vector<std::string_view> result;
  result.reserve(s.size()); // Over-estimate, but avoids reallocations

  size_t i = 0;
  while (i < s.size()) {
    const unsigned char c = static_cast<unsigned char>(s[i]);
    size_t len = 1;

    // Determine UTF-8 character length
    if ((c & 0xE0) == 0xC0) {
      len = 2; // 2-byte UTF-8
    } else if ((c & 0xF0) == 0xE0) {
      len = 3; // 3-byte UTF-8
    } else if ((c & 0xF8) == 0xF0) {
      len = 4; // 4-byte UTF-8
    }

    // Ensure we don't go out of bounds
    if (i + len > s.size()) {
      len = s.size() - i;
    }

    result.emplace_back(s.substr(i, len));
    i += len;
  }

  return result;
}

} // namespace email_predictor::features

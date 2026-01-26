#include <algorithm>
#include <string>
#include <string_view>

// NFKD normalization stuff
#include <unicode/errorcode.h>
#include <unicode/normalizer2.h>
#include <unicode/unistr.h>

#include "email_predictor/features/name_feature_constants.hpp"

namespace string_normalization {

/**
 * @brief Replaces Germanic special characters in a UTF-8 string with their
 * ASCII equivalents.
 *
 * @param lower_name A UTF-8 encoded lower case input name (as std::string_view)
 * to normalize.
 * @return A std::string with all applicable replacements performed.
 */
inline std::string replace_german_chars(std::string_view lower_name) {
  std::string output;
  output.reserve(lower_name.size()); // Reserve to reduce allocations

  for (size_t i = 0; i < lower_name.size();) {
    bool matched = false;
    for (const auto &map : email_predictor::features::GERMAN_ASCII_MAPPINGS) {
      const auto &pattern = map.from;
      // Match multi byte patterns (UTF8 germanic chars are multibyte)
      if (i + pattern.size() <= lower_name.size() &&
          lower_name.substr(i, pattern.size()) == pattern) {
        output.append(map.to);
        i += pattern.size();
        matched = true;
        break;
      }
    }

    if (!matched) {
      output.push_back(lower_name[i++]);
    }
  }

  return output;
}

/**
 * @brief Strip non-ASCII characters from string.
 * @param input Input string
 * @return ASCII-only version
 *
 * @note CoPilot helper heavily with this, not as easy as it was with python.
 */
inline std::string strip_to_ascii(std::string_view input) {
  std::string result;
  result.reserve(input.size()); // Over-estimate

  for (char c : input) {
    if (static_cast<unsigned char>(c) < 128) {
      result += c;
    }
  }

  return result;
}

/**
 * @brief Normalizes a Unicode string using NFKD and converts it to ASCII for
 * consistent string comparison.
 *
 * @param lower_name Input string view to be normalized (typically already
 * lowercase)
 * @return std::string The normalized and ASCII-stripped result. Returns the
 * original string unchanged if normalization fails.
 *
 * @note CoPilot helper heavily with this, not as easy as it was with python.
 */
inline std::string nfkd_normalize(std::string_view lower_name) {
  icu::ErrorCode error;
  const icu::Normalizer2 *normalizer = icu::Normalizer2::getNFKDInstance(error);

  if (error.isFailure()) {
    return std::string(lower_name); // Assume no normalization
  }

  const icu::UnicodeString input =
      icu::UnicodeString::fromUTF8(std::string(lower_name));
  icu::UnicodeString normalized;
  normalizer->normalize(input, normalized, error);

  if (error.isFailure()) {
    return std::string(lower_name); // Shouldn't happen but for robustness
  }

  // Back to ascii for fair comparison, german character will trigger this flag
  std::string norm_utf8;
  normalized.toUTF8String(norm_utf8);
  const std::string norm_ascii = strip_to_ascii(norm_utf8);
  return norm_ascii;
}

/**
 * @brief Converts a string_view to a lowercase std::string using ASCII rules.
 *
 * @param input The input string_view to convert.
 * @return A new std::string containing the lowercase version of the input.
 */
inline std::string to_lower(std::string_view input) {
  std::string result;
  result.reserve(input.size());
  for (char c : input) {
    result.push_back(
        static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
  }
  return result;
}

} // namespace string_normalization

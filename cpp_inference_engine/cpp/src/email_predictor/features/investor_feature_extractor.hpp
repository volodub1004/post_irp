#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace email_predictor::features {

/**
 * @brief Provides semantic feature flags for investor names.
 *
 * Extracts boolean features such as presence of German characters,
 * NFKD normalization effects, and nickname matching.
 */
class InvestorFeatureExtractor {
public:
  /**
   * @brief Struct representing high-level semantic flags for a name.
   */
  struct Flags {
    bool has_german_char = false;
    bool has_nfkd_normalized = false;
    bool has_nickname = false;

    // Utility methods for easier usage
    constexpr bool any() const noexcept {
      return has_german_char || has_nfkd_normalized || has_nickname;
    }
  };

  /**
   * @brief Extracts semantic flags from a raw name string.
   * @param full_name Full raw name to analyze.
   * @return Struct with semantic feature flags.
   */
  static Flags extract(std::string_view full_name);

private:
  /**
   * @brief Check for German characters in the name.
   * @param name_chars UTF-8 character spans from the name.
   * @return True if German characters are found.
   */
  static bool has_german_characters(
      const std::vector<std::string_view> &name_chars) noexcept;

  /**
   * @brief Check if NFKD normalization would alter the name.
   * @param lower_name Lowercase version of the name.
   * @return True if normalization changes the string.
   *
   * @note CoPilot helper heavily with this, not as easy as it was with python.
   */
  static bool would_nfkd_normalize(std::string_view lower_name);

  /**
   * @brief Extract first token/name from the full name for nickname checking.
   * @param lower_name Lowercase version of the name
   * @return First token or empty string if none found
   */
  static std::string extract_first_token(std::string_view lower_name);

  /**
   * @brief Parse UTF-8 string into character spans.
   * @param s Input UTF-8 string
   * @return Vector for each UTF-8 character
   *
   * @note CoPilot helper heavily with this, not as easy as it was with python.
   */
  static std::vector<std::string_view> parse_utf8_chars(std::string_view s);
};

} // namespace email_predictor::features

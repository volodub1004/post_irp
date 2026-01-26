#pragma once

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace string_normalization {

/**
 * @class StringViewSplitter
 * @brief Lightweight string splitter for `std::string_view` using a
 * single-character delimiter.
 *
 * This utility allows step-by-step iteration over substrings in a delimited
 * string or one-shot retrieval as a vector. It avoids allocations unless
 * explicitly requested.
 */
class StringViewSplitter {
public:
  /**
   * @brief Constructs the splitter with an input view and delimiter.
   * @param str The input string view to split.
   * @param delimiter The delimiter character to split on (e.g., '_').
   */
  explicit StringViewSplitter(std::string_view str, char delimiter);

  /**
   * @brief Returns the next substring in the sequence.
   * @return Optional substring view. Returns `std::nullopt` when no more tokens
   * remain.
   */
  std::optional<std::string_view> next();

  /**
   * @brief Splits the entire string into substrings and returns as a vector of
   * views.
   * @return Vector of string views representing each token.
   *
   * @warning Returned views reference the original input string. Do not use
   *          them after the input string is destroyed.
   */
  std::vector<std::string_view> split_all() const;

  /**
   * @brief Splits the entire string and returns a vector of owning
   * `std::string` objects.
   * @return Vector of newly constructed strings for each token.
   *
   * Useful when you need to retain the parts beyond the lifetime of the
   * original string.
   */
  std::vector<std::string> split_all_strings() const;

private:
  std::string_view str_; ///< The original string view to split.
  char delimiter_;       ///< The delimiter character to split on.
  size_t pos_ = 0;       ///< Current offset in the input view.
};

} // namespace string_normalization

#include "string_normalization/splitter.hpp"

namespace string_normalization {

StringViewSplitter::StringViewSplitter(std::string_view str, char delimiter)
    : str_(str), delimiter_(delimiter) {}

std::optional<std::string_view> StringViewSplitter::next() {
  while (pos_ <= str_.size()) {
    size_t start = pos_;
    size_t end = str_.find(delimiter_, start); // Find first delimiter

    if (end == std::string_view::npos) {
      pos_ = str_.size() + 1; // Mark as done
      if (start < str_.size()) {
        auto segment = str_.substr(start); // Return rest of string
        if (!segment.empty())
          return segment;
      }
      return std::nullopt;
    } else {
      pos_ = end + 1;  // reset position
      if (end > start) // check for non empty substring
      {
        return str_.substr(start, end - start);
      }
    }
  }

  return std::nullopt;
}

std::vector<std::string_view> StringViewSplitter::split_all() const {
  std::vector<std::string_view> result;

  size_t start = 0;
  while (start < str_.size()) {
    // Skip leading delimiters
    while (start < str_.size() && str_[start] == delimiter_) {
      ++start;
    }

    // End of string
    if (start >= str_.size())
      break;

    size_t end = start;
    while (end < str_.size() && str_[end] != delimiter_) {
      ++end;
    }

    result.emplace_back(str_.substr(start, end - start));
    start = end;
  }

  return result;
}

std::vector<std::string> StringViewSplitter::split_all_strings() const {
  std::vector<std::string> result;
  for (const auto &sv : split_all()) {
    result.emplace_back(sv); // constructs string from string_view
  }
  return result;
}

} // namespace string_normalization

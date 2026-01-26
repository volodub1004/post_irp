#pragma once

#include <sstream>
#include <string>
#include <vector>

// Read from CSV helpers - names pulled from LP dataset and into CSV
// where they are parsed with nameparser to provide test comparisons
inline std::vector<std::string> split_csv_line(const std::string &line) {
  std::vector<std::string> fields;
  std::stringstream ss(line);
  std::string item;
  // Write lines to stream
  while (std::getline(ss, item, ',')) {
    // If we have an opening quote, read until the closing quote
    if (!item.empty() && item.front() == '"' && item.back() != '"') {
      std::string remainder;
      while (std::getline(ss, remainder, ',')) {
        item += ',' + remainder;
        if (!remainder.empty() && remainder.back() == '"')
          break;
      }
    }
    // Strip quotes if present
    if (!item.empty() && item.front() == '"' && item.back() == '"')
      item = item.substr(1, item.size() - 2);

    fields.push_back(item);
  }
  return fields;
}

inline std::string join(const std::vector<std::string> &vec) {
  // Merge vector to string
  std::ostringstream oss;
  for (size_t i = 0; i < vec.size(); ++i) {
    if (i > 0)
      oss << " ";
    oss << vec[i];
  }
  return oss.str();
}

inline std::string trim(const std::string &str) {
  // Trim CSV noise
  auto start = str.find_first_not_of(" \t\n\r");
  auto end = str.find_last_not_of(" \t\n\r");
  if (start == std::string::npos)
    return "";
  return str.substr(start, end - start + 1);
}

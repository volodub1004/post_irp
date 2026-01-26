#pragma once

#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <msgpack.hpp>
#include <string>
#include <unordered_map>
#include <vector>

#include "string_normalization/splitter.hpp"

namespace data_loaders {

/**
 * @brief Represents a parsed structural token from an email template.
 *
 * A template token encodes the relationship between a component of a name
 * (e.g., first name, middle name, last name) and its normalized form in the
 * email local-part. It also supports separator-only tokens (like ".", "_", "-")
 * via the `separator` field.
 */
struct TemplateToken {
  /**
   * @brief Enum for which part of the name the token refers to.
   */
  enum class Group : uint8_t {
    First,  ///< Full first name
    Middle, ///< Full middle name
    Last,   ///< Full last name
    Unknown ///< Unrecognized or not set
  } group = Group::Unknown;

  size_t index = 0; ///< Index into the name component vector

  bool use_original =
      false; ///< Use the original name string without transformation.
  bool use_nfkd = false;     ///< Apply Unicode NFKD normalization.
  bool use_translit = false; ///< Apply language-specific transliteration.
  bool use_nickname = false; ///< Substitute with a known nickname variant.
  bool use_surname_particle = false; ///< Use a joined surname with a particle.
  bool use_initial = false; ///< True when initial is used instead of fullname.

  /**
   * @brief Optional separator token (e.g., ".", "_", "-").
   *
   * If this is set, all other fields (group, index, flags) are ignored.
   */
  std::optional<std::string> separator;
};

/**
 * @brief Represents an email template candidate with structure and statistical
 * features.
 */
struct CandidateTemplate {
  int template_id;                      ///< Unique ID of the template.
  std::vector<TemplateToken> token_seq; ///< Ordered list of structural tokens
                                        ///< representing the email pattern.
  int support_count;   ///< Global usage count across all investors.
  float coverage_pct;  ///< Global percentage coverage of this template.
  bool in_mined_rules; ///< True if template was found in mined TRuleGrowth
                       ///< rules.
  float max_rule_confidence; ///< Highest rule confidence supporting this
                             ///< template.
  float
      avg_rule_confidence; ///< Average rule confidence across supporting rules.
  bool
      uses_middle_name; ///< Whether this template includes a middle name token.
  bool uses_multiple_firsts;  ///< True if supports multiple first names.
  bool uses_multiple_middles; ///< True if supports multiple middle names.
  bool uses_multiple_lasts;   ///< True if supports multiple last names.
};

/**
 * @brief Per firm statistics summarizing template usage patterns.
 */
struct FirmStats {
  int num_templates;     ///< Total number of unique templates used by the firm.
  int num_investors;     ///< Number of investors associated with the firm.
  float diversity_ratio; ///< Ratio of templates to investors.
  bool is_single_template;   ///< True if the firm uses only one template.
  bool is_shared_infra;      ///< True if firm uses shared email infrastructure.
  bool firm_is_multi_domain; ///< True if firm uses multiple domains.
};

/**
 * @brief Metadata about how a template is used within a specific firm.
 */
struct FirmTemplateUsage {
  int support_count;    ///< Raw count of uses in this firm.
  float coverage_pct;   ///< Share of total uses by firm.
  bool is_top_template; ///< True if this is the most-used template in firm.
};

/**
 * @brief Cached previous fuzzy matched firm names and associated domain.
 */
struct CacheEntry {
  std::string canonical_firm; ///< Fuzzy matched firm name.
  double match_score{};       ///< Fuzzy match score.
};

/**
 * @brief Loads a binary file into a heap allocated buffer.
 *
 * @param path Path to the binary file.
 * @param file_size Output parameter to store the file size in bytes.
 * @return Unique pointer to the allocated buffer.
 *
 * @throws std::runtime_error if the file cannot be opened or read.
 *
 * @note CoPilot helped guide through msgpack c usage.
 */
inline std::unique_ptr<char[]> read_binary_file(const std::string &path,
                                                size_t &file_size) {
  // Open file
  std::ifstream file(path, std::ios::binary | std::ios::ate);
  if (!file.is_open()) {
    throw std::runtime_error("Cannot open file: " + path);
  }

  // File empty
  file_size = static_cast<size_t>(file.tellg());
  if (file_size == 0) {
    throw std::runtime_error("File is empty: " + path);
  }

  // write to buffer
  file.seekg(0, std::ios::beg);
  auto buffer = std::make_unique<char[]>(file_size);
  if (!file.read(buffer.get(), static_cast<std::streamsize>(file_size))) {
    throw std::runtime_error("Failed to read file: " + path);
  }

  return buffer;
}

/**
 * @brief Extracts a typed value from a MessagePack object map with error
 * checking.
 *
 * @tparam T The expected type of the field.
 * @param row The key-value map parsed from MessagePack.
 * @param key The field name to extract.
 * @return The extracted value.
 *
 * @throws std::runtime_error if the key is not present.
 */
template <typename T>
inline T safe_extract(const std::map<std::string, msgpack::object> &row,
                      const char *key) {
  const auto it = row.find(key);
  if (it == row.end()) {
    throw std::runtime_error(std::string("Missing required field: ") + key);
  }
  // Templated to return value
  return it->second.as<T>();
}

/**
 * @brief Normalizes a given firm name into a manageable state for fuzzy
 * matching.
 *
 * @param firm_name View to firm name string.
 * @return Normalized firm name.
 */
inline std::string normalize_firm_name(std::string_view firm_name) {
  std::string normalized_name(firm_name);
  std::transform(
      normalized_name.begin(), normalized_name.end(), normalized_name.begin(),
      [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

  return normalized_name; // preserves spaces & punctuation, just lowercases
}

/**
 * @brief Converts a MessagePack canonical name map to std::unordered_map.
 *
 * @param path Path to msgpack file.
 * @param out_lookup The converted map.
 * @return True on success, false otherwise.
 *
 * @note CoPilot was used to help debug this function, specifically casting from
 * msgpack object to STL container.
 */
inline bool load_canonical_firm_msgpack(
    const std::string &path,
    std::unordered_map<std::string, std::string> &out_lookup) {
  try {
    out_lookup.clear();

    // Read file
    size_t sz = 0;
    auto rows_buf = read_binary_file(path, sz);

    // Unpacking zero copy for large file
    msgpack::object_handle oh = msgpack::unpack(rows_buf.get(), sz);

    std::map<std::string, msgpack::object> rows;
    oh.get().convert(rows);

    out_lookup.reserve(rows.size() + rows.size() / 3);

    // Parse each row and add it to the map
    for (const auto &[firm_raw, obj] : rows) {
      std::map<std::string, msgpack::object> meta;
      obj.convert(meta);

      // Extract domain
      auto it = meta.find("domain");
      if (it == meta.end() || it->second.is_nil()) {
        continue; // Defensive, shouldn't happen
      }

      // Convert domain
      std::string domain;
      it->second.convert(domain);

      // Normalize firm key and insert
      const std::string key = normalize_firm_name(firm_raw);
      out_lookup[key] = std::move(domain);
    }
    return true;
  } catch (const std::exception &e) {
    // Report error and return
    std::cerr << "load_canonical_firms_msgpack error: " << e.what() << "\n";
    out_lookup.clear();
    return false;
  }
}

/**
 * @brief Converts a MessagePack fuzzy firm cache map to std::unordered_map.
 *
 * @param path Path to msgpack file.
 * @param out_cache The converted map.
 * @return True on success, false otherwise.
 *
 * @note CoPilot was used to help debug this function, specifically casting from
 * msgpack object to STL container.
 */
inline bool load_firm_cache_msgpack(
    const std::string &path,
    std::unordered_map<std::string, std::pair<std::string, CacheEntry>>
        &out_cache) {
  try {
    out_cache.clear();

    // Read file
    size_t sz = 0;
    auto rows_buf = read_binary_file(path, sz);

    // Unpacking zero copy for large file
    msgpack::object_handle oh = msgpack::unpack(rows_buf.get(), sz);

    std::map<std::string, msgpack::object> top;
    oh.get().convert(top);

    out_cache.reserve(top.size() + top.size() / 3);

    for (const auto &[raw_firm_key, value_obj] : top) {
      // Convert to map
      std::unordered_map<std::string, msgpack::object> rec;
      value_obj.convert(rec);

      // Lambda helpers
      auto get_str = [&](std::string_view k) -> std::string {
        auto it = rec.find(std::string(k));
        if (it == rec.end() || it->second.is_nil())
          return {};
        return it->second.as<std::string>();
      };
      auto get_double = [&](std::string_view k) -> double {
        auto it = rec.find(std::string(k));
        if (it == rec.end() || it->second.is_nil())
          return 0.0;
        return it->second.as<double>();
      };

      std::string domain = get_str("domain");
      std::string canonical_firm = get_str("canonical_firm");
      double match_score = get_double("match_score");

      if (domain.empty() || canonical_firm.empty())
        continue; // Defensive

      CacheEntry ce;
      ce.canonical_firm = normalize_firm_name(canonical_firm);
      ce.match_score = match_score;

      const std::string key = normalize_firm_name(raw_firm_key);
      // Last-write-wins if duplicates exist - needs to be mitigated in msgpack
      // generate script if proves an issue
      out_cache[key] = {std::move(domain), std::move(ce)};
    }
    return true;
  } catch (const std::exception &e) {
    // Report error and return
    std::cerr << "load_firm_match_cache_msgpack error: " << e.what() << "\n";
    out_cache.clear();
    return false;
  }
}

/**
 * @brief Converts a MessagePack-parsed row into a CandidateTemplate object.
 *
 * @param row The input map parsed from MessagePack.
 * @return Parsed CandidateTemplate.
 */
inline CandidateTemplate
parse_candidate_template(const std::map<std::string, msgpack::object> &row) {
  CandidateTemplate ct;
  ct.template_id = safe_extract<int>(row, "template_id");
  ct.support_count = safe_extract<int>(row, "support_count");
  ct.coverage_pct = safe_extract<float>(row, "coverage_pct");
  ct.in_mined_rules = safe_extract<bool>(row, "in_mined_rules");
  ct.max_rule_confidence = safe_extract<float>(row, "max_rule_confidence");
  ct.avg_rule_confidence = safe_extract<float>(row, "avg_rule_confidence");
  ct.uses_middle_name = safe_extract<bool>(row, "uses_middle_name");
  ct.uses_multiple_firsts = safe_extract<bool>(row, "uses_multiple_firsts");
  ct.uses_multiple_middles = safe_extract<bool>(row, "uses_multiple_middles");
  ct.uses_multiple_lasts = safe_extract<bool>(row, "uses_multiple_lasts");
  return ct;
}

/**
 * @brief Converts a MessagePack-parsed firm metadata row into a FirmStats
 * object.
 *
 * @param fields The parsed key-value map.
 * @return Parsed FirmStats.
 */
inline FirmStats
parse_firm_stats(const std::map<std::string, msgpack::object> &fields) {
  return {safe_extract<int>(fields, "num_templates"),
          safe_extract<int>(fields, "num_investors"),
          safe_extract<float>(fields, "diversity_ratio"),
          safe_extract<bool>(fields, "is_single_template"),
          safe_extract<bool>(fields, "is_shared_infra"),
          safe_extract<bool>(fields, "firm_is_multi_domain")};
}

/**
 * @brief Parses a vector of email template tokens into structured TemplateToken
 * objects.
 *
 * This function interprets tokens representing parts of email local parts such
 * as "f_0", "last_original_0", or separators like "."—and constructs a vector
 * of TemplateToken structs with the appropriate fields populated.
 *
 * If the token is a single-character separator (`.`, `_`, `-`), all structural
 * flags are false and only the `separator` field is populated.
 *
 * @param tokens Vector of template token strings to parse.
 * @return Vector of TemplateToken objects corresponding to the parsed input
 * tokens.
 *
 * @throws std::runtime_error If a token is malformed, contains an unrecognized
 * group or flag, or has an invalid index.
 */
inline std::vector<TemplateToken>
parse_token_sequence(const std::vector<std::string> &tokens) {
  std::vector<TemplateToken> parsed;
  parsed.reserve(tokens.size());

  for (const auto &token : tokens) {
    TemplateToken t;

    // Fast separator check
    if (token.size() == 1 &&
        (token[0] == '.' || token[0] == '-' || token[0] == '_')) {
      t.separator = token;
      parsed.push_back(std::move(t));
      continue;
    }

    // Splitter to collect parts
    std::vector<std::string_view> parts;
    parts.reserve(4); // Most tokens have 2-4 parts

    string_normalization::StringViewSplitter splitter(token, '_');
    while (auto part = splitter.next()) {
      parts.push_back(*part);
    }

    if (parts.size() < 2) {
      throw std::runtime_error("Invalid template token format: " + token);
    }

    // Parse index last part
    const auto &index_part = parts.back();
    if (index_part.empty()) {
      throw std::runtime_error("Invalid template token format: " + token);
    }

    size_t index_val = 0;
    for (char c : index_part) {
      // Parse potentially multi digit index (unlikely but for robustness)
      if (c < '0' || c > '9') {
        throw std::runtime_error("Invalid template token format: " + token);
      }
      index_val = index_val * 10 +
                  static_cast<size_t>(c - '0'); // convert and accumulate
    }
    t.index = index_val;

    // Parse group
    const auto &group_str = parts[0];
    switch (group_str.length()) {
    case 1: // initial case
      switch (group_str[0]) {
      case 'f':
        t.group = TemplateToken::Group::First;
        t.use_initial = true;
        break;
      case 'm':
        t.group = TemplateToken::Group::Middle;
        t.use_initial = true;
        break;
      case 'l':
        t.group = TemplateToken::Group::Last;
        t.use_initial = true;
        break;
      default:
        throw std::runtime_error("Invalid group in token: " +
                                 std::string(group_str));
      }
      break;
    case 4: // "last"
      if (group_str == "last")
        t.group = TemplateToken::Group::Last;
      else
        throw std::runtime_error("Invalid group in token: " +
                                 std::string(group_str));
      break;
    case 5: // "first"
      if (group_str == "first")
        t.group = TemplateToken::Group::First;
      else
        throw std::runtime_error("Invalid group in token: " +
                                 std::string(group_str));
      break;
    case 6: // "middle"
      if (group_str == "middle")
        t.group = TemplateToken::Group::Middle;
      else
        throw std::runtime_error("Invalid group in token: " +
                                 std::string(group_str));
      break;
    default:
      throw std::runtime_error("Invalid group in token: " +
                               std::string(group_str));
    }

    // Parse flags
    for (std::size_t i = 1; i < parts.size() - 1; ++i) {
      const auto &flag = parts[i];
      if (flag.empty())
        continue;

      switch (flag[0]) {
      case 'o': // "original"
        if (flag == "original")
          t.use_original = true;
        else
          throw std::runtime_error("Unknown normalization flag in token: " +
                                   std::string(flag));
        break;
      case 'n': // "nfkd" or "nickname"
        if (flag == "nfkd")
          t.use_nfkd = true;
        else if (flag == "nickname")
          t.use_nickname = true;
        else
          throw std::runtime_error("Unknown normalization flag in token: " +
                                   std::string(flag));
        break;
      case 't': // "translit"
        if (flag == "translit")
          t.use_translit = true;
        else
          throw std::runtime_error("Unknown normalization flag in token: " +
                                   std::string(flag));
        break;
      case 's': // "surp"
        if (flag == "surp")
          t.use_surname_particle = true;
        else
          throw std::runtime_error("Unknown normalization flag in token: " +
                                   std::string(flag));
        break;
      default:
        throw std::runtime_error("Unknown normalization flag in token: " +
                                 std::string(flag));
      }
    }

    parsed.push_back(std::move(t));
  }

  return parsed;
}

/**
 * @brief Loads candidate email templates from a MessagePack file into a map.
 *
 * The parsed templates are stored in an output map indexed by their
 * `template_id`, with the token sequences converted from string representations
 * into structured `TemplateToken` objects.
 *
 * @param candidate_templates_path Path to the `.msgpack` file containing
 * candidate templates.
 * @param out_templates Output vector to populate with parsed templates.
 */
inline void
load_candidate_templates(const std::string &candidate_templates_path,
                         std::vector<CandidateTemplate> &out_templates) {
  size_t ct_size;
  auto ct_buf = read_binary_file(candidate_templates_path, ct_size);
  std::cout << " (" << (ct_size / 1024 / 1024) << "MB)" << std::endl;

  // Unpacking zero copy for large file
  msgpack::object_handle ct_oh = msgpack::unpack(ct_buf.get(), ct_size);

  std::vector<std::map<std::string, msgpack::object>> ct_list;
  ct_oh.get().convert(ct_list);

  // Reserve space - expecting at most 358 templates
  out_templates.reserve(ct_list.size());
  std::cout << "Processing " << ct_list.size() << " candidate templates"
            << std::endl;

  for (const auto &row : ct_list) {
    auto ct = parse_candidate_template(row);

    // Parse token sequence
    auto token_seq = safe_extract<std::vector<std::string>>(row, "template");
    ct.token_seq = std::move(parse_token_sequence(token_seq));

    out_templates.emplace_back(std::move(ct));
  }

  // Sort for deterministic matrix building
  std::sort(out_templates.begin(), out_templates.end(),
            [](const CandidateTemplate &a, const CandidateTemplate &b) {
              return a.template_id < b.template_id;
            });
}

/**
 * @brief Loads template data and firm-template mappings from two MessagePack
 * files.
 *
 * @param std_candidate_templates_path Path to the
 * `std_candidate_templates.msgpack` file.
 * @param complex_candidate_templates_path Path to the
 * `complex_candidate_templates.msgpack` file.
 * @param firm_template_map_path Path to the `firm_template_map.msgpack` file.
 * @param std_out_templates Output vector of pairs: template ID,
 * CandidateTemplate - for standard names.
 * @param complex_out_templates Output vector of pairs: template ID,
 * CandidateTemplate.
 * @param out_firm_stats_map Output map: firm name -> FirmStats.
 * @return True if data loaded successfully; false otherwise.
 *
 * @throws std::runtime_error on format or I/O errors.
 *
 * @note CoPilot was used to help debug this function, specifically casting from
 * msgpack object to STL container.
 */
inline bool load_template_data(
    const std::string &std_candidate_templates_path,
    const std::string &complex_candidate_templates_path,
    const std::string &firm_template_map_path,
    std::vector<CandidateTemplate> &std_out_templates,
    std::vector<CandidateTemplate> &complex_out_templates,
    std::unordered_map<std::string, FirmStats> &out_firm_stats_map,
    std::unordered_map<std::string, std::unordered_map<int, FirmTemplateUsage>>
        &out_firm_template_usage_map) {
  try {
    // Clear output containers
    std_out_templates.clear();
    complex_out_templates.clear();
    out_firm_stats_map.clear();
    out_firm_template_usage_map.clear();

    std::cout << "Loading template data from large msgpack files..."
              << std::endl;

    // Load candidate_templates
    std::cout << "Loading candidate templates..." << std::flush;
    load_candidate_templates(std_candidate_templates_path, std_out_templates);
    load_candidate_templates(complex_candidate_templates_path,
                             complex_out_templates);

    // Load firm_template_map
    {
      std::cout << "Loading firm template map" << std::flush;
      size_t ft_size;
      auto ft_buf = read_binary_file(firm_template_map_path, ft_size);
      std::cout << " (" << (ft_size / 1024 / 1024) << "MB)" << std::endl;

      msgpack::object_handle ft_oh = msgpack::unpack(ft_buf.get(), ft_size);

      std::map<std::string, std::map<std::string, msgpack::object>> firm_map;
      ft_oh.get().convert(firm_map);

      // Pre-size for 50k firms with optimal load factor
      const size_t firm_count = firm_map.size();
      out_firm_stats_map.reserve(firm_count + firm_count / 3);
      out_firm_template_usage_map.reserve(firm_count + firm_count / 3);

      std::cout << "Processing " << firm_count << " firms" << std::endl;
      for (const auto &[firm, fields] : firm_map) {
        // Parse and store firm stats
        out_firm_stats_map.emplace(firm, parse_firm_stats(fields));

        // Extract template_ids
        const auto template_ids =
            safe_extract<std::vector<int>>(fields, "template_ids");

        // Graceful exit on empty list
        if (template_ids.empty()) {
          out_firm_template_usage_map[firm] = {};
          continue;
        }

        // Count occurrences and find max in single pass
        std::unordered_map<int, int> support_counts;
        support_counts.reserve(template_ids.size() /
                               2); // Estimate for fewer collisions

        int max_support = 0;
        for (int tid : template_ids) {
          int &count = support_counts[tid];
          ++count;
          max_support = std::max(max_support, count);
        }

        const int total_templates_used = static_cast<int>(template_ids.size());
        const auto unique_templates = support_counts.size();
        const float total_inv =
            1.0f /
            static_cast<float>(total_templates_used); // Pre-compute reciprocal

        // Fill firm usage map
        auto &usage_map = out_firm_template_usage_map[firm];
        usage_map.reserve(unique_templates);

        for (const auto &[tid, count] : support_counts) {
          usage_map.emplace(
              tid,
              FirmTemplateUsage{count,
                                static_cast<float>(count) *
                                    total_inv, // Multiply instead of divide
                                count == max_support});
        }
      }

    } // ft_buf goes out of scope here, freeing memory

    std::cout << "Template data loading complete!" << std::endl;
    std::cout << "Std templates: " << std_out_templates.size() << std::endl;
    std::cout << "Complex templates: " << complex_out_templates.size()
              << std::endl;
    std::cout << "Firms: " << out_firm_stats_map.size() << std::endl;

    return true;
  } catch (const std::exception &ex) {
    std::cerr << "Error loading template data: " << ex.what() << std::endl;

    // Clear containers on error to ensure clean state
    std_out_templates.clear();
    complex_out_templates.clear();
    out_firm_stats_map.clear();

    return false;
  }
}

} // namespace data_loaders

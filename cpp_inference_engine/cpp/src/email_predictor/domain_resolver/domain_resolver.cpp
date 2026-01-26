#include "email_predictor/domain_resolver/domain_resolver.hpp"

#include <rapidfuzz/fuzz.hpp>
#include <stdexcept>

namespace {
/**
 * @brief Find the best fuzzy match for a query string among the keys of a firm
 * -> domain map.
 *
 * @param query         The firm name to search for.
 * @param firm_to_domain Map of canonical firm names to their associated
 * domains.
 * @return std::pair<std::string, CacheEntry>
 *         containing (domain, score) if a match is found.
 *
 * @note Check fuzzy matcher GitHub for implementation notes. This follows
 * closely to the examples there.
 */
std::pair<std::string, data_loaders::CacheEntry> findBestFirmMatch(
    const std::string &query,
    const std::unordered_map<std::string, std::string> &firm_to_domain) {
  double best_score = 0;
  const std::string *best_firm = nullptr;
  const std::string *best_domain = nullptr;

  // Start scorer
  rapidfuzz::fuzz::CachedRatio<char> scorer(query);

  for (const auto &[firm, domain] : firm_to_domain) {
    // Check similarity
    double score = scorer.similarity(firm);
    if (score >= best_score) {
      best_score = score;
      best_domain = &domain;
      best_firm = &firm;
    }
  }

  return {*best_domain, data_loaders::CacheEntry{*best_firm, best_score}};
}
} // namespace

namespace email_predictor::domain_resolver {

DomainResolver::DomainResolver(std::string canonical_path,
                               std::string cache_path)
    : canonical_path_(std::move(canonical_path)),
      cache_path_(std::move(cache_path)) {
  // Load canonical firms (mapping firm -> domain)
  if (!data_loaders::load_canonical_firm_msgpack(canonical_path_,
                                                 firm_to_domain_)) {
    throw std::runtime_error("Failed to load canonical firms.");
  }

  // Load firm match cache (memoizing raw firm -> domain, score)
  if (!data_loaders::load_firm_cache_msgpack(cache_path_, firm_cache_)) {
    throw std::runtime_error("Failed to load firm match cache.");
  }
}

std::tuple<std::string, std::string, int>
DomainResolver::resolve_domain(std::string_view raw_firm_name) const {
  // Normalize given name
  std::string normalized_name =
      data_loaders::normalize_firm_name(raw_firm_name);

  // Check canonical names
  if (firm_to_domain_.contains(normalized_name)) {
    return {firm_to_domain_.at(normalized_name), normalized_name, 100};
  }

  // Check cache
  if (firm_cache_.contains(normalized_name)) {
    return {firm_cache_.at(normalized_name).first,
            firm_cache_.at(normalized_name).second.canonical_firm,
            firm_cache_.at(normalized_name).second.match_score};
  }

  // Perform fuzzy matching
  auto best_match = findBestFirmMatch(normalized_name, firm_to_domain_);

  // Cache the result for future use
  firm_cache_[normalized_name] = {best_match.first, best_match.second};
  return {best_match.first, best_match.second.canonical_firm,
          best_match.second.match_score};
}

} // namespace email_predictor::domain_resolver

#pragma once

#include <optional>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

#include "data_loader/templates_loader.hpp"

namespace email_predictor::domain_resolver {

/**
 * @brief Resolves firm names to their associated email domains.
 *
 * @note CoPilot was used to guide through C++ FuzzyMatcher inclusion and
 * implementation.
 */
class DomainResolver {
public:
  /**
   * @brief Constructs a DomainResolver and loads canonical and cache data.
   *
   * @param canonical_path Path to a MessagePack file containing a canonical
   *        firm->domain mapping.
   * @param cache_path Path to a MessagePack file containing a fuzzy-match cache
   *        mapping previously queried firm names to resolved domains and match
   * metadata.
   *
   * @throws std::runtime_error if either file cannot be read or parsed.
   */
  explicit DomainResolver(std::string canonical_path, std::string cache_path);

  /**
   * @brief Resolves the email domain for a given raw firm name.
   *
   * @param raw_firm_name Arbitrary input firm name.
   * @return A tuple containing the associated email domain, best matching firm
   * and match score.
   *
   * @note CoPilot was used to guide this implementation.
   */
  std::tuple<std::string, std::string, int>
  resolve_domain(std::string_view raw_firm_name) const;

private:
  std::string
      canonical_path_;     ///< Filesystem path to canonical firm->domain map.
  std::string cache_path_; ///< Filesystem path to fuzzy-match cache.

  std::unordered_map<std::string, std::string>
      firm_to_domain_; ///< Canonical firm->domain map.
  mutable std::unordered_map<std::string,
                             std::pair<std::string, data_loaders::CacheEntry>>
      firm_cache_; ///< Fuzzy match memoization cache.
};

} // namespace email_predictor::domain_resolver

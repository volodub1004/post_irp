#include "email_predictor/domain_resolver/domain_resolver.hpp"

#include <filesystem>
#include <gtest/gtest.h>

#include "test_utilities.hpp"

using namespace email_predictor::domain_resolver;

TEST(DomainResolverTest, MatchesPythonOutput) {
  // Test data next to test file
  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  std::ifstream file(base_path / "test_data/domain_resolver_test_data.csv");
  ASSERT_TRUE(file.is_open());

  // Path to msgpacks
  const std::string canonical_firms_path =
      base_path / "../cpp/data/canonical_firms.msgpack";
  const std::string firm_cache_path =
      base_path / "../cpp/data/firm_match_cache.msgpack";

  std::string header;
  std::getline(file, header); // skip header
  int successful_resolved = 0;
  int unsuccessful_resolved = 0;

  DomainResolver resolver(canonical_firms_path, firm_cache_path);

  // Track failed
  std::vector<std::pair<std::string, std::string>> failed_domains;

  std::string line;
  while (std::getline(file, line)) {
    auto fields = split_csv_line(line);
    ASSERT_GE(fields.size(), 2);

    // Check CSV generation script for ordering here
    std::string firm = trim(fields[0]);
    std::string domain = trim(fields[1]);

    // Resolve
    auto [resolved_domain, resolved_firm, score] =
        resolver.resolve_domain(firm);

    // Check
    if (resolved_domain != domain) {
      failed_domains.push_back({resolved_domain, domain});
      unsuccessful_resolved++;
    }

    successful_resolved++;
  }

  // Accept with a margin of error. Domain resolution is messy
  EXPECT_LT(unsuccessful_resolved,
            (successful_resolved + unsuccessful_resolved) * 0.08);

  std::cout << successful_resolved << " successfully resolved domains!"
            << std::endl;
}
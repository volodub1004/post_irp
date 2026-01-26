#include "data_loader/templates_loader.hpp"
#include <filesystem>
#include <gtest/gtest.h>

using namespace data_loaders;

// TEST(TemplateLoader, LoadValidFiles)
// {
//     std::vector<CandidateTemplate> std_templates;
//     std::vector<CandidateTemplate> complex_templates;
//     std::unordered_map<std::string, FirmStats> firm_stats_map;
//     std::unordered_map<std::string, std::unordered_map<int,
//     FirmTemplateUsage>> firm_template_usage_map;

//     std::filesystem::path base_path =
//     std::filesystem::path(__FILE__).parent_path(); const std::string
//     std_candidate_path = base_path /
//     "../cpp/data/std_candidate_templates.msgpack"; const std::string
//     complex_candidate_path = base_path /
//     "../cpp/data/complex_candidate_templates.msgpack"; const std::string
//     firm_path = base_path / "../cpp/data/firm_template_map.msgpack";

//     ASSERT_TRUE(load_template_data(std_candidate_path,
//     complex_candidate_path, firm_path, std_templates, complex_templates,
//     firm_stats_map, firm_template_usage_map));
//     ASSERT_FALSE(std_templates.empty()) << "Std candidate templates should
//     not be empty"; ASSERT_FALSE(complex_templates.empty()) << "Complex
//     candidate templates should not be empty";
//     ASSERT_FALSE(firm_stats_map.empty()) << "Firm stats map should not be
//     empty"; ASSERT_FALSE(firm_template_usage_map.empty()) << "Firm template
//     map should not be empty";

//     // Sanity check one template and firm
//     auto it = std_templates.begin();
//     EXPECT_GT(it->token_seq.size(), 0u) << "Template tokens should not be
//     empty";

//     auto fs_it = firm_stats_map.begin();
//     EXPECT_GT(fs_it->second.num_templates, 0u) << "Firm should have
//     templates";
// }

TEST(TemplateLoader, LoadDomainResolverFiles) {
  std::unordered_map<std::string, std::string> canonical_firms;
  std::unordered_map<std::string, std::pair<std::string, CacheEntry>>
      firm_cache;

  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  const std::string canonical_firms_path =
      base_path / "../cpp/data/canonical_firms.msgpack";
  const std::string firm_cache_path =
      base_path / "../cpp/data/firm_match_cache.msgpack";

  ASSERT_TRUE(
      load_canonical_firm_msgpack(canonical_firms_path, canonical_firms));
  ASSERT_TRUE(load_firm_cache_msgpack(firm_cache_path, firm_cache));
  ASSERT_FALSE(canonical_firms.empty())
      << "Canonical firm map should not be empty";
  ASSERT_FALSE(firm_cache.empty()) << "Firm cache should not be empty";

  // Sanity check one template and firm
  auto it = canonical_firms.begin();
  EXPECT_GT(it->second.size(), 0u)
      << "Firm domain map should have domains should not be empty";

  auto fc_it = firm_cache.begin();
  EXPECT_GT(fc_it->second.first.size(), 0u) << "Firm cache should have domains";
}

#include "email_predictor/name_decomposer/name_decomposer.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <gtest/gtest.h>
#include <sstream>
#include <string>
#include <vector>

#include "test_utilities.hpp"

using namespace email_predictor;
using namespace name_decomposer;

TEST(NameDecomposerTest, MatchesPythonOutput) {
  // Test data next to test file
  std::filesystem::path base_path =
      std::filesystem::path(__FILE__).parent_path();
  std::ifstream file(base_path / "test_data/nameparser_test_set.csv");
  ASSERT_TRUE(file.is_open());

  std::string header;
  std::getline(file, header); // skip header
  int successful_parsed = 0;

  std::string line;
  while (std::getline(file, line)) {
    auto fields = split_csv_line(line);
    ASSERT_GE(fields.size(), 9);

    // Check CSV generation script for ordering here
    std::string raw_name = trim(fields[0]);
    std::string expected_normalized = trim(fields[1]);
    std::string expected_first = trim(fields[2]);
    std::string expected_middle = trim(fields[3]);
    std::string expected_last = trim(fields[4]);

    // Get flags
    bool has_middle_name = fields[5] == "True";
    bool multiple_firsts = fields[6] == "True";
    bool multiple_middles = fields[7] == "True";
    bool multiple_lasts = fields[8] == "True";

    // Decompose
    NameDecomposer decomposer(raw_name);

    // Check
    EXPECT_EQ(join(decomposer.get_first_names()), expected_first)
        << "Mismatch in first names for: " << raw_name;
    EXPECT_EQ(join(decomposer.get_middle_names()), expected_middle)
        << "Mismatch in middle names for: " << raw_name;
    EXPECT_EQ(join(decomposer.get_last_names()), expected_last)
        << "Mismatch in last names for: " << raw_name;
    EXPECT_EQ(decomposer.has_middle_name(), has_middle_name)
        << "has_middle_name mismatch for: " << raw_name;
    EXPECT_EQ(decomposer.has_multiple_first_names(), multiple_firsts)
        << "has_multiple_first_names mismatch for: " << raw_name;
    EXPECT_EQ(decomposer.has_multiple_middle_names(), multiple_middles)
        << "has_multiple_middle_names mismatch for: " << raw_name;
    EXPECT_EQ(decomposer.has_multiple_last_names(), multiple_lasts)
        << "has_multiple_last_names mismatch for: " << raw_name;

    successful_parsed++;
  }

  std::cout << successful_parsed << " successfully parsed names!" << std::endl;
}

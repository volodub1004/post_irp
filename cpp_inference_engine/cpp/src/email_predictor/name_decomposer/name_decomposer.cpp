#include <algorithm>
#include <cctype>
#include <locale>
#include <ranges>
#include <regex>
#include <sstream>
#include <string_view>

#include "email_predictor/name_decomposer/name_decomposer.hpp"
#include "string_normalization/normalize.hpp"
#include "string_normalization/splitter.hpp"

namespace email_predictor::name_decomposer
{

    //  Compile time constants for string cleaning
    constexpr std::string_view WHITESPACE = " \t\n\r";
    constexpr std::string_view PASTE_NOISE = "\"'<>";

    // Compile time arrays for faster lookups than unordered_set
    constexpr std::array REMOVABLE_TOKENS = {"jr", "sr", "ii", "iii", "iv",
                                             "v", "phd", "md", "esq", "dr",
                                             "mr", "mrs", "ms", "prof", "sir"};

    constexpr std::array SURNAME_PARTICLES = {
        "santa", "san", "st", "von", "van", "de", "der", "dello", "vander",
        "del", "de la", "vom", "dela", "de los", "dos", "la", "los", "le",
        "du", "di", "da", "mac", "al", "abu", "bin", "ibn", "della"};

    namespace
    {
        // Helper function to check if token is in array
        template <std::size_t N>
        constexpr bool contains(const std::array<const char *, N> &arr,
                                std::string_view token)
        {
            return std::ranges::any_of(
                arr, [token](const char *item)
                { return token == item; });
        }

        // String trimming
        std::string_view trim(std::string_view str) noexcept
        {
            const auto start = str.find_first_not_of(WHITESPACE);
            if (start == std::string_view::npos)
                return {};

            const auto end = str.find_last_not_of(WHITESPACE);
            return str.substr(start, end - start + 1);
        }

        // Remove tokens from container
        template <typename Container>
        void remove_tokens(Container &tokens, const auto &removable_tokens)
        {
            // Remove from front
            while (!tokens.empty() && contains(removable_tokens, tokens.front()))
            {
                tokens.erase(tokens.begin());
            }

            // Remove from back
            while (!tokens.empty() && contains(removable_tokens, tokens.back()))
            {
                tokens.pop_back();
            }
        }
    } // namespace

    NameDecomposer::NameDecomposer(std::string_view full_name)
        : cleaned_full_name_(normalize_full_name(full_name))
    {
        // Parse immediately
        parse_name();
    }

    std::string NameDecomposer::normalize_full_name(std::string_view raw_input)
    {
        if (raw_input.empty())
            return {};

        // Trim and convert to string
        auto trimmed = trim(raw_input);
        if (trimmed.empty())
            return {};

        std::string result{trimmed};

        // Convert to lowercase
        result = string_normalization::to_lower(result);

        // Translit
        result = string_normalization::replace_german_chars(result);

        // NFKD
        result = string_normalization::nfkd_normalize(result);

        // Remove trailing punctuation
        while (!result.empty() && std::string_view(".,;:!?}]").find(result.back()) !=
                                      std::string_view::npos)
        {
            result.pop_back();
        }

        // Remove paste noise characters
        result.erase(std::remove_if(result.begin(), result.end(),
                                    [](char c)
                                    {
                                        return PASTE_NOISE.find(c) !=
                                               std::string_view::npos;
                                    }),
                     result.end());

        // Collapse multiple spaces
        result = std::regex_replace(result, std::regex(R"(\s{2,})"), " ");

        // Split into tokens and remove unwanted prefixes/suffixes
        string_normalization::StringViewSplitter splitter(result, ' ');
        auto tokens = splitter.split_all_strings();
        remove_tokens(tokens, REMOVABLE_TOKENS);

        if (tokens.empty())
            return {};

        // Join back
        std::string normalized;
        normalized.reserve(result.size()); // Reserve original size

        for (size_t i = 0; i < tokens.size(); ++i)
        {
            if (i > 0)
                normalized += ' ';
            normalized += tokens[i];
        }

        return normalized;
    }

    void NameDecomposer::parse_name()
    {
        // Invalid string or empty strings
        if (cleaned_full_name_.empty())
        {
            return;
        }

        string_normalization::StringViewSplitter splitter(cleaned_full_name_, ' ');
        auto parts = splitter.split_all_strings();
        if (parts.empty())
            return;

        const size_t n = parts.size();

        // Reserve minimum required space for vectors
        first_names_.reserve(2);
        middle_names_.reserve(n > 2 ? n - 2 : 0);
        last_names_.reserve(3);

        // Handle first name
        if (parts[0].find('-') != std::string::npos)
        {
            // Split hyphenated first name
            auto hyphenated_parts = parts[0] | std::views::split('-');
            for (auto &&part : hyphenated_parts)
            {
                if (!part.empty())
                {
                    first_names_.emplace_back(part.begin(), part.end());
                }
            }
        }
        else
        {
            first_names_.emplace_back(std::move(parts[0]));
        }

        // Process remaining parts
        for (size_t i = 1; i < n; ++i)
        {
            // If particle found move to last_names_ and break
            if (contains(SURNAME_PARTICLES, parts[i]))
            {
                // Move all remaining parts to last_names_
                last_names_.reserve(n - i);
                std::move(parts.begin() +
                              static_cast<std::vector<std::string>::difference_type>(i),
                          parts.end(), std::back_inserter(last_names_));
                break;
            }

            // Middle names captured in between first and last
            if (i < n - 1)
            {
                middle_names_.emplace_back(std::move(parts[i]));
            }
            else
            {
                // Last token becomes last name
                last_names_.emplace_back(std::move(parts[i]));
            }
        }
    }

    const std::vector<std::string> &
    NameDecomposer::get_first_names() const noexcept
    {
        return first_names_;
    }

    const std::vector<std::string> &
    NameDecomposer::get_middle_names() const noexcept
    {
        return middle_names_;
    }

    const std::vector<std::string> &
    NameDecomposer::get_last_names() const noexcept
    {
        return last_names_;
    }

    bool NameDecomposer::has_middle_name() const noexcept
    {
        return !middle_names_.empty();
    }

    bool NameDecomposer::has_multiple_first_names() const noexcept
    {
        return first_names_.size() > 1;
    }

    bool NameDecomposer::has_multiple_middle_names() const noexcept
    {
        return middle_names_.size() > 1;
    }

    bool NameDecomposer::has_multiple_last_names() const noexcept
    {
        return last_names_.size() > 1;
    }

} // namespace email_predictor::name_decomposer

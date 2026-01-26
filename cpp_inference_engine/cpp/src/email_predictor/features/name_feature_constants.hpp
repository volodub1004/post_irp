#pragma once

#include <array>
#include <span>
#include <string_view>
#include <unordered_map>
#include <unordered_set>

namespace email_predictor::features {

/**
 * @brief German-specific character mappings for ASCII normalization.
 * Used in NFKD normalization and string preprocessing.
 */
struct GermanMapping {
  std::string_view from;
  std::string_view to;
};

// std::array for quick lookups
inline constexpr std::array<GermanMapping, 6> GERMAN_ASCII_MAPPINGS = {
    {{"ü", "ue"},
     {"ö", "oe"},
     {"ä", "ae"},
     {"ß", "ss"},
     {"ø", "o"},
     {"å", "aa"}}};

/**
 * @brief Nickname mappings with better structure for bidirectional lookup.
 */
struct NicknameEntry {
  std::string_view formal_name;
  std::span<const std::string_view> nicknames;
};

// Nickname data - Pulled from training pipeline
namespace detail {
inline constexpr std::array<std::string_view, 1> alexander_nicknames = {"alex"};
inline constexpr std::array<std::string_view, 1> andrew_nicknames = {"andy"};
inline constexpr std::array<std::string_view, 2> anne_nicknames = {"annie",
                                                                   "nancy"};
inline constexpr std::array<std::string_view, 1> arthur_nicknames = {"art"};
inline constexpr std::array<std::string_view, 1> benjamin_nicknames = {"ben"};
inline constexpr std::array<std::string_view, 2> william_nicknames = {"bill",
                                                                      "will"};
inline constexpr std::array<std::string_view, 3> robert_nicknames = {
    "bob", "bobby", "rob"};
inline constexpr std::array<std::string_view, 1> catherine_nicknames = {
    "cathy"};
inline constexpr std::array<std::string_view, 2> charles_nicknames = {"charlie",
                                                                      "chuck"};
inline constexpr std::array<std::string_view, 2> daniel_nicknames = {"dan",
                                                                     "danny"};
inline constexpr std::array<std::string_view, 1> david_nicknames = {"dave"};
inline constexpr std::array<std::string_view, 1> donald_nicknames = {"don"};
inline constexpr std::array<std::string_view, 2> edward_nicknames = {"ed",
                                                                     "eddie"};
inline constexpr std::array<std::string_view, 3> elizabeth_nicknames = {
    "eliza", "liz", "liza"};
inline constexpr std::array<std::string_view, 1> eleanor_nicknames = {"ellie"};
inline constexpr std::array<std::string_view, 1> francis_nicknames = {"frank"};
inline constexpr std::array<std::string_view, 1> frederick_nicknames = {"fred"};
inline constexpr std::array<std::string_view, 2> gerald_nicknames = {"gary",
                                                                     "jerry"};
inline constexpr std::array<std::string_view, 1> gregory_nicknames = {"greg"};
inline constexpr std::array<std::string_view, 2> harold_nicknames = {"harry",
                                                                     "hal"};
inline constexpr std::array<std::string_view, 2> john_nicknames = {"jack",
                                                                   "johnny"};
inline constexpr std::array<std::string_view, 1> jacob_nicknames = {"jake"};
inline constexpr std::array<std::string_view, 1> janet_nicknames = {"jan"};
inline constexpr std::array<std::string_view, 1> jeffrey_nicknames = {"jeff"};
inline constexpr std::array<std::string_view, 2> jennifer_nicknames = {"jen",
                                                                       "jenny"};
inline constexpr std::array<std::string_view, 2> james_nicknames = {"jim",
                                                                    "jimmy"};
inline constexpr std::array<std::string_view, 3> joseph_nicknames = {
    "joe", "joey", "jody"};
inline constexpr std::array<std::string_view, 1> jonathan_nicknames = {"jon"};
inline constexpr std::array<std::string_view, 1> joshua_nicknames = {"josh"};
inline constexpr std::array<std::string_view, 1> joy_nicknames = {"joyce"};
inline constexpr std::array<std::string_view, 1> judith_nicknames = {"judy"};
inline constexpr std::array<std::string_view, 2> katherine_nicknames = {
    "kate", "kathy"};
inline constexpr std::array<std::string_view, 1> kenneth_nicknames = {"ken"};
inline constexpr std::array<std::string_view, 1> lawrence_nicknames = {"larry"};
inline constexpr std::array<std::string_view, 1> lewis_nicknames = {"lou"};
inline constexpr std::array<std::string_view, 2> margaret_nicknames = {"maggie",
                                                                       "marge"};
inline constexpr std::array<std::string_view, 1> martin_nicknames = {"marty"};
inline constexpr std::array<std::string_view, 1> matthew_nicknames = {"matt"};
inline constexpr std::array<std::string_view, 1> megan_nicknames = {"meg"};
inline constexpr std::array<std::string_view, 1> melvin_nicknames = {"mel"};
inline constexpr std::array<std::string_view, 1> michael_nicknames = {"mike"};
inline constexpr std::array<std::string_view, 1> nicholas_nicknames = {"nick"};
inline constexpr std::array<std::string_view, 1> patrick_nicknames = {"pat"};
inline constexpr std::array<std::string_view, 1> peter_nicknames = {"pete"};
inline constexpr std::array<std::string_view, 1> philip_nicknames = {"phil"};
inline constexpr std::array<std::string_view, 2> richard_nicknames = {"rick",
                                                                      "rich"};
inline constexpr std::array<std::string_view, 1> ronald_nicknames = {"ron"};
inline constexpr std::array<std::string_view, 1> samuel_nicknames = {"sam"};
inline constexpr std::array<std::string_view, 1> steven_nicknames = {"steve"};
inline constexpr std::array<std::string_view, 1> susan_nicknames = {"sue"};
inline constexpr std::array<std::string_view, 1> theodore_nicknames = {"ted"};
inline constexpr std::array<std::string_view, 1> terence_nicknames = {"terry"};
inline constexpr std::array<std::string_view, 1> timothy_nicknames = {"tim"};
inline constexpr std::array<std::string_view, 1> thomas_nicknames = {"tom"};
inline constexpr std::array<std::string_view, 1> anthony_nicknames = {"tony"};
inline constexpr std::array<std::string_view, 1> victor_nicknames = {"vic"};
inline constexpr std::array<std::string_view, 2> zachary_nicknames = {"zack",
                                                                      "zak"};
inline constexpr std::array<std::string_view, 1> nastya_nicknames = {"nastia"};
inline constexpr std::array<std::string_view, 1> douglas_nicknames = {"doug"};
inline constexpr std::array<std::string_view, 1> mitchell_nicknames = {"mitch"};
inline constexpr std::array<std::string_view, 1> wesley_nicknames = {"wes"};
inline constexpr std::array<std::string_view, 1> patricia_nicknames = {
    "tricia"};
inline constexpr std::array<std::string_view, 1> rajiv_nicknames = {"raj"};
} // namespace detail

/**
 * @brief Compile-time nickname mappings for efficient lookup.
 */
inline constexpr std::array<NicknameEntry, 63> NICKNAME_MAPPINGS = {
    {{"alexander", detail::alexander_nicknames},
     {"andrew", detail::andrew_nicknames},
     {"anne", detail::anne_nicknames},
     {"arthur", detail::arthur_nicknames},
     {"benjamin", detail::benjamin_nicknames},
     {"william", detail::william_nicknames},
     {"robert", detail::robert_nicknames},
     {"catherine", detail::catherine_nicknames},
     {"charles", detail::charles_nicknames},
     {"daniel", detail::daniel_nicknames},
     {"david", detail::david_nicknames},
     {"donald", detail::donald_nicknames},
     {"edward", detail::edward_nicknames},
     {"elizabeth", detail::elizabeth_nicknames},
     {"eleanor", detail::eleanor_nicknames},
     {"francis", detail::francis_nicknames},
     {"frederick", detail::frederick_nicknames},
     {"gerald", detail::gerald_nicknames},
     {"gregory", detail::gregory_nicknames},
     {"harold", detail::harold_nicknames},
     {"john", detail::john_nicknames},
     {"jacob", detail::jacob_nicknames},
     {"janet", detail::janet_nicknames},
     {"jeffrey", detail::jeffrey_nicknames},
     {"jennifer", detail::jennifer_nicknames},
     {"james", detail::james_nicknames},
     {"joseph", detail::joseph_nicknames},
     {"jonathan", detail::jonathan_nicknames},
     {"joshua", detail::joshua_nicknames},
     {"joy", detail::joy_nicknames},
     {"judith", detail::judith_nicknames},
     {"katherine", detail::katherine_nicknames},
     {"kenneth", detail::kenneth_nicknames},
     {"lawrence", detail::lawrence_nicknames},
     {"lewis", detail::lewis_nicknames},
     {"margaret", detail::margaret_nicknames},
     {"martin", detail::martin_nicknames},
     {"matthew", detail::matthew_nicknames},
     {"megan", detail::megan_nicknames},
     {"melvin", detail::melvin_nicknames},
     {"michael", detail::michael_nicknames},
     {"nicholas", detail::nicholas_nicknames},
     {"patrick", detail::patrick_nicknames},
     {"peter", detail::peter_nicknames},
     {"philip", detail::philip_nicknames},
     {"richard", detail::richard_nicknames},
     {"ronald", detail::ronald_nicknames},
     {"samuel", detail::samuel_nicknames},
     {"steven", detail::steven_nicknames},
     {"susan", detail::susan_nicknames},
     {"theodore", detail::theodore_nicknames},
     {"terence", detail::terence_nicknames},
     {"timothy", detail::timothy_nicknames},
     {"thomas", detail::thomas_nicknames},
     {"anthony", detail::anthony_nicknames},
     {"victor", detail::victor_nicknames},
     {"zachary", detail::zachary_nicknames},
     {"nastya", detail::nastya_nicknames},
     {"douglas", detail::douglas_nicknames},
     {"mitchell", detail::mitchell_nicknames},
     {"wesley", detail::wesley_nicknames},
     {"patricia", detail::patricia_nicknames},
     {"rajiv", detail::rajiv_nicknames}}};

/**
 * @brief Find nicknames for a given formal name.
 * @param formal_name The formal name to look up
 * @return Span of nicknames if found, empty otherwise
 */
constexpr std::span<const std::string_view>
find_nicknames(std::string_view formal_name) noexcept {
  for (const auto &entry : NICKNAME_MAPPINGS) {
    if (entry.formal_name == formal_name) {
      return entry.nicknames;
    }
  }
  return {};
}

} // namespace email_predictor::features

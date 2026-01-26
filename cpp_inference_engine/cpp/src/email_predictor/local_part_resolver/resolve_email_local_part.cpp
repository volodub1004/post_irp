#include "email_predictor/local_part_resolver/resolve_email_local_part.hpp"
#include "email_predictor/features/name_feature_constants.hpp"
#include "string_normalization/normalize.hpp"

namespace {
const std::vector<std::string> &
get_name_group(const email_predictor::name_decomposer::NameDecomposer &nd,
               data_loaders::TemplateToken::Group group) {
  // Initials are handled via boolean
  switch (group) {
  case data_loaders::TemplateToken::Group::First:
    return nd.get_first_names();
  case data_loaders::TemplateToken::Group::Middle:
    return nd.get_middle_names();
  case data_loaders::TemplateToken::Group::Last:
    return nd.get_last_names();
  default:
    throw std::invalid_argument("Unknown name group");
  }
}
} // namespace

namespace email_predictor::local_part_resolver {

std::optional<std::string> resolve_email_local_part(
    const name_decomposer::NameDecomposer &name,
    const std::vector<data_loaders::TemplateToken> &token_seq) {
  std::ostringstream oss;

  for (const auto &token : token_seq) {
    // Handle separator tokens
    if (token.separator.has_value()) {
      oss << token.separator.value();
      continue;
    }

    const auto &group_vec = get_name_group(name, token.group);

    if (static_cast<size_t>(token.index) >= group_vec.size()) {
      return std::nullopt; // name incompatible with token sequence
    }

    std::string raw = group_vec[token.index];
    std::string transformed;
    // Initials are not normalized
    if (token.use_initial) {
      if (raw.empty())
        return std::nullopt;
      char c =
          static_cast<char>(std::tolower(static_cast<unsigned char>(raw[0])));
      transformed = std::string(1, c);
    } else {
      // Normalization tokens are no longer part of candidate templates
      transformed = raw;
    }

    oss << string_normalization::to_lower(transformed);
  }

  return oss.str();
}

} // namespace email_predictor::local_part_resolver

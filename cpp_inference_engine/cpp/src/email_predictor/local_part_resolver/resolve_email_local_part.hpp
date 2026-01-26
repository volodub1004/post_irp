#include <optional>
#include <string>
#include <vector>

#include "data_loader/templates_loader.hpp"
#include "email_predictor/name_decomposer/name_decomposer.hpp"

namespace email_predictor::local_part_resolver {

/**
 * @brief Resolves a tokenized email template into a concrete local part string
 *        using the parsed name structure.
 *
 * @param name_decomposer Parsed name object.
 * @param token_seq Template token sequence to resolve.
 * @return Resolved email local part (e.g. "john.smith").
 */
std::optional<std::string> resolve_email_local_part(
    const name_decomposer::NameDecomposer &name,
    const std::vector<data_loaders::TemplateToken> &token_seq);

} // namespace email_predictor::local_part_resolver

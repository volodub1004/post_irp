#include "third_party/verification/hunter_client.hpp"
#include "third_party/call_api.hpp"

namespace third_party::verification {

static constexpr int MAX_RETRY_ATTEMPS = 5;

HunterClient::HunterClient(std::string api_key)
    : api_key_(std::move(api_key)) {}

std::optional<VerificationResult>
HunterClient::verify_email(const std::string &email) const {

  // Format query
  std::ostringstream url;
  url << "https://api.hunter.io/v2/email-verifier?email=" << escape(email)
      << "&api_key=" << escape(api_key_);

  const auto &response = call_api(
      url.str(), {"Accept: application/json", "User-Agent: irp-email/1.0"});

  if (response.has_value()) {
    try {
      // Parse response - CoPilot helped a lot here. Was getting some weird
      // library internal errors in previous implementations.
      const nlohmann::json &j = *response;

      // Hunter often wraps fields under "data"
      const nlohmann::json *data = &j;
      if (j.contains("data") && j["data"].is_object())
        data = &j["data"];
      if (j.contains("errors"))
        return std::nullopt; // provider error payload

      VerificationResult result;
      // Use .value(...) to avoid assertions on missing keys
      const std::string status =
          data->value("result", data->value("status", ""));
      result.status = status;
      result.score = data->value("score", 0);

      // Consider smtp_check if present
      const bool smtp_ok = data->value("smtp_check", false);
      result.is_deliverable =
          (status == "deliverable") || (status == "valid") || smtp_ok;

      result.raw_json = j.dump();

      return result;
    } catch (...) {
      return std::nullopt; // Parsing error
    }
  } else {
    // Error
    return std::nullopt;
  }
}

} // namespace third_party::verification

#pragma once

#include <optional>
#include <string>

namespace third_party::verification {

/**
 * @brief Struct containing the result of an email verification lookup.
 */
struct VerificationResult {
  std::string email; ///< The email address that was verified.
  std::string
      status; ///< Hunter.io status (e.g., "valid", "invalid", "unknown").
  int score;  ///< Confidence score (0–100).
  bool is_deliverable;  ///< True if email is marked as deliverable.
  std::string raw_json; ///< Full raw JSON response from Hunter API.
};

/**
 * @brief Client for interfacing with the Hunter.io email verification API.
 *
 * This client provides a simple wrapper to submit email addresses for
 * verification, returning structured results including deliverability score and
 * status.
 *
 * @note CoPilot helped heavily here especially for debugging Curl and JSON
 * unpacking errors. Also, this is the major bottleneck for latency. It is much
 * better for this to be done in-house rather than relying on third-party APIs.
 */
class HunterClient {
public:
  /**
   * @brief Construct a new HunterClient.
   *
   * @param api_key Hunter.io API key.
   */
  explicit HunterClient(std::string api_key);

  /**
   * @brief Verify the deliverability and status of an email address.
   *
   * @param email The email address to verify.
   * @return std::optional<VerificationResult> Parsed response if successful,
   * std::nullopt otherwise.
   */
  std::optional<VerificationResult>
  verify_email(const std::string &email) const;

private:
  std::string api_key_; ///< Hunter.io API key.
};

} // namespace third_party::verification

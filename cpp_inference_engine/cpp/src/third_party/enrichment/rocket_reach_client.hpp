#pragma once

#include <optional>
#include <string>

namespace third_party::enrichment {

/**
 * @brief Represents enriched contact information retrieved from RocketReach.
 */
struct EnrichmentResult {
  std::string email;        ///< Predicted email.
  std::string name;         ///< Full name.
  std::string job_title;    ///< Current job title or position.
  std::string linkedin_url; ///< LinkedIn profile URL, if available.
  std::string location;     ///< Contact's location.
  std::string phone;        ///< Primary phone number, if available.
  std::string raw_json;     ///< Raw json response.
};

/**
 * @brief Client for querying RocketReach's enrichment API.
 *
 * @note CoPilot was used to guide through Curl commands. Also this is untested
 * code, finance and time restraints did not allow for the full integration of
 * this code.
 */
class RocketReachClient {
public:
  /**
   * @brief Constructs a new RocketReachClient with the provided API key.
   *
   * @param api_key A RocketReach API key used for authorization.
   */
  explicit RocketReachClient(std::string api_key);

  /**
   * @brief Enrich a contact using their name and firm.
   *
   * @param full_name Full name of the contact.
   * @param firm Name of the company or firm.
   * @param predicted_email Predicted email to enrich
   * @return std::optional<EnrichmentResult> Populated result on success,
   * nullopt on failure.
   */
  std::optional<EnrichmentResult>
  enrich_contact(const std::string &full_name, const std::string &firm,
                 const std::string &predicted_email) const;

private:
  std::string
      api_key_; ///< RocketReach API key used in the Authorization header.
};

} // namespace third_party::enrichment

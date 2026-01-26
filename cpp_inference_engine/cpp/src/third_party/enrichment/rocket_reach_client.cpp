#include "third_party/enrichment/rocket_reach_client.hpp"
#include "third_party/call_api.hpp"

#include <nlohmann/json.hpp>
#include <sstream>

namespace third_party::enrichment {

RocketReachClient::RocketReachClient(std::string api_key)
    : api_key_(std::move(api_key)) {}

std::optional<EnrichmentResult>
RocketReachClient::enrich_contact(const std::string &full_name,
                                  const std::string &firm,
                                  const std::string &predicted_email) const {
  // Format url, email is optional but that is what we are enriching
  std::ostringstream url;
  url << "https://api.rocketreach.co/v1/api/lookupProfile"
      << "?name=" << escape(full_name) << "&company=" << escape(firm)
      << "&email=" << escape(predicted_email);

  // HTTP authentication in header
  std::vector<std::string> headers = {"Authorization: Bearer " + api_key_,
                                      "Accept: application/json"};

  // Call api
  auto response = call_api(url.str(), headers);
  if (response.has_value()) {
    try {
      // Parse result
      const auto &json = *response;

      EnrichmentResult result;
      result.email = predicted_email;
      result.name = json.value("name", full_name);
      result.job_title = json.value("job_title", "");
      result.linkedin_url = json.value("linkedin", "");
      result.location = json.value("location", "");
      result.phone =
          json.value("phone_numbers", std::vector<std::string>{}).empty()
              ? ""
              : json["phone_numbers"][0].get<std::string>();
      result.raw_json = json.dump();

      return result;
    } catch (...) {
      return std::nullopt; // JSON parsing error
    }
  } else {
    return std::nullopt; // http error
  }
}

} // namespace third_party::enrichment

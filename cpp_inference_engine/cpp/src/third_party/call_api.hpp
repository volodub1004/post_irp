#pragma once

#include <nlohmann/json.hpp>
#include <optional>
#include <string>
#include <vector>

namespace third_party {

/**
 * @brief Makes an HTTP GET request with optional headers and retries.
 *
 * @param full_url The full URL (including query string) to call.
 * @param headers Optional vector of HTTP headers.
 * @param timeout_seconds Connection + read timeout in seconds.
 * @param max_retries Number of retry attempts for 429 and 5xx errors.
 * @return std::optional<nlohmann::json> The response body if successful, else
 * nullopt.
 *
 * @note CoPilot suggested the use of nlohmann and helped debug errors related
 * to it.
 */
std::optional<nlohmann::json>
call_api(const std::string &full_url,
         const std::vector<std::string> &headers = {}, int timeout_seconds = 10,
         int max_retries = 5);

/**
 * @brief URL encodes a string using libcurl's curl_easy_escape.
 *
 * @param s The input string to be URL encoded.
 * @return A URL encoded version of the input string.
 */
std::string escape(const std::string &s);

} // namespace third_party

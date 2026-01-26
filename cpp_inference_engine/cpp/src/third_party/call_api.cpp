#include "call_api.hpp"

#include <curl/curl.h>
#include <iostream>
#include <sstream>
#include <thread>

namespace third_party {

namespace {
/**
 * @brief Callback function for libcurl to write response data into a
 * std::string.
 *
 * @param contents Pointer to the received data chunk.
 * @param size Size of each data unit (usually 1).
 * @param nmemb Number of data units received.
 * @param output Pointer to a std::string where the data should be accumulated.
 * @return size_t The total number of bytes successfully written to the output
 * string.
 */
size_t write_callback(void *contents, size_t size, size_t nmemb,
                      std::string *output) {
  size_t total_size = size * nmemb;
  // Save result to string and output size
  output->append(static_cast<char *>(contents), total_size);
  return total_size;
}
} // namespace

std::optional<nlohmann::json> call_api(const std::string &full_url,
                                       const std::vector<std::string> &headers,
                                       int timeout_seconds, int max_retries) {
  // Init curl command
  CURL *curl = curl_easy_init();
  if (!curl)
    return std::nullopt;

  std::string response_data;
  long http_code = 0;
  int retry_delay_ms = 500;

  // Add headers
  struct curl_slist *header_list = nullptr;
  for (const auto &h : headers) {
    header_list = curl_slist_append(header_list, h.c_str());
  }

  // Common curl opts
  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, header_list);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);
  curl_easy_setopt(curl, CURLOPT_TIMEOUT, timeout_seconds);
  curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, timeout_seconds);
  curl_easy_setopt(curl, CURLOPT_FAILONERROR, 0L);
  curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L); // safe in multithreaded code
  curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, ""); // enable gzip/deflate

  for (int attempt = 0; attempt < max_retries; ++attempt) {
    response_data.clear();
    curl_easy_setopt(curl, CURLOPT_URL, full_url.c_str());

    CURLcode res = curl_easy_perform(curl);
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    // HTTP 200 = good
    if (res == CURLE_OK && http_code == 200) {
      try {
        // Response to json
        auto json = nlohmann::json::parse(response_data);
        curl_slist_free_all(header_list);
        curl_easy_cleanup(curl);
        return json;
      } catch (...) {
        curl_slist_free_all(header_list);
        curl_easy_cleanup(curl);
        return std::nullopt; // JSON parsing error
      }
    }

    // Retry on rate limit, 5xx, and common transient curl errors
    bool retryable_http =
        (http_code == 429) || (http_code >= 500 && http_code < 600);
    bool retryable_curl =
        (res == CURLE_OPERATION_TIMEDOUT) ||
        (res == CURLE_COULDNT_RESOLVE_HOST) || (res == CURLE_COULDNT_CONNECT) ||
        (res == CURLE_RECV_ERROR) || (res == CURLE_SEND_ERROR);

    if ((retryable_http || retryable_curl) && attempt + 1 < max_retries) {
      std::this_thread::sleep_for(std::chrono::milliseconds(retry_delay_ms));
      retry_delay_ms = std::min(retry_delay_ms * 2, 8000); // backoff cap
      continue;
    }
    break; // non retryable
  }

  curl_slist_free_all(header_list);
  curl_easy_cleanup(curl);
  return std::nullopt;
}

std::string escape(const std::string &s) {
  // Format escape for third party tools to format urls
  CURL *curl = curl_easy_init();
  if (!curl)
    return std::string(s);
  char *out = curl_easy_escape(curl, s.data(), static_cast<int>(s.size()));
  std::string res = out ? out : "";
  if (out)
    curl_free(out);
  curl_easy_cleanup(curl);
  return res;
}

} // namespace third_party

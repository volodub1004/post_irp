#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace email_predictor::name_decomposer
{

  /**
   * @class NameDecomposer
   * @brief Decomposes full names into first, middle, and last parts, with
   * normalization and structural access.
   *
   * @note CoPilot was used for debugging edge cases and suggested improvements to
   * API design, such as ranges library.
   */
  class NameDecomposer
  {
  public:
    /**
     * @brief Constructs a NameDecomposer by parsing the given full name.
     * @param full_name A raw full name string.
     */
    explicit NameDecomposer(std::string_view full_name);

    /// @brief Move constructor.
    NameDecomposer(NameDecomposer &&) noexcept = default;

    /// @brief Move assignment operator.
    NameDecomposer &operator=(NameDecomposer &&) noexcept = default;

    /// @brief Copy constructor.
    NameDecomposer(const NameDecomposer &) = default;

    /// @brief Copy assignment operator.
    NameDecomposer &operator=(const NameDecomposer &) = default;

    /// @brief Destructor.
    ~NameDecomposer() = default;

    /**
     * @brief Gets parsed first name components.
     * @return Vector of first name tokens.
     */
    const std::vector<std::string> &get_first_names() const noexcept;

    /**
     * @brief Gets parsed middle name components.
     * @return Vector of middle name tokens.
     */
    const std::vector<std::string> &get_middle_names() const noexcept;

    /**
     * @brief Gets parsed last name components.
     * @return Vector of last name tokens.
     */
    const std::vector<std::string> &get_last_names() const noexcept;

    /**
     * @brief Checks if a middle name exists.
     * @return True if any middle name tokens are present.
     */
    bool has_middle_name() const noexcept;

    /**
     * @brief Checks for multiple first names.
     * @return True if more than one first name is present.
     */
    bool has_multiple_first_names() const noexcept;

    /**
     * @brief Checks for multiple middle names.
     * @return True if more than one middle name is present.
     */
    bool has_multiple_middle_names() const noexcept;

    /**
     * @brief Checks for multiple last names.
     * @return True if more than one last name is present.
     */
    bool has_multiple_last_names() const noexcept;

  private:
    /**
     * @brief Parses and tokenizes the full name into structured parts.
     */
    void parse_name();

    /**
     * @brief Normalizes the input name string.
     * @param raw_input Original raw name.
     * @return Normalized string.
     */
    static std::string normalize_full_name(std::string_view raw_input);

    std::string cleaned_full_name_;         ///< Cleaned and normalized full name.
    std::vector<std::string> first_names_;  ///< Tokenized first names.
    std::vector<std::string> middle_names_; ///< Tokenized middle names.
    std::vector<std::string> last_names_;   ///< Tokenized last names.
  };

} // namespace email_predictor::name_decomposer

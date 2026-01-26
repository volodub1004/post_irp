#include "email_predictor/email_prediction_engine.hpp"
#include "data_loader/templates_loader.hpp"
#include "email_predictor/local_part_resolver/resolve_email_local_part.hpp"

#include <iostream>
#include <stdexcept>

namespace email_predictor
{
    // Default deleter. Allows docker builder to see full definitions for optional
    // members.
    EmailPredictionResult::~EmailPredictionResult() = default;

    template <class Pred>
    EmailPredictionEngine<Pred>::EmailPredictionEngine(
        std::shared_ptr<Pred> std_predictor,
        std::shared_ptr<Pred> complex_predictor,
        const std::string &std_candidate_templates_path,
        const std::string &complex_candidate_templates_path,
        const std::string &firm_template_map_path,
        const std::optional<std::string> &canonical_firms_path,
        const std::optional<std::string> &firm_cache_path,
        std::optional<std::string> hunter_api_key,
        std::optional<std::string> rocket_api_key)
        : std_predictor_(std::move(std_predictor)),
          complex_predictor_(std::move(complex_predictor)),
          verification_pipeline_(
              hunter_api_key && !hunter_api_key->empty()
                  ? std::optional<third_party::verification::HunterClient>(
                        std::in_place, *hunter_api_key)
                  : std::nullopt),
          enrichment_pipeline_(
              rocket_api_key && !rocket_api_key->empty()
                  ? std::optional<third_party::enrichment::RocketReachClient>(
                        std::in_place, *rocket_api_key)
                  : std::nullopt)
    {
        // Load template data
        if (!data_loaders::load_template_data(
                std_candidate_templates_path, complex_candidate_templates_path,
                firm_template_map_path, std_templates_, complex_templates_,
                firm_stats_, firm_usage_map_))
        {
            throw std::runtime_error("Unable to load templates!");
        }

        // Load domain resolver if provided with path
        if (canonical_firms_path.has_value() && firm_cache_path.has_value())
        {
            domain_resolver_.emplace(std::move(domain_resolver::DomainResolver(
                *canonical_firms_path, *firm_cache_path)));
        }
    }

    template <class Pred>
    std::vector<EmailPredictionResult> EmailPredictionEngine<Pred>::predict(
        const std::string &investor_name, const std::string &firm_name,
        std::size_t top_k, std::optional<std::string> domain) const
    {
        std::string domain_string;
        // Resolve domain
        if (domain.has_value())
        {
            domain_string = domain.value();
        }
        else if (domain_resolver_.has_value())
        {
            auto [resolved_domain, matched_firm, score] =
                (*domain_resolver_).resolve_domain(firm_name);
            domain_string = std::move(resolved_domain);

            // Report confidence
            std::cout << "Domain resolved with " << score << " confidence, matched to "
                      << matched_firm << "!" << std::endl;
        }
        else
        {
            throw std::runtime_error("Not provided with domain or domain resolver!");
        }

        // Decompose name
        name_decomposer::NameDecomposer name_struct(investor_name);

        // Get flags
        auto flags = features::InvestorFeatureExtractor::extract(investor_name);

        // Determine which model to use
        bool complex_name = name_struct.has_middle_name() ||
                            name_struct.has_multiple_first_names() ||
                            name_struct.has_multiple_last_names() ||
                            flags.has_german_char || flags.has_nfkd_normalized;

        // Build candidate_ids + feature matrix
        auto feature_rows = features::builder::build_feature_rows(
            name_struct, flags, firm_name,
            complex_name ? complex_templates_ : std_templates_, firm_stats_,
            firm_usage_map_);

        // Score and get top k predictions
        auto top_predictions = complex_name
                                   ? complex_predictor_->predict_top_templates(
                                         feature_rows, complex_templates_, top_k)
                                   : std_predictor_->predict_top_templates(
                                         feature_rows, std_templates_, top_k);

        // Format result
        std::vector<EmailPredictionResult> results;
        results.reserve(top_predictions.size());

        for (const auto &pred : top_predictions)
        {
            std::string full_email;

            const auto &tokens = pred.metadata->token_seq;
            auto local_part =
                local_part_resolver::resolve_email_local_part(name_struct, tokens);
            if (local_part.has_value())
            {
                full_email = local_part.value() + "@" + domain_string;
            }
            else
            {
                continue; // Template incompatible
            }

            results.push_back(EmailPredictionResult{
                full_email, pred.score, pred.template_id, {}, {}});
        }

        // Track best score for enrichment
        EmailPredictionResult *best_result_ptr = nullptr;

        // Verify if pipeline is available
        if (verification_pipeline_.has_value())
        {
            auto &verifier = *verification_pipeline_;
            for (auto &result : results)
            {
                // Score email
                result.verification_result = verifier.verify_email(result.email);

                if (result.verification_result.has_value())
                {
                    // Track best score
                    int score = result.verification_result->score;
                    if (!best_result_ptr ||
                        score > best_result_ptr->verification_result->score)
                    {
                        best_result_ptr = &result;
                    }
                }
            }
        }

        // Enrich the best scoring result
        if (enrichment_pipeline_ && best_result_ptr)
        {
            auto enriched = enrichment_pipeline_->enrich_contact(
                investor_name, firm_name, best_result_ptr->email);

            if (enriched.has_value())
            {
                best_result_ptr->enrichment_result = std::move(enriched);
            }
        }

        return results;
    }

} // namespace email_predictor

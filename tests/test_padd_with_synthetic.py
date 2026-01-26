import pandas as pd
import json
from email_prediction.feature_engineering.padding.generate_synthetic_investors import (
    generate_synthetic_investors_for_profiles,
)
from email_prediction.feature_engineering.padding.firm_profiler import (
    summarize_drift,
    build_firm_profile,
)


# Helpers for tests
def make_template(template_tokens, template_id, weight, flag_probs):
    return {
        "template_id": template_id,
        "template": json.dumps(template_tokens),
        "sampling_weight": weight,
        "flag_probs": flag_probs,
    }


def make_profile(n_templates=2, weights=None):
    # Creates minimal profile based on templates
    weights = weights or [0.5] * n_templates
    templates = [
        make_template(
            ["f_0", ".", f"last_{i}"],
            i,
            weights[i],
            {"has_nickname": i / (n_templates - 1) if n_templates > 1 else 0.0},
        )
        for i in range(n_templates)
    ]
    return {
        "test_firm": {
            "firm": "test_firm",
            "is_shared_infra": False,
            "firm_is_multi_domain": True,
            "templates": templates,
        }
    }


def test_row_count_and_id_range():
    # Check correct number of investors is produced
    n_pad = 10
    start_id = 1000
    profile = make_profile()
    df, last_id = generate_synthetic_investors_for_profiles(
        profile, n_padding=n_pad, starting_id=start_id
    )
    assert len(df["test_firm"]) == 10
    assert df["test_firm"]["id"].min() == 1001
    assert df["test_firm"]["id"].max() == start_id + n_pad
    assert last_id == start_id + n_pad


def test_template_distribution():
    # Set sample weights
    weights = [0.6, 0.4]
    profile = make_profile(weights=weights)
    df, _ = generate_synthetic_investors_for_profiles(
        profile, n_padding=10, starting_id=0
    )

    # Check new distribution matches
    token_counts = (
        df["test_firm"]["token_seq"].apply(tuple).value_counts(normalize=True)
    )
    assert abs(token_counts.iloc[0] - 0.6) <= 0.1  # within rounding tolerance
    assert abs(token_counts.iloc[1] - 0.4) <= 0.1


def test_flag_sampling_rough_distribution():
    profile = make_profile(weights=[1.0], n_templates=1)  # Only one template
    profile["test_firm"]["templates"][0]["flag_probs"] = {"has_nickname": 0.75}

    # Generate and check nickname freq
    df, _ = generate_synthetic_investors_for_profiles(profile, n_padding=1000)
    nickname_rate = df["test_firm"]["has_nickname"].mean()
    assert 0.70 < nickname_rate < 0.80  # Tolerance window


def test_pad_with_synthetic_and_validate_drift():
    # Create small clean dataset
    base_data = pd.DataFrame(
        [
            {
                "id": 1,
                "firm": "alpha",
                "investor": "a1",
                "is_shared_infra": False,
                "firm_is_multi_domain": True,
                "token_seq": ["f_0", ".", "last_0"],
                "has_german_char": False,
                "has_nfkd_normalized": False,
                "has_nickname": True,
                "has_multiple_first_names": False,
                "has_middle_name": False,
                "has_multiple_middle_names": False,
                "has_multiple_last_names": False,
            }
        ]
    )

    # Create candidate template row matching the data
    candidate_templates = pd.DataFrame(
        [
            {
                "template_id": 1,
                "template": json.dumps(["f_0", ".", "last_0"]),
                "sampling_weight": 1.0,
                "flag_probs": {
                    "has_german_char": 0.0,
                    "has_nfkd_normalized": 0.0,
                    "has_nickname": 1.0,
                    "has_multiple_first_names": 0.0,
                    "has_middle_name": 0.0,
                    "has_multiple_middle_names": 0.0,
                    "has_multiple_last_names": 0.0,
                },
            }
        ]
    )

    # Manually build matching firm_template_map
    firm_template_map = pd.DataFrame(
        [
            {
                "firm": "alpha",
                "template_ids": json.dumps([1]),
                "num_templates": 1,
                "num_investors": 1,
                "diversity_ratio": 1.0,
                "is_single_template": True,
            }
        ]
    )

    # Profile the firm before
    profile_before = build_firm_profile(
        base_data,
        firm_template_map,
        candidate_templates,
        ["alpha"],
    )
    assert profile_before is not None

    # Pad the data
    synthetic_map, _ = generate_synthetic_investors_for_profiles(
        profile_before, n_padding=50
    )

    # flatten into one DataFrame
    synthetic_df = pd.concat(
        [df for df in synthetic_map.values() if not df.empty], ignore_index=True
    )

    # append to original
    augmented = pd.concat([base_data, synthetic_df], ignore_index=True)

    # Re-profile after synthetic generation
    profile_after = build_firm_profile(
        augmented,
        firm_template_map,
        candidate_templates,
        ["alpha"],
    )
    assert profile_after is not None

    # Compare drift
    drift = summarize_drift(profile_before, profile_after)

    # Assertions
    assert len(augmented) == len(base_data) + 49
    assert drift["global"]["template_structure_mismatches"] == 0
    assert (
        drift["global"]["total_flag_drift"] < 0.1
    )  # Should be very low, since flags are sampled from profile

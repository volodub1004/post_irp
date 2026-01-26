import pandas as pd
import json
from email_prediction.feature_engineering.padding.firm_profiler import (
    build_firm_profile,
    summarize_drift,
)


def test_build_firm_profile_basic():
    # Input data setup
    firm_id = "test_firm"

    lp_clean_df = pd.DataFrame(
        {
            "firm": [firm_id, firm_id, firm_id],
            "token_seq": [
                ["f_0", ".", "last_0"],
                ["f_0", ".", "last_0"],
                ["f_0", "last_0"],
            ],
            "is_shared_infra": [False, False, False],
            "firm_is_multi_domain": [True, True, True],
            "has_german_char": [1, 0, 0],
            "has_nfkd_normalized": [0, 1, 0],
            "has_nickname": [0, 0, 1],
            "has_multiple_first_names": [0, 0, 0],
            "has_middle_name": [0, 0, 0],
            "has_multiple_middle_names": [0, 0, 0],
            "has_multiple_last_names": [0, 0, 0],
        }
    )
    firm_template_map_df = pd.DataFrame(
        {"firm": [firm_id], "template_ids": [json.dumps([1, 2])], "num_investors": 2}
    )
    candidate_templates_df = pd.DataFrame(
        {
            "template_id": [1, 2],
            "template": [
                json.dumps(["f_0", ".", "last_0"]),
                json.dumps(["f_0", "last_0"]),
            ],
        }
    )

    result = build_firm_profile(
        lp_clean_df, firm_template_map_df, candidate_templates_df, [firm_id]
    )

    # Validate structure
    assert result is not None
    assert result[firm_id]["firm"] == firm_id
    assert isinstance(result[firm_id]["templates"], list)
    assert all("sampling_weight" in t for t in result[firm_id]["templates"])
    assert (
        abs(sum(t["sampling_weight"] for t in result[firm_id]["templates"]) - 1.0)
        < 1e-6
    )

    # Validate flag_probs
    for template in result[firm_id]["templates"]:
        assert "flag_probs" in template
        assert all(
            k in template["flag_probs"]
            for k in [
                "has_german_char",
                "has_nfkd_normalized",
                "has_nickname",
                "has_multiple_first_names",
                "has_middle_name",
                "has_multiple_middle_names",
                "has_multiple_last_names",
            ]
        )


def test_build_firm_profile_correct_output():
    firm_id = "example_firm"

    # 3 investors, 2 template sequences
    lp_clean_df = pd.DataFrame(
        {
            "firm": [firm_id] * 3,
            "token_seq": [
                ["f_0", ".", "last_0"],
                ["f_0", ".", "last_0"],
                ["f_0", "last_0"],
            ],
            "is_shared_infra": [False] * 3,
            "firm_is_multi_domain": [True] * 3,
            "has_german_char": [1, 0, 0],
            "has_nfkd_normalized": [0, 1, 0],
            "has_nickname": [0, 0, 1],
            "has_multiple_first_names": [0, 0, 0],
            "has_middle_name": [0, 0, 0],
            "has_multiple_middle_names": [0, 0, 0],
            "has_multiple_last_names": [0, 0, 0],
        }
    )

    # Firm uses template 1 and 2
    firm_template_map_df = pd.DataFrame(
        {"firm": [firm_id], "template_ids": [json.dumps([1, 2])], "num_investors": 3}
    )

    # Candidate templates
    candidate_templates_df = pd.DataFrame(
        {
            "template_id": [1, 2],
            "template": [
                json.dumps(["f_0", ".", "last_0"]),
                json.dumps(["f_0", "last_0"]),
            ],
        }
    )

    result = build_firm_profile(
        lp_clean_df, firm_template_map_df, candidate_templates_df, [firm_id]
    )

    assert result is not None
    assert result[firm_id]["firm"] == firm_id
    assert bool(result[firm_id]["is_shared_infra"]) is False
    assert bool(result[firm_id]["firm_is_multi_domain"]) is True

    # Check the templates section
    templates = result[firm_id]["templates"]
    assert len(templates) == 2

    # Convert to dict by template str for easy comparison
    tmpl_map = {t["template"]: t for t in templates}

    # Template 1, used twice by first two investors
    t1 = json.dumps(["f_0", ".", "last_0"])
    expected_t1_weight = 2 / 3
    expected_t1_flags = {
        "has_german_char": 0.5,  # (1 + 0) / 2
        "has_nfkd_normalized": 0.5,  # (0 + 1) / 2
        "has_nickname": 0.0,
    }

    # Template 2, used once by third investor
    t2 = json.dumps(["f_0", "last_0"])
    expected_t2_weight = 1 / 3
    expected_t2_flags = {
        "has_german_char": 0.0,
        "has_nfkd_normalized": 0.0,
        "has_nickname": 1.0,
    }

    # Tolerances
    tol = 1e-6

    assert abs(tmpl_map[t1]["sampling_weight"] - expected_t1_weight) < tol
    assert abs(tmpl_map[t2]["sampling_weight"] - expected_t2_weight) < tol

    for k, v in expected_t1_flags.items():
        assert abs(tmpl_map[t1]["flag_probs"][k] - v) < tol

    for k, v in expected_t2_flags.items():
        assert abs(tmpl_map[t2]["flag_probs"][k] - v) < tol


def make_profile(template_data, firm_name="dummy_firm"):
    # Helper for summarize tests
    return {
        firm_name: {
            "firm": firm_name,
            "is_shared_infra": False,
            "firm_is_multi_domain": True,
            "templates": template_data,
        }
    }


def test_summarize_drift_basic_drift():
    # Basic drift to check differences in flag probs
    before = make_profile(
        [
            {
                "template": json.dumps(["f_0", ".", "last_0"]),
                "sampling_weight": 0.7,
                "flag_probs": {"has_german_char": 0.4, "has_nickname": 0.2},
            },
            {
                "template": json.dumps(["f_0", "last_0"]),
                "sampling_weight": 0.3,
                "flag_probs": {"has_german_char": 0.1, "has_nickname": 0.0},
            },
        ]
    )

    after = make_profile(
        [
            {
                "template": json.dumps(["f_0", ".", "last_0"]),
                "sampling_weight": 0.5,
                "flag_probs": {"has_german_char": 0.5, "has_nickname": 0.0},
            },
            {
                "template": json.dumps(["f_0", "last_0"]),
                "sampling_weight": 0.5,
                "flag_probs": {"has_german_char": 0.2, "has_nickname": 0.05},
            },
        ]
    )

    result = summarize_drift(before, after)

    assert result["global"]["template_structure_mismatches"] == 0
    assert result["global"]["num_flags_with_drift"] == 2
    assert round(result["global"]["max_sampling_weight_drift"], 2) == 0.2
    assert result["global"]["max_flag_drift"]["has_german_char"] == 0.1
    assert result["global"]["max_flag_drift"]["has_nickname"] == 0.2


def test_summarize_drift_with_template_mismatch():
    # Different templates
    before = make_profile(
        [
            {
                "template": json.dumps(["f_0", ".", "last_0"]),
                "sampling_weight": 1.0,
                "flag_probs": {"has_nickname": 0.1},
            },
        ]
    )

    after = make_profile(
        [
            {
                "template": json.dumps(["f_0", "last_0"]),
                "sampling_weight": 1.0,
                "flag_probs": {"has_nickname": 0.9},
            },
        ]
    )

    result = summarize_drift(before, after)
    assert (
        result["global"]["template_structure_mismatches"] == 2
    )  # both templates missing in the other
    assert result["global"]["max_sampling_weight_drift"] == 0.0
    assert result["global"]["num_flags_with_drift"] == 0

import json
import pandas as pd
from unittest.mock import patch
from email_prediction.feature_engineering.pipeline import (
    _split_dataset_by_complexity,
    _build_profile_and_pad,
)


def test_split_by_complexity():
    df = pd.DataFrame(
        [
            {
                "token_seq": ["f_0"],
                "has_middle_name": True,
                "has_nfkd_normalized": False,
                "has_german_char": False,
                "has_multiple_first_names": False,
                "has_multiple_middle_names": False,
                "has_multiple_last_names": False,
            },
            {
                "token_seq": ["f_0"],
                "has_middle_name": False,
                "has_nfkd_normalized": False,
                "has_german_char": False,
                "has_multiple_first_names": False,
                "has_multiple_middle_names": False,
                "has_multiple_last_names": False,
            },
        ]
    )
    # Test split function basics. Internals are tested elswhere
    templates = pd.DataFrame([{"template_id": 1, "template": json.dumps(["f_0"])}])
    # Patch to_csv on DataFrame globally for this test
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        result = _split_dataset_by_complexity(df, templates)
        assert "std_name_set" in result
        assert "complex_name_set" in result
        assert mock_to_csv.call_count == 2  # Ensure both files were attempted


@patch(
    "email_prediction.feature_engineering.pipeline.build_firm_profile",
    return_value={
        "firm": "f",
        "templates": [{"template": ["f_0"], "sampling_weight": 1.0, "flag_probs": {}}],
    },
)
@patch(
    "email_prediction.feature_engineering.pipeline.generate_synthetic_investors_for_profiles",
    return_value=(
        {
            "f": pd.DataFrame(
                [{"investor": "synthetic_investor_f_0", "token_seq": ["f_0"]}]
            )
        },
        None,
    ),
)
def test_build_profile_and_pad(mock_pad, mock_build):
    df = pd.DataFrame([{"firm": "f", "token_seq": ["f_0"]}])
    # Same here, internals are tested elsewhere
    result = _build_profile_and_pad(df, pd.DataFrame(), pd.DataFrame(), ["f"], n_pad=10)
    assert not result.empty

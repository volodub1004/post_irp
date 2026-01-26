import json
import pandas as pd
import pytest
from email_prediction.feature_engineering.features.feature_builder import (
    _build_firm_template_lookup,
    _build_firm_stats_lookup,
    build_feature_matrix,
)
from db.models import TableName
from db.db import read_table


@pytest.fixture
def firm_template_map_df():
    return pd.DataFrame(
        [
            {
                "firm": "Acme",
                "template_ids": json.dumps([10, 11]),
                "num_templates": 2,
                "num_investors": 1,
                "diversity_ratio": 2.0,
                "is_single_template": False,
            }
        ]
    )


@pytest.fixture
def candidate_templates_df():
    return pd.DataFrame(
        [
            {
                "template_id": 10,
                "template": json.dumps(["f", ".", "last"]),
                "support_count": 5,
                "coverage_pct": 0.2,
                "in_mined_rules": True,
                "max_rule_confidence": 0.9,
                "avg_rule_confidence": 0.85,
                "uses_middle_name": False,
                "uses_multiple_firsts": False,
                "uses_multiple_middles": False,
                "uses_multiple_lasts": False,
            },
            {
                "template_id": 11,
                "template": json.dumps(["first", ".", "last"]),
                "support_count": 2,
                "coverage_pct": 0.1,
                "in_mined_rules": False,
                "max_rule_confidence": 0.5,
                "avg_rule_confidence": 0.45,
                "uses_middle_name": False,
                "uses_multiple_firsts": False,
                "uses_multiple_middles": False,
                "uses_multiple_lasts": False,
            },
        ]
    )


@pytest.fixture
def clean_data_df():
    return pd.DataFrame(
        [
            {
                "id": 1,
                "investor": "Alice",
                "firm": "Acme",
                "token_seq": ["f", ".", "last"],
                "is_shared_infra": False,
                "firm_is_multi_domain": False,
                "has_german_char": False,
                "has_nfkd_normalized": False,
                "has_nickname": False,
                "has_multiple_first_names": False,
                "has_middle_name": False,
                "has_multiple_middle_names": False,
                "has_multiple_last_names": False,
            }
        ]
    )


def test_build_firm_template_lookup(firm_template_map_df):
    lookup = _build_firm_template_lookup(firm_template_map_df)
    assert "Acme" in lookup
    assert 10 in lookup["Acme"]
    assert 11 in lookup["Acme"]
    assert lookup["Acme"][10]["support_count"] == 1
    assert lookup["Acme"][11]["coverage_pct"] == 0.5


def test_build_firm_stats_lookup(firm_template_map_df):
    stats = _build_firm_stats_lookup(firm_template_map_df)
    assert stats["Acme"]["num_templates"] == 2
    assert stats["Acme"]["diversity_ratio"] == 2.0
    assert stats["Acme"]["is_single_template"] is False


@pytest.mark.integration
def test_build_feature_matrix(
    clean_data_df, candidate_templates_df, firm_template_map_df
):
    build_feature_matrix(
        clean_data_df,
        candidate_templates_df,
        firm_template_map_df,
        TableName.FEATURE_MATRIX,
    )

    df = read_table(TableName.FEATURE_MATRIX)

    assert len(df) == 2  # Two candidate templates
    assert set(df["template_id"]) == {10, 11}
    assert df[df["template_id"] == 10]["label"].iloc[0] == 1
    assert df[df["template_id"] == 11]["label"].iloc[0] == 0
    assert df["firm_diversity_ratio"].unique().tolist() == [2.0]

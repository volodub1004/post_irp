import pandas as pd
from pattern_mining.data_enrichment.enrich_candidates import (
    enrich_candidate_templates,
    _is_subsequence,
    _extract_template_structure_features,
)


def test_is_subsequence():
    assert _is_subsequence(["a", "b"], ["a", "x", "b"])
    assert _is_subsequence([], ["a", "b"])
    assert not _is_subsequence(["b", "a"], ["a", "b"])
    assert not _is_subsequence(["a", "c"], ["a", "b"])
    assert _is_subsequence(["a"], ["a"])
    assert not _is_subsequence(["a"], [])


def test_extract_template_structure_features():
    features = _extract_template_structure_features(
        ["first_original_0", ".", "middle_original_0", "last_original_1"]
    )

    assert features["uses_middle_name"] is True
    assert features["uses_multiple_firsts"] is False
    assert features["uses_multiple_middles"] is False
    assert features["uses_multiple_lasts"] is True

    features = _extract_template_structure_features(
        ["f_1", "middle_original_0", "middle_original_1", "last_original_0"]
    )

    assert features["uses_middle_name"] is True
    assert features["uses_multiple_firsts"] is True
    assert features["uses_multiple_middles"] is True
    assert features["uses_multiple_lasts"] is False


def test_enrich_candidate_templates_basic():
    token_seqs = [
        ["0", "-", "1"],
        ["0_sub_1", "1_sub_1", "2_sub_1"],
        ["1_sub_1", "2_sub_1"],
        ["x", "y", "z"],
    ]

    rules = [
        {"lhs_tokens": ["0"], "rhs_tokens": ["1"], "support": 100, "confidence": 0.8},
        {
            "lhs_tokens": ["0_sub_1"],
            "rhs_tokens": ["2_sub_1"],
            "support": 50,
            "confidence": 0.7,
        },
        {"lhs_tokens": ["x"], "rhs_tokens": ["z"], "support": 30, "confidence": 0.6},
    ]

    # minimal DataFrame with token_seq for coverage calc
    clean_df = pd.DataFrame(
        {
            "token_seq": [
                ["0", "-", "1"],
                ["0_sub_1", "1_sub_1", "2_sub_1"],
                ["1_sub_1", "2_sub_1"],
                ["x", "y", "z"],
                ["x", "y", "z"],
            ]
        }
    )

    enriched = enrich_candidate_templates(token_seqs, rules, clean_df)

    assert isinstance(enriched, list)
    assert all("support_count" in e for e in enriched)
    assert all("coverage_pct" in e for e in enriched)

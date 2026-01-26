import pandas as pd
import pytest
from email_prediction.feature_engineering.features.split_and_stratify import (
    split_clean_ids,
)


@pytest.fixture
def mock_clean_df():
    emails = ["12@a.com", "12@b.com", "12@c.com"]
    n_per_domain = 1000
    rows = []

    id_counter = 0
    for email in emails:
        for _ in range(n_per_domain):
            rows.append({"id": id_counter, "email": email})
            id_counter += 1

    return pd.DataFrame(rows)


def test_split_clean_ids_basic_properties(mock_clean_df):
    val_ids, test_ids = split_clean_ids(
        mock_clean_df, test_ratio=0.2, val_ratio=0.2, seed=123
    )

    split_ids = set(val_ids + test_ids)

    # No ID is lost or duplicated
    assert len(split_ids) == len(val_ids) + len(test_ids)

    # Splits are disjoint
    assert set(val_ids).isdisjoint(test_ids)

    # Sizes roughly align
    n = len(mock_clean_df)
    assert abs(len(test_ids) - 0.2 * n) < 0.05 * n
    assert abs(len(val_ids) - 0.2 * n) < 0.05 * n


def test_split_is_deterministic(mock_clean_df):
    # Split twice with same seed
    first = split_clean_ids(mock_clean_df, test_ratio=0.2, seed=42)
    second = split_clean_ids(mock_clean_df, test_ratio=0.2, seed=42)
    assert first == second


def test_domain_distribution_approx_preserved(mock_clean_df):
    # Split dataset
    _, test_ids = split_clean_ids(mock_clean_df, test_ratio=0.2, seed=42)
    test_df = mock_clean_df[mock_clean_df["id"].isin(test_ids)]

    # Compare domain distributions
    mock_clean_df["domain"] = (
        mock_clean_df["email"].str.extract("@(.*)$")[0].str.lower()
    )
    test_df = test_df.copy()
    test_df.loc[:, "domain"] = test_df["email"].str.extract(r"@(.+)$")[0].str.lower()
    full_dist = mock_clean_df["domain"].value_counts(normalize=True).to_dict()
    test_dist = test_df["domain"].value_counts(normalize=True).to_dict()

    for domain in full_dist:
        assert abs(full_dist[domain] - test_dist[domain]) < 0.05

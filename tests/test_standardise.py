import pytest
import pandas as pd
from etl.transform.standardise import (
    _normalise_table,
    _regex_cleaning,
    standardise_table,
    _drop_bad_investor_names,
)


def test_normalise_table_basic():
    df = pd.DataFrame(
        {
            "name": [" John Smith ", "ANNA O'NEILL", None],
            "firm": [" Blackstone ", "KKR", "SoftBank"],
            "num": [1, 2, 3],  # non-text should remain unchanged
        }
    )
    out = _normalise_table(df)
    assert out["name"].tolist() == ["john smith", "anna o'neill", None]
    assert out["firm"].tolist() == ["blackstone", "kkr", "softbank"]
    assert out["num"].equals(df["num"])  # untouched


def test_regex_cleaning_basics():
    df = pd.DataFrame(
        {
            "email": ["joe.bloggs@firm.com>", ' "jane.doe@x.io" '],
            "tel": ["(123) 456-7890", "0044- 7123 456 789"],
            "linkedin": ["https://linkedin.com/in/jane-smith/?ref=abc", None],
            "website": ["https://example.com?session=123", "www.site.org"],
            "notes": [" messy. ", "clean"],  # trailing punc & whitespace
        }
    )
    out = _regex_cleaning(df)
    assert out["email"].tolist() == ["joe.bloggs@firm.com", "jane.doe@x.io"]
    assert out["tel"].tolist() == ["1234567890", "00447123456789"]
    assert out["linkedin"].tolist() == ["linkedin.com/in/jane-smith/", None]
    assert out["website"].tolist() == ["example.com", "www.site.org"]
    assert out["notes"].tolist() == ["messy", "clean"]


@pytest.mark.integration
def test_standardise_table_integration():
    df = pd.DataFrame(
        {
            "id": [1],
            "investor": ["  John SMITH "],
            "email": ['"JOHN.SMITH@EXAMPLE.COM" '],
            "firm": ["Blackstone."],
            "linkedin": ["https://linkedin.com/in/john-smith?ref=abc"],
            "website": ["http://example.com/page?session=xyz"],
            "tel": ["(123) 456-7890"],
        }
    )

    cleaned = standardise_table(df)

    assert cleaned.loc[0, "investor"] == "john smith"
    assert cleaned.loc[0, "email"] == "john.smith@example.com"
    assert cleaned.loc[0, "firm"] == "blackstone"
    assert cleaned.loc[0, "linkedin"] == "linkedin.com/in/john-smith"
    assert cleaned.loc[0, "website"] == "example.com/page"
    assert cleaned.loc[0, "tel"] == "1234567890"


def test_drop_bad_investor_names():
    # Create a dummy DataFrame
    df = pd.DataFrame(
        {
            "investor": [
                "Alice Smith",
                "??",
                None,
                "   ",
                "Bob Jones",
                "???",
                "Charlie",
            ],
            "firm": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta"],
        }
    )

    # Apply function
    cleaned_df = _drop_bad_investor_names(df)

    # Expected remaining investors
    expected_investors = ["Alice Smith", "Bob Jones", "Charlie"]
    assert cleaned_df["investor"].tolist() == expected_investors
    assert cleaned_df.shape[0] == 3
    assert "firm" in cleaned_df.columns


def test_drop_bad_investor_names_raises_if_missing_column():
    df = pd.DataFrame({"firm": ["A", "B", "C"]})

    with pytest.raises(ValueError, match="Missing required 'investor' column."):
        _drop_bad_investor_names(df)

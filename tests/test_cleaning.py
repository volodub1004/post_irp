import pandas as pd
import pytest
from etl.transform.cleaning import (
    drop_rows_missing_emails,
    drop_emails_with_invalid_local,
)


def test_drops_rows_with_missing_email():
    df = pd.DataFrame(
        {
            "email": ["a@example.com", None, "b@example.com", None],
            "name": ["Alice", "Bob", "Carol", "Dave"],
        }
    )
    result = drop_rows_missing_emails(df)

    assert result.shape[0] == 2
    assert result["email"].isnull().sum() == 0
    assert set(result["name"]) == {"Alice", "Carol"}


def test_keeps_all_rows_when_no_missing():
    df = pd.DataFrame(
        {"email": ["a@example.com", "b@example.com"], "name": ["Alice", "Bob"]}
    )
    result = drop_rows_missing_emails(df)

    assert result.shape[0] == 2
    assert result.equals(df)


def test_raises_when_email_column_missing():
    df = pd.DataFrame({"name": ["Alice", "Bob"]})

    with pytest.raises(ValueError, match="Cannot clean data without necessary fields!"):
        drop_rows_missing_emails(df)


def test_drops_nonalpha():
    df = pd.DataFrame(
        {
            "email": [
                "æweig@mcllp.com",  # should drop: æ
                "v.guyotsionnest?@edr.com",  # should drop: ?
                "j-smith@company.com",  # should not drop: - is allowed
            ],
        }
    )

    result = drop_emails_with_invalid_local(df)
    assert result.shape[0] == 1


def test_keeps_valid_if_nonalpha():
    df = pd.DataFrame(
        {
            "email": ["jorg.muller@example.com", "jean.pierre@dupont.com"],
        }
    )

    result = drop_emails_with_invalid_local(df)
    assert result.shape[0] == 2  # nothing dropped


def test_all_ascii_passes():
    df = pd.DataFrame(
        {
            "email": ["alice.smith@example.com", "bob.jones@example.com"],
        }
    )

    result = drop_emails_with_invalid_local(df)
    assert result.equals(df)


def test_mixed_pass_and_fail():
    df = pd.DataFrame(
        {
            "email": [
                "æweig@mcllp.com",  # drop
                "clemence.coppin@weil.com",  # keep
                "jean.michel@example.com",  # keep
            ],
        }
    )

    result = drop_emails_with_invalid_local(df)
    assert result.shape[0] == 2
    assert "æweig@mcllp.com" not in result["email"].values

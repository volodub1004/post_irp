import pytest
import pandas as pd
from etl.transform.validate import (
    _validate_email_field,
    _validate_linkedin,
    _validate_firm_names,
    _validate_investor_names,
    _find_missing_email_linkedin_pairs,
    validate_table,
    flag_multi_domain_firms,
    flag_shared_domain,
)


def test_validate_email_field():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "email": [
                "john.doe@example.com",  # valid
                "invalid@",  # bad format
                "a@x.com",  # too short
                None,  # missing
            ],
        }
    )
    invalid_ids = _validate_email_field(df)
    assert set(invalid_ids) == {2, 3, 4}


def test_validate_linkedin():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "linkedin": [
                "https://linkedin.com/in/john-doe",  # valid
                "https://linkedin.com/company/test",  # invalid path
                None,  # missing
            ],
        }
    )
    assert set(_validate_linkedin(df)) == {2, 3}


def test_validate_firm_names():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "firm": ["blackstone", None, "ai"],  # valid  # missing  # too short
        }
    )
    assert set(_validate_firm_names(df)) == {2, 3}


def test_validate_investor_names():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "investor": [
                "john smith",  # valid (length 10)
                "a b",  # too short
                None,  # missing
            ],
        }
    )
    assert set(_validate_investor_names(df)) == {2, 3}


def test_missing_email_and_linkedin_pairs():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "email": ["test@example.com", None, None],
            "linkedin": [None, None, "linkedin.com/in/user"],
        }
    )
    assert _find_missing_email_linkedin_pairs(df) == [2]


@pytest.mark.integration
def test_validate_table_integration():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "email": ["valid@example.com", "bad@", None, "short@x"],
            "linkedin": [
                "linkedin.com/in/user",
                "linkedin.com/company/foo",
                None,
                None,
            ],
            "firm": ["Blackstone", None, "AI", "KKR"],
            "investor": ["John Smith", "A", None, "Jane Longname"],
        }
    )

    result = validate_table(df)

    assert set(result["invalid_email"]) == {2, 3, 4}
    assert set(result["invalid_linkedin"]) == {2, 3, 4}
    assert set(result["invalid_firm"]) == {2, 3, 4}
    assert set(result["invalid_investor"]) == {2, 3}
    assert result["missing_email_and_linkedin"] == [3]


def test_flag_shared_domain_basic():
    df = pd.DataFrame(
        [
            {"id": 1, "firm": "FirmA", "email": "a@domain1.com"},
            {"id": 2, "firm": "FirmB", "email": "b@domain1.com"},  # shared domain
            {"id": 3, "firm": "FirmC", "email": "c@domain2.com"},
        ]
    )
    flagged = flag_shared_domain(df)

    assert flagged.loc[flagged["id"] == 1, "is_shared_infra"].values[0]
    assert flagged.loc[flagged["id"] == 2, "is_shared_infra"].values[0]
    assert not flagged.loc[flagged["id"] == 3, "is_shared_infra"].values[0]


def test_flag_shared_domain_all_unique():
    df = pd.DataFrame(
        [
            {"id": 1, "firm": "FirmA", "email": "a@domain1.com"},
            {"id": 2, "firm": "FirmB", "email": "b@domain2.com"},
        ]
    )
    flagged = flag_shared_domain(df)

    assert flagged["is_shared_infra"].sum() == 0


def test_flag_multi_domain_firms_basic():
    df = pd.DataFrame(
        [
            {"id": 1, "firm": "FirmX", "email": "a@domain1.com"},
            {
                "id": 2,
                "firm": "FirmX",
                "email": "b@domain2.com",
            },  # FirmX uses 2 domains
            {"id": 3, "firm": "FirmY", "email": "c@domain1.com"},
        ]
    )
    flagged = flag_multi_domain_firms(df)

    assert flagged.loc[flagged["id"] == 1, "firm_is_multi_domain"].values[0]
    assert flagged.loc[flagged["id"] == 2, "firm_is_multi_domain"].values[0]
    assert not flagged.loc[flagged["id"] == 3, "firm_is_multi_domain"].values[0]


def test_flag_multi_domain_firms_all_single_domain():
    df = pd.DataFrame(
        [
            {"id": 1, "firm": "FirmA", "email": "a@domain1.com"},
            {"id": 2, "firm": "FirmA", "email": "b@domain1.com"},  # Same domain
            {"id": 3, "firm": "FirmB", "email": "c@domain2.com"},
        ]
    )
    flagged = flag_multi_domain_firms(df)

    assert flagged["firm_is_multi_domain"].sum() == 0

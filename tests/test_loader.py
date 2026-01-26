import pytest
import pandas as pd

from db.db import read_table
from db.models import TableName
from etl.load.loader import load_raw_data


# Helpers to build minimal DataFrames
def make_lp_df():
    return pd.DataFrame(
        [
            {
                "INVESTOR": "InvA",
                "FIRM TYPE": "TypeA",
                "TITLE": "Mr",
                "NAME": "NameA",
                "ALTERNATIVE NAME": "AltA",
                "ROLE": "RoleA",
                "JOB TITLE": "JT A",
                "ASSET CLASS": "Equity",
                "EMAIL": "a@a.com",
                "TEL": "111",
                "CITY": "CityA",
                "STATE": "StateA",
                "COUNTRY/TERRITORY": "CountryA",
                "ZIP CODE": "ZIPA",
                "LINKEDIN": "LI A",
                "REGION": "RegA",
                "ADDRESS": "AddrA",
                "WEBSITE": "www.a.com",
                "GENERAL EMAIL": "gen@a.com",
            }
        ]
    )


def make_gp_df():
    return pd.DataFrame(
        [
            {
                "FUND MANAGER": "FundA",
                "FIRM TYPE": "TypeG",
                "TITLE": "Dr",
                "NAME": "NameG",
                "JOB TITLE": "JT G",
                "ASSET CLASS": "Debt",
                "EMAIL": "g@g.com",
                "TEL": "222",
                "CITY": "CityG",
                "STATE": "StateG",
                "COUNTRY/TERRITORY": "CountryG",
                "ZIP CODE": "ZIPG",
                "LINKEDIN": "LI G",
                "REGION": "RegG",
                "ADDRESS": "AddrG",
                "WEBSITE": "www.g.com",
                "GENERAL EMAIL": "gen@g.com",
            }
        ]
    )


@pytest.mark.integration
def test_load_raw_lp(monkeypatch):
    """Integration: LP loader writes exactly one row with mapped fields."""
    monkeypatch.setattr(
        "etl.load.loader.extract_excel_data", lambda sheet: make_lp_df()
    )
    load_raw_data(TableName.LP)

    df = read_table(
        TableName.LP,
        columns=["firm", "firm_type", "title", "investor", "email", "general_email"],
        limit=5,
    )
    assert len(df) == 1
    row = df.iloc[0]
    assert row["firm"] == "InvA"
    assert row["firm_type"] == "TypeA"
    assert row["title"] == "Mr"
    assert row["investor"] == "NameA"
    assert row["email"] == "a@a.com"
    assert row["general_email"] == "gen@a.com"


@pytest.mark.integration
def test_load_raw_gp(monkeypatch):
    """Integration: GP loader writes exactly one row with mapped fields."""
    monkeypatch.setattr(
        "etl.load.loader.extract_excel_data", lambda sheet: make_gp_df()
    )
    load_raw_data(TableName.GP)

    df = read_table(
        TableName.GP,
        columns=["firm", "firm_type", "title", "investor", "email", "general_email"],
        limit=5,
    )
    assert len(df) == 1
    row = df.iloc[0]
    assert row["firm"] == "FundA"
    assert row["firm_type"] == "TypeG"
    assert row["title"] == "Dr"
    assert row["investor"] == "NameG"
    assert row["email"] == "g@g.com"
    assert row["general_email"] == "gen@g.com"


@pytest.mark.integration
def test_load_raw_empty_sheet(monkeypatch):
    """Integration: empty sheet triggers ValueError."""
    monkeypatch.setattr(
        "etl.load.loader.extract_excel_data", lambda sheet: pd.DataFrame()
    )
    with pytest.raises(ValueError, match="No data found in sheet: LP Contact Data"):
        load_raw_data(TableName.LP)


def test_load_raw_invalid_table():
    """Unit: invalid enum to load_raw_data should raise immediately."""
    with pytest.raises(ValueError, match="Non conforming table type selected!"):
        load_raw_data(TableName.COMBINED_CLEAN)

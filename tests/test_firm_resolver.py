import pandas as pd
import pytest
from db.db import write_table, read_table
from db.models import TableName
from fuzzlookup.resolver import FirmResolver


def test_resolver_resolves_and_caches_unit(temp_db):
    """Unit test: resolves a raw firm name and writes to cache."""
    canonical = pd.DataFrame(
        [
            {"firm": "Blackstone", "domain": "blackstone.com"},
            {"firm": "Goldman Sachs", "domain": "gs.com"},
        ]
    )
    write_table(TableName.CANONICAL_FIRMS, canonical)

    resolver = FirmResolver(threshold=80)
    result = resolver.resolve("Blacstone")

    assert result[0] == "Blacstone"
    assert result[1] == "Blackstone"
    assert result[2] == "blackstone.com"
    assert result[3] >= 80

    # Check that it's cached
    cached = read_table(TableName.FIRM_CACHE)
    assert "Blacstone" in cached["raw_firm"].values


@pytest.mark.integration
def test_resolver_integrates_with_db(temp_db):
    """Integration test: verify full path from clean data to match cache."""
    # Simulate a small cleaned combined table
    cleaned = pd.DataFrame(
        [
            {
                "source": "lp",
                "record_id": 1,
                "investor": "Alice",
                "firm": "Blacstone",
                "email": "alice@some.com",
            },
            {
                "source": "lp",
                "record_id": 2,
                "investor": "Bob",
                "firm": "Goldmann Sacs",
                "email": "bob@other.com",
            },
        ]
    )
    write_table(TableName.COMBINED_CLEAN, cleaned)

    # Simulate canonical firm table
    canonical = pd.DataFrame(
        [
            {"firm": "Blackstone", "domain": "blackstone.com"},
            {"firm": "Goldman Sachs", "domain": "gs.com"},
        ]
    )
    write_table(TableName.CANONICAL_FIRMS, canonical)

    resolver = FirmResolver()

    # Manually resolve all firms from the cleaned table
    raw_firms = cleaned["firm"].dropna().unique().tolist()
    for firm in raw_firms:
        resolver.resolve(firm)

    # Validate the cache
    cache = read_table(TableName.FIRM_CACHE)
    assert set(cache["raw_firm"].values) == {"Blacstone", "Goldmann Sacs"}
    assert "Blackstone" in cache["canonical_firm"].values
    assert "Goldman Sachs" in cache["canonical_firm"].values

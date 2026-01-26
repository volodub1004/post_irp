import pandas as pd
import pytest
from fuzzlookup.cache_builder import (
    _add_typo,
    _generate_noisy_variants,
    populate_cache_with_noise,
)
from db.db import read_table, write_table
from db.models import TableName


def test_add_typo_generates_change():
    original = "Blackstone"
    typo = _add_typo(original)
    assert typo != original
    assert isinstance(typo, str)
    assert len(typo) >= 2  # ensure result isn't too short


def test_generate_noisy_variants_are_diverse():
    name = "Goldman Sachs"
    variants = _generate_noisy_variants(name)
    assert isinstance(variants, list)
    assert len(variants) >= 6
    assert name not in variants  # original not included
    assert all(isinstance(v, str) for v in variants)


@pytest.mark.integration
def test_populate_cache_with_noise(temp_db):
    # Populate canonical table
    canonical = pd.DataFrame(
        [
            {"firm": "Blackstone", "domain": "blackstone.com"},
            {"firm": "Goldman Sachs", "domain": "gs.com"},
        ]
    )
    write_table(TableName.CANONICAL_FIRMS, canonical)

    # Run noise population
    populate_cache_with_noise()

    # Read from cache and check shape
    df = read_table(TableName.FIRM_CACHE)
    assert not df.empty
    assert set(df.columns) == {"raw_firm", "canonical_firm", "domain", "match_score"}
    assert df["canonical_firm"].isin(["Blackstone", "Goldman Sachs"]).all()
    assert df["match_score"].between(0, 100).all()

import pytest
import pandas as pd
from pattern_mining.data_enrichment.add_name_characteristics import (
    _has_german_char,
    _has_nfkd_char,
    _has_nickname,
    _parse_name_structure,
    add_name_characteristics_flags,
)


def test_has_german_char():
    assert _has_german_char("Jürgen Müller") is True
    assert _has_german_char("Anna Bauer") is False


def test_has_nfkd_char():
    assert _has_nfkd_char("José Alvarez") is True
    assert _has_nfkd_char("John Smith") is False


def test_has_nickname():
    assert _has_nickname("Bill Gates") is True  # 'bill' in nickname map
    assert _has_nickname("George Gates") is False


def test_parse_name_structure():
    result = _parse_name_structure("John A. Smith")
    assert result == (False, True, False, False)

    result = _parse_name_structure("Jean-Luc Picard")
    assert result == (True, False, False, False)

    result = _parse_name_structure("Mary Anne Elizabeth O'Hara")
    assert result == (False, True, True, False)


@pytest.mark.integration
def test_add_name_characteristics_flags():
    df = pd.DataFrame(
        {
            "investor": [
                "Jürgen Müller",  # has_german_char, nfkd
                "José Antonio da Silva",  # nfkd, multiple last
                "Bill Smith",  # nickname
                "Mary Anne Elizabeth O'Hara",  # multiple middle
                "John Smith",  # plain
            ]
        }
    )

    result = add_name_characteristics_flags(df)

    # Check column presence
    expected_columns = [
        "has_german_char",
        "has_nfkd_normalized",
        "has_nickname",
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
    ]
    for col in expected_columns:
        assert col in result.columns

    # Spot check flags
    assert bool(result.loc[0, "has_german_char"]) is True
    assert bool(result.loc[1, "has_nfkd_normalized"]) is True
    assert bool(result.loc[2, "has_nickname"]) is True
    assert bool(result.loc[3, "has_multiple_middle_names"]) is True
    assert bool(result.loc[4, "has_middle_name"]) is False

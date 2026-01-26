import pytest
import pandas as pd
from pattern_mining.template_encoders import DomainTemplateEncoder


def test_normalize_firm_name():
    dte = DomainTemplateEncoder()
    assert dte._normalize_firm_name("Bain Capital, L.P.") == "bain capital lp"
    assert (
        dte._normalize_firm_name("J.P. Morgan / Asset Mgmt") == "jp morgan asset mgmt"
    )


def test_to_firm_sequence():
    dte = DomainTemplateEncoder()
    assert dte._to_firm_sequence("Goldman Sachs Inc.") == ["goldman", "sachs", "inc"]
    assert dte._to_firm_sequence("Électricité de France") == [
        "electricite",
        "de",
        "france",
    ]


def test_tokenize_firm_name_simple_match():
    dte = DomainTemplateEncoder()
    tokens = dte._tokenize_firm_name("Bain Capital", "baincap.com")
    assert tokens == ["0", "1_sub_3"]


def test_tokenize_firm_name_acronym():
    dte = DomainTemplateEncoder()
    tokens = dte._tokenize_firm_name("General Investments", "gi.com")
    assert tokens == ["0_sub_1", "1_sub_1"]


def test_tokenize_firm_name_separators():
    dte = DomainTemplateEncoder()
    tokens = dte._tokenize_firm_name("Blackstone Group", "blackstone-group.com")
    assert tokens == ["0", "-", "1"]


def test_tokenize_firm_name_unknown():
    dte = DomainTemplateEncoder()
    tokens = dte._tokenize_firm_name("Bridgewater Associates", "xyz123.com")
    assert tokens is None
    assert dte.stats["unk_tokens"] > 0


@pytest.mark.integration
def test_integration_encode_dataframe():
    dte = DomainTemplateEncoder()
    df = pd.DataFrame(
        {
            "firm": [
                "Bain Capital",
                "General Electric",
                "Blackstone Group",
                "Bridgewater Associates",
            ],
            "domain": ["baincap.com", "ge.com", "blackstone-group.com", "xyz123.com"],
        }
    )

    encoded = dte.encode_dataframe(df)

    # Assert encoded values are integers
    assert all(isinstance(seq, list) for seq in encoded)
    assert all(isinstance(tok, int) for seq in encoded for tok in seq)

    # Assert token_seq added to df where valid
    assert isinstance(df.at[0, "domain_token_seq"], tuple)
    assert df.at[3, "domain_token_seq"] is None

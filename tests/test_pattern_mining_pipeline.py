import pytest
import pandas as pd
from pattern_mining.pipeline import (
    _encode_email_templates,
    _mine_rules,
)
from pattern_mining import run
from db.models import TableName
from db.db import read_table, write_table, init_db
from etl.pipeline import _process_table
from etl.load import load_clean_data


# Mock classes and data
class MockETE:
    def __init__(self):
        self.stats = {"unk_sequences": []}

    def encode_dataframe(self, df):
        return [["first", ".", "last"] for _ in range(len(df))]

    def decode_token_sequence(self, seq):
        return seq


class MockMiner:
    def __init__(self, ete, spmf_jar_dir):
        pass

    def mine(self, token_seqs):
        return [
            {
                "lhs_tokens": ["first"],
                "rhs_tokens": ["last"],
                "support": 3,
                "confidence": 0.95,
            }
        ]


# Tests


def test_encode_email_templates():
    df = pd.DataFrame(
        {
            "email": ["john.smith@example.com", "j.smith@example.com"],
            "investor": ["John Smith", "John Smith"],
            "firm": ["Example Ltd", "Example Ltd"],
        }
    )

    ete, token_seqs = _encode_email_templates(df)

    assert isinstance(token_seqs, list)
    assert all(isinstance(seq, list) for seq in token_seqs)
    assert len(ete.stats["unk_sequences"]) <= len(df)


def test_mine_rules(monkeypatch):
    monkeypatch.setattr("pattern_mining.pipeline.TemplateRuleMiner", MockMiner)
    ete = MockETE()
    token_seqs = [["first", ".", "last"]]
    rules = _mine_rules(ete, token_seqs)

    assert isinstance(rules, list)
    assert all("lhs_tokens" in r for r in rules)
    assert all("rhs_tokens" in r for r in rules)


@pytest.mark.integration
def test_pattern_mining_pipeline_basic():
    # Init db
    init_db()
    # Create test input
    test_data = pd.DataFrame(
        {
            "investor": [
                "Alice Smith",
                "Bob Jones",
                "Carlos Vandermeer",
                "Diana Prince",
                "Edward Blake",
                "Frank Castle",
            ],
            "firm": [
                "FirmA",
                "FirmA",
                "FirmA",
                "FirmA",
                "FirmA",
                "FirmB",  # FirmA has 5 entries, FirmB has 1
            ],
            "email": [
                "a.smith@firma.com",
                None,
                "c.vandermeer@firma.com",
                "d.prince@firma.com",
                "e.blake@firma.com",
                "f.castle@firmb.com",  # 2 missing out of 5 for FirmA (40%)
            ],
            "tel": [
                "+1 555 123",
                "+1 555 456",
                "+1 555 789",
                "+1 555 000",
                "+1 555 111",
                "+1 555 222",
            ],
            "linkedin": [
                "https://linkedin.com/in/alice",
                "https://linkedin.com/in/bob",
                "https://linkedin.com/in/carlos",
                "https://linkedin.com/in/diana",
                "https://linkedin.com/in/edward",
                "https://linkedin.com/in/frank",
            ],
            "website": [
                "firma.com",
                "firma.com",
                "firma.com",
                "firma.com",
                "firma.com",
                "firmb.com",
            ],
        }
    )

    # Write raw to LP
    write_table(TableName.LP, test_data)

    # Clean test data
    cleaned = _process_table(TableName.LP)

    # Standardise and write to LP_CLEAN
    load_clean_data(TableName.LP_CLEAN, cleaned)

    # Run pipeline
    run()

    # Assert outputs
    cand = read_table(TableName.CANDIDATE_TEMPLATES)
    fmap = read_table(TableName.FIRM_TEMPLATE_MAP)
    lp_clean = read_table(TableName.LP_CLEAN)

    assert not cand.empty, "Expected candidate templates"
    assert not fmap.empty, "Expected firm-template map"
    assert "has_middle_name" in lp_clean.columns, "Missing enrichment in lp_clean"

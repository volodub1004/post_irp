import pytest
import pandas as pd
from pattern_mining import TemplateRuleMiner
from unittest.mock import Mock
from pattern_mining import EmailTemplateEncoder


def test_parse_rules_valid(tmp_path):
    # Use pytest's built-in tmp_path fixture to get a temp directory
    output_file = tmp_path / "test_rules.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    content = ["1 ==> 2 #SUP: 100 #CONF: 0.8", "1,3 ==> 2 #SUP: 50 #CONF: 0.6"]
    output_file.write_text("\n".join(content))

    miner = TemplateRuleMiner(
        encoder=Mock(), work_dir=str(tmp_path)
    )  # encoder not used here
    rules = miner._parse_rules(str(output_file))
    # Check rule count and structure
    assert len(rules) == 2
    assert rules[0]["lhs"] == [1]
    assert rules[0]["rhs"] == [2]
    assert rules[0]["support"] == 100
    assert rules[0]["confidence"] == 0.8


def test_write_input(tmp_path):
    miner = TemplateRuleMiner(encoder=Mock())
    miner.work_dir = tmp_path
    sequences = [[1, 2], [3, 4, 5]]
    path = miner._write_input(sequences)

    with open(path) as f:
        lines = f.read().splitlines()

    # Expected SPMF format for two sequences
    assert lines == ["1 -1 2 -1 -2", "3 -1 4 -1 5 -1 -2"]


@pytest.mark.integration
def test_full_pipeline(tmp_path):
    encoder = EmailTemplateEncoder()
    df = pd.DataFrame(
        {
            "email": ["john.smith@example.com", "j.smith@example.com"],
            "investor": ["John Smith", "John Smith"],
        }
    )
    # Tokenize the email local-parts
    token_seqs = encoder.encode_dataframe(df)

    # Run the TRuleGrowth miner on token sequences
    miner = TemplateRuleMiner(encoder=encoder)
    miner.work_dir = tmp_path
    rules = miner.mine(token_seqs, minsup=0.01, minconf=0.4, window_size=3)

    # Validate result structure
    assert len(rules) > 0
    for rule in rules:
        assert "lhs_tokens" in rule
        assert "rhs_tokens" in rule
        assert 0 <= rule["confidence"] <= 1

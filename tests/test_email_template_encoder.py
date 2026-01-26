import pandas as pd
import pytest
from pattern_mining import EmailTemplateEncoder


@pytest.mark.parametrize(
    "input_name,expected",
    [
        (
            "John Michael Smith",
            {
                "first": ["john"],
                "middle": ["michael"],
                "last": ["smith"],
            },
        ),
        (
            "Mary-Anne O'Neill-Jones",
            {
                "first": ["mary", "anne"],
                "middle": [],
                "last": ["oneill", "jones"],
            },
        ),
        (
            "Ali Bin Ahmad",
            {
                "first": ["ali"],
                "middle": [],
                "last": [
                    "bin",
                    "ahmad",
                ],  # Treats bin as composite surname for cultural reasons
            },
        ),
    ],
)
def test_decompose_name(input_name, expected):
    encoder = EmailTemplateEncoder()
    result = encoder._decompose_name(input_name)
    assert result == expected


@pytest.mark.parametrize(
    "local_part, full_name, expected_tokens",
    [
        # Standard case with middle name
        (
            "john.m.smith",
            "John Michael Smith",
            ["first_original_0", ".", "m_0", ".", "last_original_0"],
        ),
        # Case with multiple last name parts
        (
            "john.oneilljones",
            "John O'Neill Jones",
            ["first_original_0", ".", "middle_original_0", "last_original_0"],
        ),
        # Initials only
        ("jms", "John Michael Smith", ["f_0", "m_0", "l_0"]),
        # Unmatched junk
        (
            "abcxyz",
            "John Smith",
            None,
        ),  # None as it contains "UNK"
    ],
)
def test_tokenize_local_part(local_part, full_name, expected_tokens):
    encoder = EmailTemplateEncoder()
    name_parts = encoder._decompose_name(full_name)
    tokens = encoder._tokenize_local_part(local_part, name_parts)
    assert tokens == expected_tokens


def test_build_vocab_and_encode_token_sequences():
    encoder = EmailTemplateEncoder()

    # Given symbolic token sequences
    token_seqs = [["f", ".", "last"], ["first", ".", "last"], ["f", "m1", "l2"]]

    # Build vocab
    encoder._build_vocab(token_seqs)

    # Check vocab contents
    assert encoder.token_to_id["f"] > 0
    assert encoder.token_to_id["."] > 0
    assert encoder.token_to_id["last"] > 0
    assert encoder.id_to_token[encoder.token_to_id["first"]] == "first"

    # Check all tokens were assigned
    unique_tokens = set(t for seq in token_seqs for t in seq)
    assert set(encoder.token_to_id.keys()) == unique_tokens
    assert len(encoder.token_to_id) == len(encoder.id_to_token)

    # Encode
    encoded = encoder._encode_token_sequences(token_seqs)

    # Manually verify encoding is consistent
    for i, seq in enumerate(token_seqs):
        expected = [encoder.token_to_id[token] for token in seq]
        assert encoded[i] == expected


@pytest.mark.integration
def test_encode_dataframe_end_to_end():
    data = pd.DataFrame(
        {
            "investor": ["John Michael Smith", "Ali Bin Ahmad"],
            "email": ["john.m.smith@example.com", "ali.b.ahmad@domain.com"],
        }
    )

    encoder = EmailTemplateEncoder()
    encoded = encoder.encode_dataframe(data)

    # Check type and structure
    assert isinstance(encoded, list)
    assert all(isinstance(seq, list) for seq in encoded)
    assert all(isinstance(token_id, int) for seq in encoded for token_id in seq)

    # Check length matches input
    assert len(encoded) == 2

    # Check vocab contains expected semantic tokens
    tokens = list(encoder.token_to_id.keys())
    assert "first_original_0" in tokens
    assert "." in tokens
    assert any(t.startswith("m") for t in tokens)  # m0 or m1
    assert any(t.startswith("l") for t in tokens)  # l0 or l1

    # Check integer IDs are unique and start from 1
    ids = list(encoder.token_to_id.values())
    assert sorted(ids) == list(range(1, len(ids) + 1))

    # Check reverse mapping is correct
    for token, token_id in encoder.token_to_id.items():
        assert encoder.id_to_token[token_id] == token

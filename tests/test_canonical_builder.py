import pandas as pd
from db.models import TableName
from db.db import write_table, read_table
from fuzzlookup.canonical_builder import build_canonical_firms


def test_build_canonical_firms_basic(temp_db):
    # Setup dummy data for COMBINED_CLEAN
    df = pd.DataFrame(
        [
            {
                "source": "lp",
                "record_id": 1,
                "investor": "John Smith",
                "firm": "Blackstone",
                "email": "john@blackstone.com",
                "token_seq": "[test]",
            },
            {
                "source": "lp",
                "record_id": 2,
                "investor": "Jane Doe",
                "firm": "Blackstone",
                "email": "jane@gmail.com",
                "token_seq": "[test]",
            },
            {
                "source": "gp",
                "record_id": 3,
                "investor": "Sue Chan",
                "firm": "Sequoia Capital",
                "email": "sue@sequoiacap.com",
                "token_seq": "[test]",
            },
            {
                "source": "gp",
                "record_id": 4,
                "investor": "Bob Li",
                "firm": "Sequoia Capital",
                "email": "bob@yahoo.com",
                "token_seq": "[test]",
            },
        ]
    )

    write_table(TableName.COMBINED_CLEAN, df)

    # Call function
    build_canonical_firms()

    # Read output and assert results
    result = read_table(TableName.CANONICAL_FIRMS)
    result_set = set(
        tuple(row) for row in result[["firm", "domain"]].to_records(index=False)
    )

    expected_set = {
        ("blackstone", "blackstone.com"),
        ("sequoia capital", "sequoiacap.com"),
    }

    assert result_set == expected_set

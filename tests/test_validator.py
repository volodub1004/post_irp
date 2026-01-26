import pytest
import pandas as pd
from db.db import write_table
from db.models import TableName
from etl.load.validator import get_count, check_count


def test_count_initially_zero():
    # On fresh DB tables will be empty
    assert get_count(TableName.LP) == 0
    assert get_count(TableName.GP) == 0


def test_check_count_pass_and_raises():
    # Insert one LP record via write table
    data = {"investor": "Alice", "firm": "Acme", "email": "alice@acme.com"}
    df = pd.DataFrame([data])
    write_table(TableName.LP, df)
    # Count should be 1
    assert get_count(TableName.LP) == 1

    # Check count should pass with count is correct
    check_count(TableName.LP, 1)

    # And throw when not
    with pytest.raises(AssertionError):
        check_count(TableName.LP, 0)

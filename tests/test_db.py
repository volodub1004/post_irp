import sqlite3
import pandas as pd
from db.models import TableName, _TABLE_LOOKUP
from db.db import write_table, read_table


def test_init_db_creates_file(temp_db):
    # Use the SQLite master table to confirm tables exist
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    expected_tables = {"lp_raw", "gp_raw", "lp_clean", "gp_clean", "combined_clean"}
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    found = {row[0] for row in cur.fetchall()}
    assert expected_tables <= found
    conn.close()


def test_write_and_read_single_rows():
    # Insert two LP records
    rec1 = {"investor": "Alice", "firm": "Acme", "email": "a@ac.me"}
    df1 = pd.DataFrame([rec1])
    rec2 = {"investor": "Bob", "firm": "Beta", "email": "b@be.ta"}
    df2 = pd.DataFrame([rec2])

    write_table(TableName.LP, df1)
    write_table(TableName.LP, df2)

    # Read back, default limit=10, ordered by time_stamp DESC
    df = read_table(TableName.LP)
    # Bob should come first
    assert list(df["investor"]) == ["Bob", "Alice"]
    assert list(df["email"]) == ["b@be.ta", "a@ac.me"]


def test_read_with_projection_and_limit():
    # Insert three GP records
    for inv, firm, email in [
        ("X", "XCorp", "x@xc.orp"),
        ("Y", "YCorp", "y@yc.orp"),
        ("Z", "ZCorp", "z@zc.orp"),
    ]:
        rec = {"investor": inv, "firm": firm, "email": email}
        df = pd.DataFrame([rec])
        write_table(TableName.GP, df)

    # Read only columns investor & email, limit to 2
    df = read_table(TableName.GP, columns=["investor", "email"], limit=2)

    # Check columns
    assert list(df.columns) == ["investor", "email"]
    # Should return exactly 2 rows
    assert len(df) == 2


def test_upsert_overwrites_existing_record():
    # Insert initial record
    original = {"investor": "Charlie", "firm": "C Firm", "email": "c@cf.com"}
    df1 = pd.DataFrame([original])
    write_table(TableName.LP, df1)

    # Modify and re-insert with same primary key
    # First we read to get the auto-generated ID
    existing = read_table(TableName.LP, limit=1)
    row_id = int(existing.iloc[0]["id"])
    updated = {
        "id": row_id,  # must include primary key
        "investor": "Charlie",
        "firm": "C Firm Updated",
        "email": "new@cf.com",
    }
    df2 = pd.DataFrame([updated])
    write_table(TableName.LP, df2)  # This should perform an upsert

    # Read back and check the update was applied
    result = read_table(
        TableName.LP, filters=[_TABLE_LOOKUP[TableName.LP].c.id == row_id]
    )
    print("Result from filter query:", result.to_dict(orient="records"))
    assert result.iloc[0]["firm"] == "C Firm Updated"
    assert result.iloc[0]["email"] == "new@cf.com"


def test_upsert_combined_clean():
    record = {
        "source": "gp",
        "record_id": 999,
        "investor": "Dana",
        "firm": "Delta Group",
        "email": "dana@delta.com",
        "token_seq": "[test]",
    }
    df1 = pd.DataFrame([record])
    write_table(TableName.COMBINED_CLEAN, df1)

    # Modify email for same composite key
    updated = record.copy()
    updated["email"] = "dana@newdelta.com"
    df2 = pd.DataFrame([updated])
    write_table(TableName.COMBINED_CLEAN, df2)

    # Read back and verify overwrite
    df = read_table(
        TableName.COMBINED_CLEAN,
        filters=[
            _TABLE_LOOKUP[TableName.COMBINED_CLEAN].c.source == "gp",
            _TABLE_LOOKUP[TableName.COMBINED_CLEAN].c.record_id == 999,
        ],
    )
    assert df.iloc[0]["email"] == "dana@newdelta.com"

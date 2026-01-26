from sqlalchemy import select, func
from db.models import _TABLE_LOOKUP, get_engine, TableName


def get_count(table: TableName) -> int | None:
    """Function to get row count from SQL table

    Args:
        table (TableName): Table to get count from.
    Returns:
        int | None: Row count or none.
    """
    tbl = _TABLE_LOOKUP[table]
    # Get count from sql db.
    stmt = select(func.count()).select_from(tbl)
    with get_engine().connect() as conn:
        return conn.execute(stmt).scalar()


def check_count(table: TableName, expected_count: int) -> None:
    """Function to ensure SQL table has the expected
    number of rows.

    Args:
        table (TableName): The table to check.
        expected_count (int): The required count.

    Returns:
        None
    Raises:
        AssertionError: When count is not as expected.
        RunTimeError: If table count fetch fails.
    """
    # Get count from sql db.
    table_count = get_count(table)
    if table_count is None:
        raise RuntimeError(f"Unable to fetch count for {table}!")
    # Check counts
    if table_count > expected_count:
        raise AssertionError(
            f"Row count mismatch for {table.name}: "
            f"{expected_count} vs. {table_count}."
        )

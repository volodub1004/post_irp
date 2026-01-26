import os
import pandas as pd
from typing import List, Optional, Any, cast, Mapping, Sequence
import db.models as m
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select


# Database Helpers
# ------------------------------------------


# Initialization
def init_db() -> None:
    """Initialize the database by creating tables if they do not exist.

    Returns:
        None
    Raises:
        sqlite3.DatabaseError: If there are issues creating the tables.
    """
    # ensure directory
    parent = os.path.dirname(m.DB_FILE)
    os.makedirs(parent, exist_ok=True)

    m.create_tables()


# General Read Table function
def read_table(
    table: m.TableName,
    columns: Optional[List[str]] = None,
    filters: Optional[List[Any]] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Read data from a specified table with optional filters and limits.
    Args:
        table (TableName): The table to read from.
        columns (Optional[List[str]]): List of columns to select. If None, selects all.
        filters (Optional[List[Any]]): List of filter conditions.
        limit (Optional[int]): Maximum number of rows to return. Defaults to entire
            database.
    Returns:
        pd.DataFrame: DataFrame containing the queried data.
    """
    tbl = m._TABLE_LOOKUP[table]

    # Build base SELECT
    if columns is not None:
        cols = [tbl.c[col] for col in columns]
        stmt = select(*cols)
    else:
        stmt = select(tbl)

    # Apply filters if provided
    if filters:
        for condition in filters:
            stmt = stmt.where(condition)

    # Order and limit only if both columns exist
    ordering = []
    if "time_stamp" in tbl.c:
        ordering.append(tbl.c.time_stamp.desc())
    if "id" in tbl.c:
        ordering.append(tbl.c.id.desc())
    if ordering:
        stmt = stmt.order_by(*ordering)

    # Only apply limit if one is provided
    if limit is not None:
        stmt = stmt.limit(limit)

    # Execute into DataFrame
    with m.get_engine().connect() as conn:
        df = pd.read_sql(stmt, conn)

    print(f"Read {table.name} table from database!")
    return df


def replace_table(table: m.TableName, df: pd.DataFrame, silent: bool = True) -> int:
    """
    Completely replaces the contents of a SQL table with the provided DataFrame.

    Args:
        table (TableName): The table to replace.
        df (pd.DataFrame): New data to insert.

    Returns:
        int: Number of inserted records.

    Raises:
        ValueError: If the table is invalid or data is missing required fields.

    Note:
        CoPilot was used to assist implementing and debugging this function.
    """
    tbl = m._TABLE_LOOKUP.get(table)
    if tbl is None:
        raise ValueError(f"Unknown table: {table}")

    # Truncate the table
    with m.get_engine().begin() as conn:
        conn.execute(tbl.delete())
        if not silent:
            print(f"Cleared all rows from {table.name}")

    # Reuse existing insert logic
    return write_table(table, df, silent)


# General single-row insert function
def write_table(table: m.TableName, df: pd.DataFrame, silent: bool = True) -> int:
    """Bulk insert a pandas DataFrame into the given SQLAlchemy table.

    Args:
      table (m.TableName):  Which TableName to write to.
      df (DataFrame):       A dict mapping column names to
                            values for one row.

    Returns:
        int: number of written records

    Raises:
      ValueError: If table could not be resolved or pandas
                  dataframe columns do not match required.

    Note:
        CoPilot was used to assist debugging this method, especially as SQL table
        definitions changed.
    """
    # Resolve the table from the lookup
    tbl = m._TABLE_LOOKUP.get(table)
    if tbl is None:
        raise ValueError(f"Unknown table: {table}")

    # Ensure only valid columns are provided
    valid_cols = set(tbl.c.keys())
    df_cols = set(df.keys())
    extra = df_cols - valid_cols
    if extra:
        raise ValueError(f"DataFrame contains invalid columns: {extra}")

    # Ensure required non-null columns are present
    required = {
        name
        for name, col in tbl.c.items()
        if not col.nullable
        and not col.primary_key
        and col.default is None
        and col.server_default is None
    }
    missing = required - df_cols
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Convert DataFrame to list-of-dicts and bulk insert
    records = df.to_dict(orient="records")

    # Find all primary key rows
    pk_cols = [col.name for col in tbl.primary_key.columns]

    def has_all_pks(row):
        return all(pk in row and row[pk] is not None for pk in pk_cols)

    # Find records with and without primary keys
    records_with_pk = [r for r in records if has_all_pks(r)]
    records_without_pk = [r for r in records if not has_all_pks(r)]

    with m.get_engine().begin() as conn:
        # If record has primary key, do upsert
        if records_with_pk:
            # Update on conflict of primary key
            stmt = sqlite_insert(tbl).on_conflict_do_update(
                index_elements=pk_cols,
                set_={
                    col: getattr(sqlite_insert(tbl).excluded, col)
                    for col in df_cols
                    if col not in pk_cols
                },
            )
            conn.execute(stmt, cast(Sequence[Mapping[str, Any]], records_with_pk))

        if records_without_pk:
            if pk_cols:  # must be autoincrementable
                conn.execute(
                    tbl.insert(), cast(Sequence[Mapping[str, Any]], records_without_pk)
                )
            else:
                raise ValueError(
                    f"Cannot insert records without full primary keys into table {table.name}"
                )
    if not silent:
        print(
            f"{len(records_with_pk)} upserted {len(records_without_pk)} inserted into {table.name}"
        )
    return len(records_with_pk) + len(records_without_pk)

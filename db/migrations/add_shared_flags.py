from sqlalchemy import text
from sqlalchemy import create_engine
from db.models import DB_FILE, metadata

# Get SQL engine
engine = create_engine(f"sqlite:///{DB_FILE}")


def _add_column_if_missing(
    table_name: str, column_name: str, column_type: str, silent: bool = True
) -> None:
    """
    Adds a new column to a SQLite table if it does not already exist.

    Args:
        table_name (str): The name of the table to modify.
        column_name (str): The name of the new column to add.
        column_type (str): The SQL data type for the new column (e.g., "BOOLEAN").

    Returns:
        None
    """
    with engine.connect() as conn:
        existing_cols = conn.execute(
            text(f"PRAGMA table_info({table_name})")
        ).fetchall()
        column_names = [col[1] for col in existing_cols]

        if column_name not in column_names:
            if not silent:
                print(f"Adding column '{column_name}' to '{table_name}'")
            conn.execute(
                text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT 0"
                )
            )
        else:
            if not silent:
                print(f"Column '{column_name}' already exists in '{table_name}'.")


def add_flags() -> None:
    """
    Executes a schema migration to add email/name structure flags to
    `lp_clean`, `gp_clean`, and `combined_clean` tables if they don't already exist.

    Returns:
        None
    """
    columns_to_add = [
        "is_shared_infra",
        "firm_is_multi_domain",
        "has_german_char",
        "has_nfkd_normalized",
        "has_nickname",
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
    ]

    # Add each flag to each table
    for table in ["lp_clean", "gp_clean", "combined_clean"]:
        # Add token_seq to clean
        _add_column_if_missing(table, "token_seq", "JSON")
        for col in columns_to_add:
            _add_column_if_missing(table, col, "BOOLEAN")

    # Refresh metadata to sync with DB
    metadata.clear()
    metadata.reflect(bind=engine)


if __name__ == "__main__":
    add_flags()

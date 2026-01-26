from sqlalchemy import text, create_engine
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


def add_features() -> None:
    """
    Add newly add feature fields to feature matrix.
    """
    # Feature matrix additions
    feature_matrix_cols = [
        ("template_firm_support_count", "INTEGER"),
        ("template_firm_coverage_pct", "FLOAT"),
        ("template_is_top_template", "BOOLEAN"),
        ("template_name_characteristic_clash", "BOOLEAN"),
    ]
    for col, dtype in feature_matrix_cols:
        _add_column_if_missing("feature_matrix", col, dtype)

    # Refresh metadata to sync with DB
    metadata.clear()
    metadata.reflect(bind=engine)


if __name__ == "__main__":
    add_features()

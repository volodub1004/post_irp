from db.db import read_table
from db.models import TableName
from etl.transform.standardise import standardise_table
from etl.transform.validate import validate_table


def transform_table(table: TableName) -> dict:
    """Runs the full transformation pipeline on raw investor data.

    This applies; Standardization - text normalization + regex cleanup;
    Validation - adds flag columns and returns issue lists.

    Args:
        table (TableName): Table to transform.

    Returns:
        dict: {
            "final_df": Cleaned, and validated,
            "validation": Result of `validate_table(df)`,
        }
    Raises:
        ValueError: If provided table is not valid raw table.
    """
    if table is not TableName.GP and table is not TableName.LP:
        raise ValueError("Non raw table selected for cleaning.")

    # Get table data
    df = read_table(table=table)

    # Standardise fields
    df = standardise_table(df)

    # Validate key fields
    validation = validate_table(df)

    return {"final_df": df, "validation": validation}

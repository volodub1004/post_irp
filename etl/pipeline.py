import pandas as pd
from db.db import init_db
from db.migrations import run_all_migrations
from db.models import TableName
from etl.load import load_raw_data, load_clean_data
from etl.transform import transform_table
from etl.transform.cleaning import (
    drop_rows_missing_emails,
    drop_emails_with_invalid_local,
)
from etl.transform.validate import flag_shared_domain, flag_multi_domain_firms


def _process_table(table: TableName, is_gp: bool = False) -> pd.DataFrame:
    """Processes and cleans a single contact table (LP or GP).

    This function:
      1. Transforms the raw table using domain-specific logic.
      2. Drops rows with missing or structurally invalid emails.
      3. Extracts ambiguous duplicates and identifies valid career move records.
      4. Reinserts these duplicates into the clean dataset.
      5. Flags records with shared infrastructure email domains (`is_shared_infra`).
      6. Flags firms using multiple email domains (`firm_is_multi_domain`).

    Args:
        table (TableName): Enum value representing the table to process (e.g., TableName.LP).
        is_gp (bool): Set to True if the table is from the GP dataset (affects grouping logic
        for deduplication).

    Returns:
        pd.DataFrame: The cleaned and enriched DataFrame ready to be written to the database.
    """
    # Transform and extract base cleaned data
    transformed = transform_table(table)
    clean_df = transformed["final_df"]

    # Clean step
    clean_df = drop_rows_missing_emails(clean_df)
    clean_df = drop_emails_with_invalid_local(clean_df)

    # Flagging
    clean_df = flag_shared_domain(clean_df)
    clean_df = flag_multi_domain_firms(clean_df)

    return clean_df


def run(do_gp_too: bool = True) -> bool:
    """Executes the full data preprocessing pipeline for LP (and optionally GP) datasets.

    This function performs the following steps:
      1. Initializes the SQL database schema.
      2. Loads raw LP data into the database (and optionally GP data).
      3. Transforms and cleans the data:
         - Drops rows with missing or malformed emails.
         - Identifies and reintegrates career move-style ambiguous duplicates.
         - Flags records with shared email infrastructure domains and multi-domain firms.
      4. Writes the cleaned datasets back to the database (LP_CLEAN and optionally GP_CLEAN).

    All cleaned data will also be written to the COMBINED_CLEAN table regardless if gp option
    selected.

    Args:
        do_gp_too (bool): Whether to also process the GP dataset alongside LP.

    Returns:
        bool: True if the pipeline completes successfully, False if any exception occurs.
    """
    try:
        # Setup DB and load raw data
        init_db()
        load_raw_data(TableName.LP)
        if do_gp_too:
            load_raw_data(TableName.GP)

        # Process LP table
        clean_lp = _process_table(TableName.LP)

        # Process GP table if needed
        if do_gp_too:
            clean_gp = _process_table(TableName.GP, is_gp=True)

        # Migrate to new schema
        run_all_migrations()

        # Write results
        load_clean_data(TableName.LP_CLEAN, clean_lp)
        if do_gp_too:
            load_clean_data(TableName.GP_CLEAN, clean_gp)

        return True

    except Exception as ex:
        print(f"[ERROR] Preprocessing failed: {ex}")
        return False


if __name__ == "__main__":
    run(do_gp_too=True)

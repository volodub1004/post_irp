import pandas as pd
from etl.extract.extractor import extract_excel_data
from db.db import write_table, replace_table
from db.models import TableName


def _load_raw_data_from_sheet(
    sheet_name: str, table: TableName, column_map: dict, drop_columns: list
) -> int:
    """Load raw data into the database from an Excel sheet.

    Args:
        sheet_name (str): Excel sheet to read from.
        table (TableName): SQL table to right to.
        column_map (dict): Maps CSV columns to SQL table columns.
        drop_columns (list): CSV columns to drop.

    Returns:
        int: Number of rows written to db.
    Raises:
        ValueError: If columns are malformed.
    """
    # Read CSV data
    df = extract_excel_data(sheet_name)
    if df.empty:
        raise ValueError(f"No data found in sheet: {sheet_name}")

    # Rename and drop columns
    df = df.rename(columns=column_map, errors="ignore")
    df = df.drop(columns=drop_columns, errors="ignore")

    # Time stamp
    df = df.assign(source_file=sheet_name, time_stamp=pd.Timestamp.now())

    # Write to table
    try:
        replace_table(table, df)
    except KeyError as e:
        raise ValueError(f"Missing expected column in {sheet_name}: {e}")

    print(f"Write to {table.name} complete!")
    return len(df)


def __raw_lp_data() -> int:
    """Load raw LP data into the database from an Excel sheet.

    Returns:
        int: Number of rows written to db.
    Raises:
        ValueError: If columns are malformed.
    """
    return _load_raw_data_from_sheet(
        sheet_name="LP Contact Data",
        table=TableName.LP,
        column_map={
            "INVESTOR": "firm",
            "FIRM TYPE": "firm_type",
            "TITLE": "title",
            "NAME": "investor",
            "ALTERNATIVE NAME": "alternative_name",
            "ROLE": "role",
            "JOB TITLE": "job_title",
            "ASSET CLASS": "asset_class",
            "EMAIL": "email",
            "TEL": "tel",
            "CITY": "city",
            "STATE": "state",
            "COUNTRY": "country",
            "ZIP CODE": "zip_code",
            "LINKEDIN": "linkedin",
            "REGION": "region",
            "ADDRESS": "address",
            "WEBSITE": "website",
            "GENERAL EMAIL": "general_email",
        },
        drop_columns=[
            "CITY.1",
            "TEL.1",
            "STATE/COUNTY",
            "ZIP CODE.1",
            "COUNTRY/TERRITORY",
        ],
    )


def __raw_gp_data() -> int:
    """Load raw GP data into the database from an Excel sheet.

    Returns:
        int: Number of rows written to db.
    Raises:
        ValueError: If columns are malformed.
    """
    return _load_raw_data_from_sheet(
        sheet_name="GP Contact Data",
        table=TableName.GP,
        column_map={
            "FUND MANAGER": "firm",
            "FIRM TYPE": "firm_type",
            "TITLE": "title",
            "NAME": "investor",
            "JOB TITLE": "job_title",
            "ASSET CLASS": "asset_class",
            "EMAIL": "email",
            "TEL": "tel",
            "CITY": "city",
            "STATE": "state",
            "COUNTRY/TERRITORY": "country",
            "ZIP CODE": "zip_code",
            "LINKEDIN": "linkedin",
            "REGION": "region",
            "ADDRESS": "address",
            "WEBSITE": "website",
            "GENERAL EMAIL": "general_email",
        },
        drop_columns=["CITY.1", "TEL.1", "STATE/COUNTY", "ZIP CODE.1", "COUNTRY"],
    )


def load_raw_data(table: TableName) -> None:
    """Load raw data into the database from an Excel sheet.

    Args:
        table (TableName): The table to load data into.

    Returns:
        None
    Raises:
        ValueError: If none raw table selected.
    """
    # Load correct table data
    if table is TableName.LP:
        write_count = __raw_lp_data()
    elif table is TableName.GP:
        write_count = __raw_gp_data()
    else:
        # Raise exception for incorrect template
        raise ValueError("Non conforming table type selected!")

    # Validate row counts and data types
    print(f"Written {write_count} records to {table.name}")


def __rename_clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename cleaned columns to match DB schema."""
    return df.rename(
        columns={
            "INVESTOR": "investor",
            "FIRM TYPE": "firm_type",
            "TITLE": "title",
            "NAME": "investor",
            "ALTERNATIVE NAME": "alternative_name",
            "ROLE": "role",
            "JOB TITLE": "job_title",
            "ASSET CLASS": "asset_class",
            "EMAIL": "email",
            "TEL": "tel",
            "CITY": "city",
            "STATE": "state",
            "COUNTRY": "country",
            "ZIP CODE": "zip_code",
            "LINKEDIN": "linkedin",
            "REGION": "region",
            "ADDRESS": "address",
            "WEBSITE": "website",
            "GENERAL EMAIL": "general_email",
            "SOURCE FILE": "source_file",
            "TIMESTAMP": "time_stamp",
        }
    )


def load_clean_data(table: TableName, df: pd.DataFrame, replace: bool = False) -> None:
    """Load cleaned LP or GP data into the clean table and combined_clean.

    Args:
        table (TableName): TableName.LP_CLEAN or TableName.GP_CLEAN.
        df (pd.DataFrame): Cleaned DataFrame.

    Raises:
        ValueError: If invalid table or missing required columns.
    """
    if table not in {TableName.LP_CLEAN, TableName.GP_CLEAN, TableName.COMBINED_CLEAN}:
        raise ValueError("Only LP_CLEAN and GP_CLEAN are supported.")

    if replace:
        write_func = replace_table
    else:
        write_func = write_table

    df = __rename_clean_columns(df).copy()
    df["time_stamp"] = df.get("time_stamp", pd.Timestamp.now())

    required = {"id", "investor", "firm", "email"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Prepare and write to combined_clean
    combined_df = df.copy()

    if table is not TableName.COMBINED_CLEAN:
        # Write to the clean table
        write_count = write_func(table, df)
        print(f"Wrote {write_count} rows to {table.name}")

        # Set source and record ID
        combined_df["source"] = "LP" if table == TableName.LP_CLEAN else "GP"
        combined_df = combined_df.rename(columns={"id": "record_id"})
        combined_cols = [
            "source",
            "record_id",
            "investor",
            "firm_type",
            "title",
            "firm",
            "alternative_name",
            "role",
            "job_title",
            "asset_class",
            "email",
            "tel",
            "city",
            "state",
            "country",
            "zip_code",
            "linkedin",
            "region",
            "address",
            "website",
            "general_email",
            "source_file",
            "is_shared_infra",
            "firm_is_multi_domain",
            "has_german_char",
            "has_nfkd_normalized",
            "has_nickname",
            "has_multiple_first_names",
            "has_middle_name",
            "has_multiple_middle_names",
            "has_multiple_last_names",
            "token_seq",
            "time_stamp",
        ]
        # Only keep columns that actually exist in the DataFrame
        existing_cols = [col for col in combined_cols if col in combined_df.columns]
        combined_df = combined_df[existing_cols]

    write_count = write_func(TableName.COMBINED_CLEAN, combined_df)
    print(f"Also wrote {len(combined_df)} rows to COMBINED_CLEAN")

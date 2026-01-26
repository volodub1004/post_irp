import pandas as pd


def _normalise_table(df: pd.DataFrame) -> pd.DataFrame:
    """Normailses table data.

    Lower case normalises and trims all text fields
    in a pandas DataFrame.

    Args:
        df (pd.DataFrame): Data to normalise

    Returns:
        pd.DataFrame: Normalised Data
    """
    df = df.copy()

    # Normalise all text fields
    object_cols = df.select_dtypes(include="object").columns
    df[object_cols] = df[object_cols].apply(
        lambda col: col.where(col.isna(), col.str.strip().str.lower())
    )

    print("Table Normalisation Complete!")
    return df


def _regex_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans text fields using regex-based rules.

    Applies generic cleaning to all string fields to remove trailing punctuation,
    collapse multiple spaces, and strip common paste artifacts. Also applies
    specific rules to clean URL fields by removing protocol and tracking
    parameters, and removes non-digit characters from telephone numbers.

    Args:
        df (pd.DataFrame): Input DataFrame containing raw text fields.

    Returns:
        pd.DataFrame: Cleaned DataFrame with normalized text fields.
    Raises:
        ValueError: If the required column is not present in the input DataFrame.
    """
    required = ["linkedin", "website", "tel"]
    for req in required:
        if req not in df.columns:
            raise ValueError(f"Input DataFrame must contain an {req} column.")

    df = df.copy()

    # Define vectorized cleaning helpers
    def _clean_generic(series: pd.Series) -> pd.Series:
        mask = series.notna()
        cleaned = series[mask].astype(str).str.strip().str.lower()
        cleaned = (
            cleaned.str.replace(r"[.,;:!?)}\]]+$", "", regex=True)  # Trailing punc
            .str.replace(r"\s{2,}", " ", regex=True)  # Multiple spaces
            .str.replace(r"[\"'<>]", "", regex=True)  # Common paste noise
        )
        return series.where(~mask, cleaned)

    def _clean_url(series: pd.Series) -> pd.Series:
        mask = series.notna()
        cleaned = series[mask].astype(str).str.strip().str.lower()
        cleaned = (
            cleaned.str.replace(r"^(https?://)", "", regex=True)  # Remove http/https
            .str.replace(r"[\"'<>]", "", regex=True)  # Remove junk characters
            .str.replace(r"[\?#].*$", "", regex=True)  # Remove query string or fragment
        )
        return series.where(~mask, cleaned)

    def _clean_tel(series: pd.Series) -> pd.Series:
        mask = series.notna()
        cleaned = series[mask].astype(str).str.replace(r"\D", "", regex=True)
        return series.where(~mask, cleaned)  # Keep only digits

    # Clean all generic text fields
    object_cols = df.select_dtypes(include="object").columns
    df[object_cols] = df[object_cols].apply(_clean_generic)

    # Field-specific logic
    df["linkedin"] = _clean_url(df["linkedin"])
    df["website"] = _clean_url(df["website"])
    df["tel"] = _clean_tel(df["tel"])

    print("Table Regex-Cleaning Complete!")
    return df


def _drop_bad_investor_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows with missing, empty, or invalid investor names.

    This function filters out rows where the `investor` field is null, an empty string,
    or contains suspicious placeholder characters such as question marks.

    Args:
        df (pd.DataFrame): DataFrame containing an 'investor' column.

    Returns:
        pd.DataFrame: Filtered DataFrame with bad investor rows removed.

    Raises:
        ValueError: If the 'investor' column is not present in the input DataFrame.
    """
    if "investor" not in df.columns:
        raise ValueError("Missing required 'investor' column.")

    initial_count = len(df)

    # Strip white space and noise
    mask = (
        df["investor"].notna()
        & df["investor"].str.strip().ne("")
        & ~df["investor"].str.contains(r"\?", regex=True, na=False)
    )

    # Remove
    df = df[mask]
    removed = initial_count - len(df)
    print(f"Removed {removed} bad investor rows!")

    return df


def standardise_table(df: pd.DataFrame) -> pd.DataFrame:
    """Standardises string entires in a given table.

    Trims and lowercase normalises all string fields, then
    calls functions for regex based cleaning.

    Args:
        df (pd.DataFrame): Table to standardise.

    Returns:
        pd.DataFrame: Standardised data.
    """
    # Normalise table
    df = _normalise_table(df)

    # Regex clean
    df = _regex_cleaning(df)

    # Remove bad investor names
    df = _drop_bad_investor_names(df)

    print("Table Standardisation Complete!")
    return df

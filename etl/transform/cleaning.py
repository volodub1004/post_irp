import re
import pandas as pd


def drop_rows_missing_emails(df: pd.DataFrame) -> pd.DataFrame:
    """Drops rows with missing `email` fields.

    Part of aggressive cleaning process.

    Args:
        df (pd.DataFrame): DataFrame to clean.
    Returns:
        pd.DataFrame: Cleaned DataFrame
    Raises:
        ValueError: If `email` field does not exist.
    """
    if "email" not in df.columns:
        raise ValueError("Cannot clean data without necessary fields!")

    return df[df["email"].notnull()].copy()


def drop_emails_with_invalid_local(df: pd.DataFrame) -> pd.DataFrame:
    """Drops rows where the email's local-part contains non-a-z characters.

    Args:
        df (pd.DataFrame): DataFrame with 'email' column.

    Returns:
        pd.DataFrame: Filtered DataFrame with suspicious rows dropped.

    Raises:
        ValueError: If required columns are missing.
    """
    # Validate columns
    required = {"email"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    # Valid local parts only (before @)
    valid_local_pattern = re.compile(r"^[a-z0-9._-]+$", re.IGNORECASE)

    # Helper for apply
    def is_valid(email: str) -> bool:
        # Needs an domain
        if not isinstance(email, str) or "@" not in email:
            return False
        local = email.split("@")[0]
        return bool(valid_local_pattern.match(local))

    # Remove
    mask = df["email"].apply(is_valid)
    removed = (~mask).sum()
    print(f"Removed {removed} emails with invalid local-part characters.")

    return df[mask].copy()

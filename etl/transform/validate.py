import pandas as pd
from typing import List


def flag_shared_domain(df_to_flag: pd.DataFrame) -> pd.DataFrame:
    """Flags rows that belong to shared email infrastructure domains (used by multiple firms).

    Adds a boolean 'is_shared_infra' column to the returned DataFrame.

    Args:
        df_to_flag (pd.DataFrame): DataFrame with at least 'email' and 'firm' columns.

    Returns:
        pd.DataFrame: Copy of the input DataFrame with 'is_shared_infra' column added.

    Raises:
    ValueError: If "email" or "firm" column does not exist in given
            DataFrame.
    """
    required = ["email", "firm"]
    for req in required:
        if req not in df_to_flag.columns:
            raise ValueError(f"Missing required {req} field!")

    df = df_to_flag.copy()

    # Extract domain
    df["domain"] = df["email"].str.extract("@(.*)$")[0].str.lower()

    # Count firms per domain
    domain_firm_counts = (
        df.groupby("domain")["firm"].nunique().sort_values(ascending=False)
    )
    shared_domains = domain_firm_counts[domain_firm_counts > 1]

    # Flag shared infrastructure domains
    df["is_shared_infra"] = df["domain"].isin(shared_domains.index)

    return df.drop(columns=["domain"])


def flag_multi_domain_firms(df_to_flag: pd.DataFrame) -> pd.DataFrame:
    """
    Flags rows belonging to firms that use multiple email domains.

    Adds a boolean 'firm_is_multi_domain' column to the returned DataFrame.

    Args:
        df_to_flag (pd.DataFrame): DataFrame with at least 'email' and 'firm' columns.

    Returns:
        pd.DataFrame: Copy of the input DataFrame with 'firm_is_multi_domain' column added.

    Raises:
    ValueError: If "email" or "firm" column does not exist in given
            DataFrame.
    """
    required = ["email", "firm"]
    for req in required:
        if req not in df_to_flag.columns:
            raise ValueError(f"Missing required {req} field!")

    df = df_to_flag.copy()

    # Extract domain
    df["domain"] = df["email"].str.extract("@(.*)$")[0].str.lower()

    # Count domains per firm
    firm_domain_counts = (
        df.groupby("firm")["domain"].nunique().sort_values(ascending=False)
    )
    multi_domain_firms = firm_domain_counts[firm_domain_counts > 1]

    # Flag firms using multiple domains
    df["firm_is_multi_domain"] = df["firm"].isin(multi_domain_firms.index)

    return df.drop(columns=["domain"])


def _validate_email_field(df: pd.DataFrame) -> List[int]:
    """Validates email fields in table DataFrame.

    Checks that given emails are not missing, are valid
    and are within the expected length range deduced from
    preliminary EDA.

    Args:
        df (pd.DataFrame): Standardised table.

    Returns:
        list: Of invalid Row IDs.

    Raises:
        ValueError: If "email" column does not exist in given
            DataFrame.
    """
    if "email" not in df.columns:
        raise ValueError("Cannot Validate `email` Field Without 'email' Column!")

    email = df["email"]

    # Check whether email is missing
    is_missing = email.isna()

    # Pre-filter non-missing only once
    non_missing = email[~is_missing]

    # Length check
    is_invalid_length = non_missing.str.len().lt(10) | non_missing.str.len().gt(45)

    # Format check
    email_regex = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
    is_invalid_format = ~non_missing.str.match(email_regex)

    # Combine
    bad_index = is_missing[is_missing].index.union(
        non_missing[is_invalid_length | is_invalid_format].index
    )

    print(f"{is_invalid_length.sum()} invalid email lengths found!")
    print(f"{is_missing.sum()} missing emails!")
    print(f"{is_invalid_format.sum()} invalid email formats found!")

    return df.loc[bad_index, "id"].tolist()


def _validate_linkedin(df: pd.DataFrame) -> List[int]:
    """Returns a list of row IDs with invalid LinkedIn formats.

    Args:
        df (pd.DataFrame): Standardised table.

    Returns:
        list: Of invalid Row IDs.

    Raises:
        ValueError: If "linkedin" column does not exist in given
            DataFrame.
    """
    if "linkedin" not in df.columns:
        raise ValueError("Cannot Validate `linkedin` Field Without 'linkedin' Column!")

    # Check whether LinkedIn is missing
    is_missing = df["linkedin"].isna()

    # Regex rules to validate LinkedIn url
    is_invalid = (
        ~df["linkedin"].str.contains(r"linkedin\.com/in/", na=False) & ~is_missing
    )

    print(f"{is_invalid.sum()} invalid LinkedIns found!")
    print(f"{is_missing.sum()} missing LinkedIns!")

    return df[is_invalid | is_missing]["id"].tolist()


def _validate_firm_names(df: pd.DataFrame) -> List[int]:
    """Returns a list of row IDs with invalid firm names.

    Checks whether firm name is missing or is outside
    expected length range. See EDA for more details on this.

    Args:
        df (pd.DataFrame): Standardised table.

    Returns:
        list: Of invalid Row IDs.

    Raises:
        ValueError: If "firm" column does not exist in given
            DataFrame.
    """
    if "firm" not in df.columns:
        raise ValueError("Cannot Validate `firm` Field Without 'firm' Column!")

    # Check whether firm is missing
    is_missing = df["firm"].isna()

    # Check length is within valid length (see EDA for notes on this)
    is_invalid_length = (
        ~df["firm"].str.len().between(4, 60, inclusive="both") & ~is_missing
    )

    print(f"{is_invalid_length.sum()} invalid firm lengths found!")
    print(f"{is_missing.sum()} missing firms!")

    return df[is_invalid_length | is_missing]["id"].tolist()


def _validate_investor_names(df: pd.DataFrame) -> List[int]:
    """Returns a list of row IDs with invalid investor names.

    Checks whether investor name is missing or is outside
    expected length range. See EDA for more details on this.

    Args:
        df (pd.DataFrame): Standardised table.

    Returns:
        list: Of invalid Row IDs.

    Raises:
        ValueError: If "investor" column does not exist in given
            DataFrame.
    """
    if "investor" not in df.columns:
        raise ValueError("Cannot Validate `investor` Field Without 'investor' Column!")

    # Check whether investor is missing
    is_missing = df["investor"].isna()

    # Check length is within valid length (see EDA for notes on this)
    is_invalid_length = (
        ~df["investor"].str.len().between(8, 18, inclusive="both") & ~is_missing
    )

    print(f"{is_invalid_length.sum()} invalid investor lengths found!")
    print(f"{is_missing.sum()} missing investors!")

    return df[is_invalid_length | is_missing]["id"].tolist()


def _find_missing_email_linkedin_pairs(df: pd.DataFrame) -> List[int]:
    """Returns a list of row IDs with missing LinkedIn and email fields.

    Checks whether LinkedIn and email fields are missing for the same
    row and collects said rowIDs to flag for human review later.

    Args:
        df (pd.DataFrame): Standardised table.

    Returns:
        list: Of invalid Row IDs.

    Raises:
        ValueError: If "linkedin" or "email" columns do not exist in
            given DataFrame.
    """
    if "linkedin" not in df.columns or "email" not in df.columns:
        raise ValueError("Missing neccessary fields!")

    # Check whether investor is missing
    is_missing = df["linkedin"].isna() & df["email"].isna()

    print(f"{is_missing.sum()} missing linkedin and email pairs!")

    return df[is_missing]["id"].tolist()


def validate_table(df: pd.DataFrame) -> dict:
    """Validates key fields in a cleaned investor contact dataset.

    Applies rule-based validation checks on email structure,
    LinkedIn profile links, investor and firm name lengths,
    and email length.
    Returns a dictionary containing:
      - the original DataFrame with `_valid` columns added
      - filtered DataFrames of commonly flagged issues

    Args:
        df (pd.DataFrame): Standardised and cleaned input data.

    Returns:
        dict: {
            "invalid_email": Rows with invalid, missing or outside expected length range,
            "invalid_linkedin": Rows with invalid LinkedIn URLs,
            "invalid_firm": Rows with empty or outside expected length range,
            "invalid_investor": Rows with missing investor names outside expected length range,
            "missing_email_and_linkedin": Rows missing both email and LinkedIn,
        }
    """
    df = df.copy()

    # Flag invalid emails
    invalid_email = _validate_email_field(df)

    # Flag invalid LinkedIn fields
    invalid_linkedin = _validate_linkedin(df)

    # Flag invalid firm fields
    invalid_firm = _validate_firm_names(df)

    # Flag invalid investor names
    invalid_investor = _validate_investor_names(df)

    # Flag missing email and LinkedIn pairs
    missing_email_and_linkedin = _find_missing_email_linkedin_pairs(df)

    return {
        "invalid_email": invalid_email,
        "invalid_linkedin": invalid_linkedin,
        "invalid_firm": invalid_firm,
        "invalid_investor": invalid_investor,
        "missing_email_and_linkedin": missing_email_and_linkedin,
    }

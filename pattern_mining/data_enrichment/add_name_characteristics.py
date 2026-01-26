import pandas as pd
import unicodedata
from nameparser import HumanName
from pattern_mining.template_encoders.reverse_nickname_map import NICKNAME_MAP
from pattern_mining.template_encoders.email_template_encoder import GERMAN_ASCII_MAP
from typing import Tuple

# Get set of all names int he nickname map
ALL_NAMES_WITH_NICKNAMES = set(NICKNAME_MAP.keys())


def _has_german_char(name: str) -> bool:
    """
    Check if the input name contains any German-specific characters.

    Args:
        name (str): The full name string to check.

    Returns:
        bool: True if the name contains any characters from GERMAN_ASCII_MAP, else False.
    """
    # Check if any german char appears in the name
    return any(char in name.lower() for char in GERMAN_ASCII_MAP)


def _has_nfkd_char(name: str) -> bool:
    """
    Check if NFKD normalization alters the input name.

    Args:
        name (str): The full name string to normalize.

    Returns:
        bool: True if the normalized string differs from the original, else False.
    """
    # Check the difference between normalized and original name
    norm = (
        unicodedata.normalize("NFKD", name.lower())
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    return norm != name.lower()


def _has_nickname(name: str) -> bool:
    """
    Check if the name contains any known formal names that have nickname variants.

    Args:
        name (str): The full name string to inspect.

    Returns:
        bool: True if any formal name from NICKNAME_MAP is found in the input string.
    """
    # Check whether or not name has associated nickname
    return any(char in name.lower() for char in ALL_NAMES_WITH_NICKNAMES)


def _parse_name_structure(name: str) -> Tuple[bool, bool, bool, bool]:
    """
    Parse the structural composition of a full name.

    Args:
        name (str): The full name string to parse using HumanName.

    Returns:
        Tuple[bool, bool, bool, bool]: A tuple of flags:
            - has_multiple_first_names (bool)
            - has_middle_name (bool)
            - has_multiple_middle_names (bool)
            - has_multiple_last_names (bool)
    """
    # Parse name into pars
    parsed = HumanName(name)
    first_parts = parsed.first.lower().replace("'", "").replace("-", " ").split()
    middle_parts = parsed.middle.lower().replace("'", "").replace("-", " ").split()
    last_parts = parsed.last.lower().replace("'", "").replace("-", " ").split()
    # Construct tuple return
    return (
        len(first_parts) > 1,
        bool(middle_parts),
        len(middle_parts) > 1,
        len(last_parts) > 1,
    )


def add_name_characteristics_flags(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add boolean flags for name characteristics to a DataFrame.

    Args:
        data (pd.DataFrame): A DataFrame containing an 'investor' column with full name strings.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with additional boolean columns:
            - has_german_char
            - has_nfkd_normalized
            - has_nickname
            - has_multiple_first_names
            - has_middle_name
            - has_multiple_middle_names
            - has_multiple_last_names

    Raises:
        ValueError: If the 'investor' column is not present in the input DataFrame.
    """
    if "investor" not in data.columns:
        raise ValueError("Required field 'investor' missing!")

    df = data.copy()

    # Apply boolean checks into their own fields
    df["has_german_char"] = df["investor"].apply(_has_german_char)
    df["has_nfkd_normalized"] = df["investor"].apply(_has_nfkd_char)
    df["has_nickname"] = df["investor"].apply(_has_nickname)

    # Structural parsing
    struct_flags = df["investor"].apply(_parse_name_structure)
    df["has_multiple_first_names"] = struct_flags.apply(lambda x: x[0])
    df["has_middle_name"] = struct_flags.apply(lambda x: x[1])
    df["has_multiple_middle_names"] = struct_flags.apply(lambda x: x[2])
    df["has_multiple_last_names"] = struct_flags.apply(lambda x: x[3])

    return df

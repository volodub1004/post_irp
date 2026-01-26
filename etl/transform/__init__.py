"""
etl.transform

Transform package for ETL.
"""

from .standardise import standardise_table
from .validate import validate_table, flag_multi_domain_firms, flag_shared_domain
from .transformer import transform_table
from .cleaning import (
    drop_rows_missing_emails,
    drop_emails_with_invalid_local,
)

__all__ = [
    "standardise_table",
    "validate_table",
    "transform_table",
    "drop_rows_missing_emails",
    "drop_emails_with_invalid_local",
    "flag_multi_domain_firms",
    "flag_shared_domain",
]

# Note: CoPilot was used to help guide through SQLAlchemy use and inform on best practices.

import os
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    Engine,
    Boolean,
    Float,
    JSON,
)
from enum import Enum

# Enums and Constants
# ------------------------------------------


# Enum for table names
class TableName(Enum):
    """Enumeration of database tables.

    Attributes:
        LP:
            Raw “LP” contacts table.
        GP:
            Raw “GP” contacts table.
        LP_CLEAN:
            Cleaned “LP” contacts table.
        GP_CLEAN:
            Cleaned “GP” contacts table.
        COMBINED_CLEAN:
            Merged clean LP + GP table.
        CANONICAL_FIRMS:
            Canonical firm names.
        FIRM_CACHE:
            Fuzzy match firm names cache.
        CANDIDATE_TEMPLATES:
            All possible templates mined from our dataset.
        FIRM_TEMPLATE_MAP:
            Maps templates to firms for feature engineering.
        FEATURE_MATRIX:
            Engineered features for model training.
    """

    LP = "lp_raw"
    GP = "gp_raw"
    LP_CLEAN = "lp_clean"
    GP_CLEAN = "gp_clean"
    COMBINED_CLEAN = "combined_clean"
    CANONICAL_FIRMS = "canonical_firms"
    FIRM_CACHE = "firm_cache"
    CANDIDATE_TEMPLATES = "candidate_templates"
    FIRM_TEMPLATE_MAP = "firm_template_map"
    FEATURE_MATRIX = "feature_matrix"
    FEATURE_MATRIX_COMPLEX = "feature_matrix_complex"


# Database file path
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_FILE = os.path.join(DB_DIR, "database.db")

# SQLAlchemy Engine and Metadata
# ------------------------------------------


# Create SQLAlchemy engine for SQLite
def get_engine() -> Engine:
    """Get a cached SQLAlchemy engine for the database.
    Returns:
        Engine: SQLAlchemy engine connected to the SQLite database.
    """
    return create_engine(
        f"sqlite:///{DB_FILE}",
        connect_args={"check_same_thread": False},
        echo=False,
    )


# Define metadata
metadata = MetaData()

# Raw LP table
lp_raw = Table(
    "lp_raw",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("investor", Text, nullable=False),
    Column("firm_type", Text),
    Column("title", Text),
    Column("firm", Text, nullable=False),
    Column("alternative_name", Text),
    Column("role", Text),
    Column("job_title", Text),
    Column("asset_class", Text),
    Column("email", Text),
    Column("tel", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("linkedin", Text),
    Column("region", Text),
    Column("address", Text),
    Column("website", Text),
    Column("general_email", Text),
    Column("source_file", Text),
    Column("time_stamp", DateTime),
)

# Raw GP table
gp_raw = Table(
    "gp_raw",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("investor", Text, nullable=False),
    Column("firm_type", Text),
    Column("title", Text),
    Column("firm", Text, nullable=False),
    Column("alternative_name", Text),
    Column("role", Text),
    Column("job_title", Text),
    Column("asset_class", Text),
    Column("email", Text),
    Column("tel", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("linkedin", Text),
    Column("region", Text),
    Column("address", Text),
    Column("website", Text),
    Column("general_email", Text),
    Column("source_file", Text),
    Column("time_stamp", DateTime),
)

# Clean LP table
lp_clean = Table(
    "lp_clean",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, unique=True),
    Column("investor", Text, nullable=False),
    Column("firm_type", Text),
    Column("title", Text),
    Column("firm", Text, nullable=False),
    Column("alternative_name", Text),
    Column("role", Text),
    Column("job_title", Text),
    Column("asset_class", Text),
    Column("email", Text, nullable=False),
    Column("tel", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("linkedin", Text),
    Column("region", Text),
    Column("address", Text),
    Column("website", Text),
    Column("general_email", Text),
    Column("source_file", Text),
    Column("is_shared_infra", Boolean, nullable=False, default=False),
    Column("firm_is_multi_domain", Boolean, nullable=False, default=False),
    Column("has_german_char", Boolean, nullable=False, default=False),
    Column("has_nfkd_normalized", Boolean, nullable=False, default=False),
    Column("has_nickname", Boolean, nullable=False, default=False),
    Column("has_multiple_first_names", Boolean, nullable=False, default=False),
    Column("has_middle_name", Boolean, nullable=False, default=False),
    Column("has_multiple_middle_names", Boolean, nullable=False, default=False),
    Column("has_multiple_last_names", Boolean, nullable=False, default=False),
    Column("token_seq", JSON),
    Column("time_stamp", DateTime),
)

# Clean GP table
gp_clean = Table(
    "gp_clean",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, unique=True),
    Column("investor", Text, nullable=False),
    Column("firm_type", Text),
    Column("title", Text),
    Column("firm", Text, nullable=False),
    Column("alternative_name", Text),
    Column("role", Text),
    Column("job_title", Text),
    Column("asset_class", Text),
    Column("email", Text, nullable=False),
    Column("tel", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("linkedin", Text),
    Column("region", Text),
    Column("address", Text),
    Column("website", Text),
    Column("general_email", Text),
    Column("source_file", Text),
    Column("is_shared_infra", Boolean, nullable=False, default=False),
    Column("firm_is_multi_domain", Boolean, nullable=False, default=False),
    Column("has_german_char", Boolean, nullable=False, default=False),
    Column("has_nfkd_normalized", Boolean, nullable=False, default=False),
    Column("has_nickname", Boolean, nullable=False, default=False),
    Column("has_multiple_first_names", Boolean, nullable=False, default=False),
    Column("has_middle_name", Boolean, nullable=False, default=False),
    Column("has_multiple_middle_names", Boolean, nullable=False, default=False),
    Column("has_multiple_last_names", Boolean, nullable=False, default=False),
    Column("token_seq", JSON),
    Column("time_stamp", DateTime),
)

# Combined clean table
combined_clean = Table(
    "combined_clean",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, unique=True),
    Column("source", Text, nullable=False),
    Column("record_id", Integer, nullable=False),
    Column("investor", Text, nullable=False),
    Column("firm_type", Text),
    Column("title", Text),
    Column("firm", Text, nullable=False),
    Column("alternative_name", Text),
    Column("role", Text),
    Column("job_title", Text),
    Column("asset_class", Text),
    Column("email", Text, nullable=False),
    Column("tel", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("linkedin", Text),
    Column("region", Text),
    Column("address", Text),
    Column("website", Text),
    Column("general_email", Text),
    Column("source_file", Text),
    Column("is_shared_infra", Boolean, nullable=False, default=False),
    Column("firm_is_multi_domain", Boolean, nullable=False, default=False),
    Column("has_german_char", Boolean, nullable=False, default=False),
    Column("has_nfkd_normalized", Boolean, nullable=False, default=False),
    Column("has_nickname", Boolean, nullable=False, default=False),
    Column("has_multiple_first_names", Boolean, nullable=False, default=False),
    Column("has_middle_name", Boolean, nullable=False, default=False),
    Column("has_multiple_middle_names", Boolean, nullable=False, default=False),
    Column("has_multiple_last_names", Boolean, nullable=False, default=False),
    Column("token_seq", JSON),
    Column("time_stamp", DateTime),
)

# Fuzzy lookup table stuff
canonical_firms = Table(
    "canonical_firms",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("firm", Text, nullable=False),
    Column("domain", Text, nullable=False),
)
# This is the domain firm pairs to store.

# This is the cache to memoise our results.
firm_match_cache = Table(
    "firm_match_cache",
    metadata,
    Column("raw_firm", Text, primary_key=True),
    Column("canonical_firm", Text),
    Column("domain", Text),
    Column("match_score", Integer),  # e.g. 0–100 from RapidFuzz
)

# Candidate templates for our feature matrix
candidate_templates = Table(
    "candidate_templates",
    metadata,
    Column("template_id", Integer, primary_key=True, autoincrement=True),
    Column(
        "template", JSON, nullable=False
    ),  # stored as JSON string like '["f", ".", "last"]'
    # Usage stats
    Column("support_count", Integer, nullable=False),
    Column("coverage_pct", Float, nullable=False),
    # Rule-based support
    Column("in_mined_rules", Boolean, nullable=False),
    Column("max_rule_confidence", Float, nullable=False),
    Column("avg_rule_confidence", Float, nullable=False),
    # Structure-based features
    Column("uses_middle_name", Boolean, nullable=False),
    Column("uses_multiple_firsts", Boolean, nullable=False),
    Column("uses_multiple_middles", Boolean, nullable=False),
    Column("uses_multiple_lasts", Boolean, nullable=False),
)

# Map templates to firms
firm_template_map = Table(
    "firm_template_map",
    metadata,
    Column("firm", Text, primary_key=True),
    Column("template_ids", JSON, nullable=False),  # list of template_id ints
    Column("num_templates", Integer, nullable=False),
    Column("num_investors", Integer, nullable=False),
    Column("diversity_ratio", Float, nullable=False),  # templates / investors
    Column("is_single_template", Boolean, nullable=False),  # for fast filtering
    Column("is_shared_infra", Boolean, nullable=False, default=False),
    Column("firm_is_multi_domain", Boolean, nullable=False, default=False),
)

# Engineered Features
feature_matrix = Table(
    "feature_matrix",
    metadata,
    Column("clean_row_id", Integer, nullable=False),
    Column("investor", Text, nullable=False),
    Column("firm", Text, nullable=False),
    Column("template_id", Integer, nullable=False),
    Column("template_in_firm_templates", Boolean, nullable=False),
    Column("firm_is_shared_infra", Boolean, nullable=False),
    Column("firm_is_multi_domain", Boolean, nullable=False),
    Column("investor_has_german_char", Boolean, nullable=False),
    Column("investor_has_nfkd_normalized", Boolean, nullable=False),
    Column("investor_has_nickname", Boolean, nullable=False),
    Column("investor_has_multiple_first_names", Boolean, nullable=False),
    Column("investor_has_middle_name", Boolean, nullable=False),
    Column("investor_has_multiple_middle_names", Boolean, nullable=False),
    Column("investor_has_multiple_last_names", Boolean, nullable=False),
    Column("template_support_count", Integer, nullable=False),
    Column("template_coverage_pct", Float, nullable=False),
    Column("template_in_mined_rules", Boolean, nullable=False),
    Column("template_max_rule_confidence", Float, nullable=False),
    Column("template_avg_rule_confidence", Float, nullable=False),
    Column("template_uses_middle_name", Boolean, nullable=False),
    Column("template_uses_multiple_firsts", Boolean, nullable=False),
    Column("template_uses_multiple_middles", Boolean, nullable=False),
    Column("template_uses_multiple_lasts", Boolean, nullable=False),
    Column("template_firm_support_count", Integer),
    Column("template_firm_coverage_pct", Float),
    Column("template_is_top_template", Boolean),
    Column("template_name_characteristic_clash", Boolean, nullable=False),
    Column("firm_num_templates", Integer),
    Column("firm_num_investors", Integer),
    Column("firm_diversity_ratio", Float),
    Column("firm_is_single_template", Boolean),
    Column("label", Integer, nullable=False),  # 1 if correct template, else 0
    PrimaryKeyConstraint("clean_row_id", "template_id"),
)

# Complex feature matrix
feature_matrix_complex = Table(
    "feature_matrix_complex",
    metadata,
    *[
        Column(col.name, col.type, *col.constraints, nullable=col.nullable)
        for col in feature_matrix.columns
    ],
    PrimaryKeyConstraint("clean_row_id", "template_id"),
)


# Create all tables in the database
def create_tables():
    """Create all tables in the database."""
    metadata.create_all(get_engine())
    print("Tables created successfully.")


_TABLE_LOOKUP: dict[TableName, Table] = {
    TableName.LP: lp_raw,
    TableName.GP: gp_raw,
    TableName.LP_CLEAN: lp_clean,
    TableName.GP_CLEAN: gp_clean,
    TableName.COMBINED_CLEAN: combined_clean,
    TableName.CANONICAL_FIRMS: canonical_firms,
    TableName.FIRM_CACHE: firm_match_cache,
    TableName.CANDIDATE_TEMPLATES: candidate_templates,
    TableName.FIRM_TEMPLATE_MAP: firm_template_map,
    TableName.FEATURE_MATRIX: feature_matrix,
    TableName.FEATURE_MATRIX_COMPLEX: feature_matrix_complex,
}

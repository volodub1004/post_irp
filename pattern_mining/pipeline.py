import json
import pandas as pd
from db.db import init_db, read_table, write_table
from etl.load import load_clean_data
from pathlib import Path
from db.models import TableName
from db.migrations import run_all_migrations
from pattern_mining import (
    EmailTemplateEncoder,
    TemplateRuleMiner,
)
from pattern_mining.data_enrichment import (
    add_name_characteristics_flags,
    enrich_candidate_templates,
    build_f_t_map,
)

# Constants - Check notebook for details
MAX_MISSING_PCT = 40
MIN_TOTAL_COUNT = 5

ESSENTIAL_COLUMNS = [
    "id",
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
    "time_stamp",
    "has_german_char",
    "has_nfkd_normalized",
    "has_nickname",
    "has_multiple_first_names",
    "has_middle_name",
    "has_multiple_middle_names",
    "has_multiple_last_names",
    "token_seq",
]


def _process_and_load_cleaned_data() -> pd.DataFrame:
    """
    Processes a cleaned contact table, mines patterns, and enriches data for email prediction.

    Returns:
        pd.DataFrame: Processed DataFrame pruned to essential columns.
    """
    # Read clean table and structural flags
    df = read_table(TableName.COMBINED_CLEAN)
    df = add_name_characteristics_flags(df)

    # Mine rules and tokenize sequences
    ete, token_seqs = _encode_email_templates(df)
    email_rules = _mine_rules(ete, token_seqs)

    # Remove none sequences from df
    df = df[df["token_seq"].notna()].reset_index(drop=True)

    # Generate unique templates and lookup
    unique_templates_str = {
        tuple(ete.decode_token_sequence(list(seq)))
        for seq in [tuple(seq) for seq in token_seqs]
    }

    # Enrich templates with structural features
    enriched_templates = enrich_candidate_templates(
        list(unique_templates_str), email_rules, df
    )

    # Identify low support templates
    enriched_templates = pd.DataFrame(enriched_templates)
    low_support_templates = enriched_templates.loc[
        enriched_templates["support_count"] < 2, "template"
    ]

    # Prune of low support templates
    enriched_templates = enriched_templates[
        enriched_templates["support_count"] >= 2
    ].reset_index(drop=True)
    template_lookup = {
        tuple(seq): idx + 1
        for idx, seq in enumerate(
            tuple(x) if isinstance(x, (list, tuple)) else tuple(json.loads(x))
            for x in enriched_templates["template"].dropna()
        )
    }

    # Write to SQL
    write_table(TableName.CANDIDATE_TEMPLATES, enriched_templates)

    # Build firm template map
    firm_template_map = build_f_t_map(df, template_lookup)
    write_table(TableName.FIRM_TEMPLATE_MAP, firm_template_map)

    # Remove low support templates from clean data
    df["token_str"] = df["token_seq"].apply(json.dumps)
    df_filtered = df[~df["token_str"].isin(low_support_templates)].reset_index(
        drop=True
    )

    # Prune to essential columns
    return df_filtered[ESSENTIAL_COLUMNS].copy()


def _encode_email_templates(df: pd.DataFrame):
    """
    Encodes email fields into token sequences using a template encoder.

    Args:
        df (pd.DataFrame): Input DataFrame with contact records.

    Returns:
        Tuple[EmailTemplateEncoder, List[List[str]]]:
            - The encoder instance.
            - List of tokenized email local-part sequences.
    """
    # Construct and encode emails
    ete = EmailTemplateEncoder()
    token_seqs = ete.encode_dataframe(df)
    print(f"{len(ete.stats['unk_sequences'])} unknown sequences out of {df.shape[0]}")
    print(f"{len(set(tuple(seq) for seq in token_seqs))} unique templates!")
    return ete, token_seqs


def _mine_rules(ete: EmailTemplateEncoder, token_seqs: list) -> list:
    """
    Mines frequent token sequence rules using the TRuleGrowth algorithm.

    Args:
        ete (EmailTemplateEncoder): The encoder instance used for tokenization.
        token_seqs (list): List of tokenized sequences to mine.

    Returns:
        list: List of mined rule dictionaries with support and confidence.
    """
    # Run rule miner
    BASE_PATH = Path(__file__).parent.resolve()
    spmf_path = (BASE_PATH / "..").resolve()
    tm = TemplateRuleMiner(ete, spmf_jar_dir=spmf_path)
    rules = tm.mine(token_seqs)
    print(f"{len(rules)} rules mined!\n{rules}")
    return rules


def run() -> bool:
    """
    Executes the full pattern mining and data enrichment pipeline.

    Args:
        do_gp_too (bool, optional): Whether to process the GP_CLEAN table. Defaults to False.

    Returns:
        bool: True if processing succeeded without exceptions, False otherwise.
    """
    try:
        # Initialise and get data
        init_db()
        clean_data = _process_and_load_cleaned_data()

        # Migrate and load clean data back into the data base.
        run_all_migrations()
        load_clean_data(TableName.COMBINED_CLEAN, clean_data, replace=True)

        return True

    except Exception as ex:
        print(f"[ERROR] Pattern mining failed: {ex}")
        return False


if __name__ == "__main__":
    run()

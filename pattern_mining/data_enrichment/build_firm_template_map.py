import pandas as pd
import json


def build_f_t_map(flagged: pd.DataFrame, template_lookup: dict) -> pd.DataFrame:
    """
    Builds a firm-level template usage map.

    Args:
        flagged (pd.DataFrame): Dataset with 'firm' and 'token_seq' columns.
        template_lookup (dict): Mapping from token_seq (tuple) to template_id (int).

    Returns:
        pd.DataFrame: Firm template map with diversity and usage statistics.
    """
    # Drop rows without templates
    valid = flagged.dropna(subset=["token_seq"]).copy()
    valid = valid[
        valid["token_seq"].apply(lambda x: isinstance(x, (list, tuple)))
    ]  # Filter out malformed
    valid["template_key"] = valid["token_seq"].apply(tuple)
    valid["template_id"] = valid["template_key"].apply(lambda t: template_lookup.get(t))

    # Group by firm
    grouped = (
        valid.groupby("firm")
        .agg(
            {
                "template_id": lambda x: sorted(x.dropna()),
                "investor": "count",
                "is_shared_infra": "any",
                "firm_is_multi_domain": "any",
            }
        )
        .reset_index()
    )
    grouped = grouped.rename(columns={"investor": "num_investors"})

    # Compute stats
    grouped["num_templates"] = grouped["template_id"].apply(set).apply(len)
    grouped["diversity_ratio"] = grouped["num_templates"] / grouped["num_investors"]
    grouped["is_single_template"] = grouped["num_templates"] == 1
    grouped["template_ids"] = grouped["template_id"].apply(
        json.dumps
    )  # for SQLite JSON compatibility
    grouped = grouped.drop(columns=["template_id"])

    return grouped

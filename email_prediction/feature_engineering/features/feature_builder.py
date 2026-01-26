import json
import pandas as pd
from typing import List, Dict
from db.models import TableName
from db.db import write_table
from collections import Counter


def build_feature_matrix(
    clean_data: pd.DataFrame,
    candidate_templates: pd.DataFrame,
    firm_template_map: pd.DataFrame,
    table: TableName,
    batch_size: int = 1000,
) -> None:
    """
    Combines cleaned investor records with candidate email templates
    and firm-template mapping statistics to produce a supervised learning
    dataset. Each row represents an (investor, firm, template) triple with features
    and a binary label indicating whether the template matches the investor.

    Args:
        clean_data (pd.DataFrame): Cleaned data.
        candidate_templates (pd.DataFrame): All candidate templates with usage stats
            and structural indicators.
        firm_template_map (pd.DataFrame): DataFrame mapping firms to template IDs and
            firm-level statistics.
    """
    if table != TableName.FEATURE_MATRIX and table != TableName.FEATURE_MATRIX_COMPLEX:
        raise ValueError("Invalid table name selected")

    # Validate the columns first
    _validate_columns(clean_data, candidate_templates, firm_template_map)

    # Construct lookups
    firm_template_lookup = _build_firm_template_lookup(firm_template_map)
    firm_stats_lookup = _build_firm_stats_lookup(firm_template_map)

    # Convert candidate templates to Python string
    candidate_templates = candidate_templates.copy()
    candidate_templates["template"] = candidate_templates["template"].apply(json.loads)

    # Construct feature matrices, row by row
    candidate_templates = candidate_templates.sort_values("template_id").reset_index(
        drop=True
    )

    # Buffer for writing
    buffer: List[pd.DataFrame] = []
    pairs_in_batch = 0
    total_pairs = 0
    for _, clean_row in clean_data.iterrows():
        if total_pairs % 5000 == 0:
            print(f"{total_pairs} features built out of {clean_data.shape[0]}")
        submatrix_rows = _build_rows_for_investor(
            clean_row, candidate_templates, firm_template_lookup, firm_stats_lookup
        )
        df = pd.DataFrame(submatrix_rows)

        # Accumulate
        buffer.append(df)
        pairs_in_batch += 1
        total_pairs += 1

        if pairs_in_batch >= batch_size:
            # Write batch
            write_table(table, pd.concat(buffer, ignore_index=True))
            buffer.clear()
            pairs_in_batch = 0

    # flush remainder
    if buffer:
        write_table(table, pd.concat(buffer, ignore_index=True))


def _validate_columns(
    clean_data: pd.DataFrame,
    candidate_templates: pd.DataFrame,
    firm_template_map: pd.DataFrame,
) -> None:
    """
    Ensures that all required columns are present in the three input DataFrames.

    Args:
        clean_data (pd.DataFrame): DataFrame of investor contact records.
        candidate_templates (pd.DataFrame): DataFrame of email templates and metadata.
        firm_template_map (pd.DataFrame): DataFrame mapping firms to template IDs and stats.

    Raises:
        ValueError: If any required column is missing in any of the inputs.
    """
    required_clean = [
        "id",
        "firm",
        "investor",
        "is_shared_infra",
        "firm_is_multi_domain",
        "has_german_char",
        "has_nfkd_normalized",
        "has_nickname",
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
    ]

    required_templates = [
        "template_id",
        "template",
        "support_count",
        "coverage_pct",
        "in_mined_rules",
        "max_rule_confidence",
        "avg_rule_confidence",
        "uses_middle_name",
        "uses_multiple_firsts",
        "uses_multiple_middles",
        "uses_multiple_lasts",
    ]

    required_firm_stats = [
        "firm",
        "template_ids",
        "num_templates",
        "num_investors",
        "diversity_ratio",
        "is_single_template",
    ]

    # Validate each DataFrame with respect its own required columns
    for col in required_clean:
        if col not in clean_data.columns:
            raise ValueError(f"Missing column from clean_data: {col}")
    for col in required_templates:
        if col not in candidate_templates.columns:
            raise ValueError(f"Missing column from candidate_templates: {col}")
    for col in required_firm_stats:
        if col not in firm_template_map.columns:
            raise ValueError(f"Missing column from firm_template_map: {col}")


def _build_firm_template_lookup(
    firm_template_map: pd.DataFrame,
) -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Builds a lookup table mapping each firm to the set of template IDs used by it.

    Args:
        firm_template_map (pd.DataFrame): DataFrame with 'firm' and 'template_ids' columns.

    Returns:
            Dict[str, Dict[int, Dict[str, float]]]:
                A nested dictionary mapping each firm to its template usage metadata:
                {
                    firm_name: {
                        template_id: {
                            "support_count": int,        # Raw count of uses in this firm
                            "coverage_pct": float,       # share of total uses by firm
                            "is_top_template": bool      # True if it's the most-used template
                        },
                        ...
                    },
                    ...
                }
    """
    # Flatten firm -> template list into counts
    records = []
    for _, row in firm_template_map.iterrows():
        firm = row["firm"]
        template_ids = json.loads(row["template_ids"])
        # Count template ids
        counts = Counter(template_ids)
        # Build dict so we can group by firm later
        for tid, count in counts.items():
            records.append(
                {
                    "firm": firm,
                    "template_ids": tid,
                    "firm_template_support_count": count,
                }
            )
    # Flatten to df
    flat_df = pd.DataFrame(records)

    # Build enriched firm -> template id -> metadata lookup
    output = {}
    for firm, group in flat_df.groupby("firm"):
        total = group["firm_template_support_count"].sum()
        max_support = group["firm_template_support_count"].max()

        # Build metadata dict
        template_dict = {}
        for _, row in group.iterrows():
            tid = row["template_ids"]
            support = row["firm_template_support_count"]
            template_dict[tid] = {
                "support_count": int(support),
                "coverage_pct": support / total if total > 0 else 0.0,
                "is_top_template": support == max_support,
            }
        # Add to firm dict
        output[firm] = template_dict
    return output


def _build_firm_stats_lookup(firm_template_map: pd.DataFrame) -> Dict[str, Dict]:
    """
    Builds a lookup table mapping firms to their template diversity statistics.

    Args:
        firm_template_map (pd.DataFrame): DataFrame with firm-level metadata.

    Returns:
        Dict[str, Dict]: A mapping from firm name to a dictionary of numeric stats.
    """
    return {
        row["firm"]: {
            "num_templates": row["num_templates"],
            "num_investors": row["num_investors"],
            "diversity_ratio": row["diversity_ratio"],
            "is_single_template": row["is_single_template"],
        }
        for _, row in firm_template_map.iterrows()
    }


def _build_rows_for_investor(
    clean_row: pd.Series,
    templates: pd.DataFrame,
    firm_template_lookup: Dict[str, Dict[int, Dict[str, float]]],
    firm_stats_lookup: Dict[str, Dict],
) -> List[dict]:
    """
    Builds the full sub-matrix for one investor-firm record.

    Iterates over all candidate templates and creates one feature row for each.
    A binary label is assigned based on whether the candidate matches the known
    correct template for the investor.

    Args:
        clean_row (pd.Series): A single cleaned row.
        templates (pd.DataFrame): All candidate template records.
        firm_template_lookup (Dict[str, Dict[int, Dict[str, float]]]): Precomputed map of firm to
        template IDs.
        firm_stats_lookup (Dict[str, Dict]): Precomputed map of firm to numeric stats.

    Returns:
        List[dict]: List of feature rows (as dicts) for that investor.

    Raises:
        RuntimeError: If multiple or zero matching templates are found for a row.
    """

    def infer_token_clash_flags(clean_row, template_tokens):
        """
        Helper function to detect token and name clashes.
        """
        flags = []

        if clean_row["has_middle_name"]:
            if any(tok.startswith("m_") or "middle" in tok for tok in template_tokens):
                flags.append("middle")

        if clean_row["has_multiple_last_names"]:
            if any(tok.startswith("l_") or "last" in tok for tok in template_tokens):
                flags.append("last")

        if clean_row["has_multiple_first_names"]:
            if any(
                tok.startswith("f_") or "first_original_1" in tok
                for tok in template_tokens
            ):
                flags.append("first")

        if clean_row["has_nfkd_normalized"]:
            if any("nfkd" in tok for tok in template_tokens):
                flags.append("nfkd")

        if clean_row["has_nickname"]:
            if any("nickname" in tok for tok in template_tokens):
                flags.append("nickname")

        return bool(flags)

    # Get firm stats if exist
    firm = clean_row["firm"]
    firm_templates = firm_template_lookup.get(firm, {})
    firm_stats = firm_stats_lookup.get(firm, {})

    rows = []
    label_found = False
    # Construct candidate rows
    for _, tmpl in templates.iterrows():
        tmpl_id = tmpl["template_id"]
        template_meta = firm_templates.get(tmpl_id, {})
        label = int(tmpl["template"] == clean_row["token_seq"])
        # Multiple labels should not happen
        if label:
            if label_found:
                raise RuntimeError(
                    f"Multiple labels found for clean_row_id={clean_row['id']}"
                )
            label_found = True

        # Construct row
        rows.append(
            {
                "clean_row_id": clean_row["id"],
                "investor": clean_row["investor"],
                "firm": firm,
                "template_id": tmpl_id,
                "template_in_firm_templates": tmpl_id in firm_templates,
                "template_firm_support_count": template_meta.get("support_count", 0),
                "template_firm_coverage_pct": template_meta.get("coverage_pct", 0.0),
                "template_is_top_template": template_meta.get("is_top_template", False),
                "firm_is_shared_infra": clean_row["is_shared_infra"],
                "firm_is_multi_domain": clean_row["firm_is_multi_domain"],
                "investor_has_german_char": clean_row["has_german_char"],
                "investor_has_nfkd_normalized": clean_row["has_nfkd_normalized"],
                "investor_has_nickname": clean_row["has_nickname"],
                "investor_has_multiple_first_names": clean_row[
                    "has_multiple_first_names"
                ],
                "investor_has_middle_name": clean_row["has_middle_name"],
                "investor_has_multiple_middle_names": clean_row[
                    "has_multiple_middle_names"
                ],
                "investor_has_multiple_last_names": clean_row[
                    "has_multiple_last_names"
                ],
                "template_support_count": tmpl["support_count"],
                "template_coverage_pct": tmpl["coverage_pct"],
                "template_in_mined_rules": tmpl["in_mined_rules"],
                "template_max_rule_confidence": tmpl["max_rule_confidence"],
                "template_avg_rule_confidence": tmpl["avg_rule_confidence"],
                "template_uses_middle_name": tmpl["uses_middle_name"],
                "template_uses_multiple_firsts": tmpl["uses_multiple_firsts"],
                "template_uses_multiple_middles": tmpl["uses_multiple_middles"],
                "template_uses_multiple_lasts": tmpl["uses_multiple_lasts"],
                "template_name_characteristic_clash": infer_token_clash_flags(
                    clean_row, tmpl["template"]
                ),
                "firm_num_templates": firm_stats.get("num_templates"),
                "firm_num_investors": firm_stats.get("num_investors"),
                "firm_diversity_ratio": firm_stats.get("diversity_ratio"),
                "firm_is_single_template": firm_stats.get("is_single_template"),
                "label": label,
            }
        )

    # At least one label required per investor candidate pair
    if not label_found:
        raise RuntimeError(f"No label found for clean_row_id={clean_row['id']}")
    return rows

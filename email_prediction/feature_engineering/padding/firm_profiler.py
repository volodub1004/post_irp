import json
from collections import defaultdict
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


def build_firm_profile(
    data_df: pd.DataFrame,
    firm_template_map_df: pd.DataFrame,
    candidate_templates_df: pd.DataFrame,
    firms: List[str],
) -> dict:
    """
    Builds a profile for a given firm, summarizing its email template usage and structural name
    features.

    Args:
        firm_id (str): The name or unique identifier of the firm.
        data_df (pd.DataFrame): The cleaned dataset, with tokenized sequences and name flags.
        firm_template_map_df (pd.DataFrame): A summary table with one row per firm.
        candidate_templates_df (pd.DataFrame): Table of all candidate templates with columns
            and any metadata.

    Returns:
        Optional[dict]: A structured dictionary with:
            - 'firm' (str): The firm ID.
            - 'is_shared_infra' (bool): Whether the firm shares an email domain with others.
            - 'firm_is_multi_domain' (bool): Whether the firm uses multiple domains.
            - 'templates' (List[Dict]): A list of template dicts with:
                - 'template' (str): The serialized token sequence.
                - 'sampling_weight' (float): Relative frequency of this template for the firm.
                - 'flag_probs' (Dict[str, float]): Average name feature rates for investors using
                    this template.
            - "num_investors" (int): Number of investors in the firm.
        Returns None if no valid token sequences or templates are found for the firm.

    Note:
        CoPilot was used to help optimize this function.
    """

    name_flags = [
        "has_german_char",
        "has_nfkd_normalized",
        "has_nickname",
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
    ]

    # Pre filter
    def _to_tuple_or_json(x):
        if isinstance(x, (list, tuple)):
            return tuple(x)
        if isinstance(x, str):
            return tuple(json.loads(x))
        return np.nan

    df = data_df.loc[
        data_df["token_seq"].notna(),
        ["firm", "token_seq", "is_shared_infra", "firm_is_multi_domain", *name_flags],
    ].copy()
    df = df[df["firm"].isin(firms)]
    ftm = firm_template_map_df.copy()
    ftm = ftm[ftm["firm"].isin(firms)]
    cand = candidate_templates_df.copy()
    df["template_tuple"] = df["token_seq"].map(_to_tuple_or_json)
    cand["template_tuple"] = cand["template"].map(_to_tuple_or_json)
    ftm["template_ids"] = ftm["template_ids"].apply(
        lambda v: json.loads(v) if isinstance(v, str) else v
    )

    # Compute probabilities
    firm_meta = (
        df[["firm", "is_shared_infra", "firm_is_multi_domain"]]
        .drop_duplicates("firm")
        .set_index("firm")
    )
    grp = df.groupby(["firm", "template_tuple"], sort=False)
    usage = grp.size().rename("usage_count")
    flag_means = grp[name_flags].mean(numeric_only=True)
    agg = pd.concat([usage, flag_means], axis=1).reset_index()
    firm_totals = (
        usage.groupby(level=0).sum().rename("total_usage").to_frame().reset_index()
    )

    # Merge
    ftm_ex = (
        ftm[["firm", "template_ids", "num_investors"]]
        .explode("template_ids")
        .rename(columns={"template_ids": "template_id"})
    )
    firm_cand = ftm_ex.merge(
        cand[["template_id", "template_tuple", "template"]],
        how="left",
        on="template_id",
    )
    merged = firm_cand.merge(agg, how="left", on=["firm", "template_tuple"]).merge(
        firm_totals, how="left", on="firm"
    )

    # Drop rows where template is nan
    merged = merged.dropna(subset=["template"])

    # Fill + compute stats
    merged["usage_count"] = merged["usage_count"].fillna(0).astype(int)
    for f in name_flags:
        merged[f] = merged[f].fillna(0.0)
    merged["total_usage"] = merged["total_usage"].fillna(0)
    merged["sampling_weight"] = np.where(
        merged["total_usage"] > 0, merged["usage_count"] / merged["total_usage"], 0.0
    )
    merged["flag_probs"] = merged[name_flags].to_dict(orient="records")

    # Per template
    per_template = merged[["firm", "template", "sampling_weight", "flag_probs"]]
    templates_per_firm = (
        per_template.groupby("firm", sort=False, group_keys=False)
        .apply(
            lambda g: g[["template", "sampling_weight", "flag_probs"]].to_dict(
                orient="records"
            ),
            include_groups=False,
        )
        .rename("templates")
        .to_frame()
    )

    # Drop firms that ended up with no templates
    templates_per_firm = templates_per_firm[
        templates_per_firm["templates"].map(len) > 0
    ]

    # Format and return
    out = (
        templates_per_firm.join(firm_meta, how="left")
        .join(
            ftm[["firm", "num_investors"]].drop_duplicates("firm").set_index("firm"),
            how="left",
        )
        .reset_index(names="firm")
    )

    return {
        r["firm"]: {
            "firm": r["firm"],
            "is_shared_infra": bool(r["is_shared_infra"]),
            "firm_is_multi_domain": bool(r["firm_is_multi_domain"]),
            "templates": r["templates"],
            "num_investors": int(r["num_investors"])
            if pd.notna(r["num_investors"])
            else 0,
        }
        for _, r in out.iterrows()
    }


def summarize_drift(
    firm_profiles_before: Dict[str, Optional[Dict[str, Any]]],
    firm_profiles_after: Dict[str, Optional[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Compares two mappings {firm_id -> firm_profile_dict} and computes drift stats across:
      - name-flag probabilities per template,
      - sampling weights per template,
      - template set/structure mismatches,
      - missing firms between snapshots.

    Returns a dict with 'global' summary, 'per_firm' details, and 'missing_firms'.

    Note:
        CoPilot was used to help optimize and conform this function to new firm profiles
    """
    # Name flags to check (extend here if new flags appear)
    name_flags = [
        "has_german_char",
        "has_nfkd_normalized",
        "has_nickname",
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
    ]

    def template_key(t: Dict[str, Any]):
        """Normalize template field to a tuple for dict/set keys."""
        tpl = t.get("template")
        if isinstance(tpl, (list, tuple)):
            return tuple(tpl)
        if isinstance(tpl, str):
            try:
                parsed = json.loads(tpl)
                return tuple(parsed if isinstance(parsed, list) else [parsed])
            except json.JSONDecodeError:
                # treat raw string as a single-token template
                return (tpl,)
        # Fallback: make it hashable
        return tuple(tpl) if tpl is not None else ("<NONE>",)

    # Globals (across all firms)
    global_max_flag_drift = defaultdict(float)  # flag -> max drift
    global_max_sampling_weight_drift = 0.0  # max drift
    global_template_structure_mismatches = 0  # count of template presence mismatches

    # Missing firms
    before_firms = set(k for k, v in firm_profiles_before.items() if v is not None)
    after_firms = set(k for k, v in firm_profiles_after.items() if v is not None)
    only_in_before = sorted(list(before_firms - after_firms))
    only_in_after = sorted(list(after_firms - before_firms))

    # Per-firm details
    per_firm: Dict[str, Dict[str, Any]] = {}

    for firm in sorted(before_firms | after_firms):
        before = firm_profiles_before.get(firm)
        after = firm_profiles_after.get(firm)

        # If either side missing, record and continue
        if before is None or after is None:
            per_firm[firm] = {
                "max_flag_drift": {f: 0.0 for f in name_flags},
                "total_flag_drift": 0.0,
                "num_flags_with_drift": 0,
                "max_sampling_weight_drift": 0.0,
                "template_structure_mismatches": 0
                if (before is None and after is None)
                else 1,
                "status": "missing_before"
                if before is None and after is not None
                else "missing_after"
                if after is None and before is not None
                else "missing_both",
            }
            if not (before is None and after is None):
                global_template_structure_mismatches += 1
            continue

        # Build template lookups
        before_templates = {template_key(t): t for t in before.get("templates", [])}
        after_templates = {template_key(t): t for t in after.get("templates", [])}
        all_templates = set(before_templates) | set(after_templates)

        firm_max_flag_drift = defaultdict(float)
        firm_max_sampling_weight_drift = 0.0
        firm_template_mismatch_count = 0

        for tmpl in all_templates:
            b = before_templates.get(tmpl)
            a = after_templates.get(tmpl)

            if b is None or a is None:
                firm_template_mismatch_count += 1
                global_template_structure_mismatches += 1
                continue

            # Sampling weight drift
            sw_b = b.get("sampling_weight", 0.0)
            sw_a = a.get("sampling_weight", 0.0)
            sw_diff = abs(float(sw_b) - float(sw_a))
            firm_max_sampling_weight_drift = max(
                firm_max_sampling_weight_drift, sw_diff
            )
            global_max_sampling_weight_drift = max(
                global_max_sampling_weight_drift, sw_diff
            )

            # Name-flag probability drift
            b_flags = b.get("flag_probs", {}) or {}
            a_flags = a.get("flag_probs", {}) or {}
            for flag in name_flags:
                diff = abs(
                    float(b_flags.get(flag, 0.0)) - float(a_flags.get(flag, 0.0))
                )
                if diff > firm_max_flag_drift[flag]:
                    firm_max_flag_drift[flag] = diff
                if diff > global_max_flag_drift[flag]:
                    global_max_flag_drift[flag] = diff

        nonzero_flags = {k: v for k, v in firm_max_flag_drift.items() if v > 0}
        per_firm[firm] = {
            "max_flag_drift": dict(
                sorted(firm_max_flag_drift.items(), key=lambda x: x[1], reverse=True)
            ),
            "total_flag_drift": float(sum(nonzero_flags.values())),
            "num_flags_with_drift": int(len(nonzero_flags)),
            "max_sampling_weight_drift": float(firm_max_sampling_weight_drift),
            "template_structure_mismatches": int(firm_template_mismatch_count),
            "status": "ok",
        }

    global_nonzero_flags = {k: v for k, v in global_max_flag_drift.items() if v > 0}
    return {
        "global": {
            "max_flag_drift": dict(
                sorted(global_max_flag_drift.items(), key=lambda x: x[1], reverse=True)
            ),
            "total_flag_drift": float(sum(global_nonzero_flags.values())),
            "num_flags_with_drift": int(len(global_nonzero_flags)),
            "max_sampling_weight_drift": float(global_max_sampling_weight_drift),
            "template_structure_mismatches": int(global_template_structure_mismatches),
            "num_firms_compared": int(len(per_firm)),
        },
        "per_firm": per_firm,
        "missing_firms": {
            "only_in_before": only_in_before,
            "only_in_after": only_in_after,
        },
    }

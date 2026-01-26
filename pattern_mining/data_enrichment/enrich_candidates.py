import re
import json
import numpy as np
import pandas as pd
from typing import List, Dict

# Precompiled regex checkers, matches name type with any number of transforms
# to an index
_RE_FIRST_IDX = re.compile(r"^first_.*_(\d+)$")
_RE_MIDDLE_IDX = re.compile(r"^middle_.*_(\d+)$")
_RE_LAST_IDX = re.compile(r"^last_.*_(\d+)$")
_RE_F_IDX = re.compile(r"^f_(\d+)$")
_RE_M_IDX = re.compile(r"^m_(\d+)$")
_RE_L_IDX = re.compile(r"^l_(\d+)$")


def _is_subsequence(sub: List[str], seq: List[str]) -> bool:
    """
    Checks whether a list of tokens is a contiguous or non-contiguous subsequence of another list.

    This is used to determine whether a candidate template matches a mined rule pattern
    by verifying that the full LHS + RHS token sequence appears in order.

    Args:
        sub (List[str]): The token sequence to check as a subsequence.
        seq (List[str]): The full sequence to check within.

    Returns:
        bool: True if `sub` is a subsequence of `seq`, False otherwise.
    """
    # Check full sequence for subsequence
    it = iter(seq)
    return all(token in it for token in sub)


def _extract_template_structure_features(token_seq: List[str]) -> Dict[str, bool]:
    """
    Extracts structural characteristics from a tokenized template sequence.

    Flags whether the template references:
    - Middle name components
    - Multiple first/middle/last name parts

    Args:
        token_seq (List[str]): A list of string tokens representing the template.

    Returns:
        Dict[str, bool]: A dictionary of boolean flags:
            - 'uses_middle_name': True if any token refers to middle name
            - 'uses_multiple_firsts': True if any secondary first name tokens are used
            - 'uses_multiple_middles': True if any secondary middle name tokens are used
            - 'uses_multiple_lasts': True if any secondary last name tokens are used
    """
    # Check for middle names
    uses_middle_name = any("middle" in tok for tok in token_seq)

    # Helper to find patterns
    def has_multiple(patterns: List[re.Pattern]) -> bool:
        for tok in token_seq:
            for pattern in patterns:
                match = pattern.match(tok)
                if match and int(match.group(1)) > 0:
                    return True
        return False

    return {
        "uses_middle_name": uses_middle_name,
        "uses_multiple_firsts": has_multiple([_RE_FIRST_IDX, _RE_F_IDX]),
        "uses_multiple_middles": has_multiple([_RE_MIDDLE_IDX, _RE_M_IDX]),
        "uses_multiple_lasts": has_multiple([_RE_LAST_IDX, _RE_L_IDX]),
    }


def enrich_candidate_templates(
    token_seqs: List[List[str]], rule_list: List[Dict], clean_df: pd.DataFrame
) -> List[Dict]:
    """
    Enriches each candidate template with rule-based support statistics and structural features.

    For every tokenized candidate template:
    - Checks whether any TRuleGrowth rule applies (i.e., is a subsequence match)
    - Aggregates confidence and support from matching rules
    - Computes structural flags via `extract_template_structure_features`
    - Calculates support count and dataset coverage

    Args:
        token_seqs (List[List[str]]): List of tokenized template sequences observed in the dataset.
        rule_list (List[Dict]): List of mined TRuleGrowth rules, each with:
            - 'lhs_tokens' (List[str])
            - 'rhs_tokens' (List[str])
            - 'support' (int)
            - 'confidence' (float)
        clean_df (pd.DataFrame): The clean data, used to calculate coverage.

    Returns:
        List[Dict]: A list of enriched template dictionaries with the following keys:
            - 'template': original token sequence
            - 'support_count': how many times this template appears
            - 'coverage_pct': proportion of dataset using this template
            - 'in_mined_rules': whether any rule supports this template
            - 'max_rule_confidence': highest confidence among supporting rules
            - 'avg_rule_confidence': average confidence among supporting rules
            - structural flags from `_extract_template_structure_features(...)`
    Raises:
        Value Error: If token_seq is not present in clean data.
    """
    if "token_seq" not in clean_df.columns:
        raise ValueError("Missing `token_seq` form clean data!")
    enriched = []

    # Precompute total and token sequence frequencies
    clean_df = clean_df.copy()
    clean_df["token_seq_str"] = clean_df["token_seq"].apply(json.dumps)
    total_templates = len(clean_df)

    # Count how many times each token_seq appears
    support_series = clean_df["token_seq_str"].value_counts()
    coverage_series = support_series / total_templates

    # Precompute rule full patterns
    rule_patterns = [
        (rule["lhs_tokens"] + rule["rhs_tokens"], rule["confidence"], rule["support"])
        for rule in rule_list
    ]

    # Iterate each token sequence in list
    for tpl in token_seqs:
        tpl_str = json.dumps(tpl)
        matched_confidences = []
        matched_supports = []

        # Check mined rules from dict
        for pattern, conf, supp in rule_patterns:
            if _is_subsequence(pattern, tpl):
                matched_confidences.append(conf)
                matched_supports.append(supp)

        # Extract structural flags
        structural_flags = _extract_template_structure_features(tpl)

        # Return in dict
        enriched.append(
            {
                "template": tpl_str,
                "support_count": support_series.get(tpl_str, 0),
                "coverage_pct": coverage_series.get(tpl_str, 0.0),
                "in_mined_rules": bool(matched_confidences),
                "max_rule_confidence": max(matched_confidences, default=0.0),
                "avg_rule_confidence": float(np.mean(matched_confidences))
                if matched_confidences
                else 0.0,
                **structural_flags,  # unpack flags into dict
            }
        )

    return enriched

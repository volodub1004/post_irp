import pandas as pd
from sklearn.model_selection import train_test_split
from typing import Tuple, List


def split_clean_ids(
    clean_df: pd.DataFrame,
    val_ratio: float = 0.2,
    test_ratio: float = 0.3,
    seed: int = 42,
) -> Tuple[List[int], List[int]]:
    """
    Splits clean data into validation and test IDs using stratified sampling on domain.
    Singleton-domain rows are excluded from val/test, so they can go to training.

    Args:
        clean_df (pd.DataFrame): Clean dataframe with 'id' and 'email'.
        val_ratio (float): Proportion of data to assign to validation.
        test_ratio (float): Proportion of data to assign to test.
        seed (int): Random seed.

    Returns:
        Tuple[List[int], List[int]]: (val_ids, test_ids)

    Note:
        CoPilot was used to assist debugging issues around stratified split.
    """
    df = clean_df.copy()
    df["domain"] = df["email"].str.extract(r"@(.+)$")[0].str.lower()

    # Filter domains that appear at least 2 times
    domain_counts = df["domain"].value_counts()
    eligible_domains = domain_counts[domain_counts > 1].index
    strat_df = df[df["domain"].isin(eligible_domains)].copy()

    # Stratified test split
    strat_df_remain, strat_df_test = train_test_split(
        strat_df,
        test_size=test_ratio,
        stratify=strat_df["domain"],
        random_state=seed,
    )

    # Now recalculate domain counts for the remaining part before val split
    remaining_domain_counts = strat_df_remain["domain"].value_counts()
    val_eligible_domains = remaining_domain_counts[remaining_domain_counts > 1].index
    val_strat_df = strat_df_remain[
        strat_df_remain["domain"].isin(val_eligible_domains)
    ].copy()

    # Stratified val split
    val_size_relative = val_ratio / (1.0 - test_ratio)
    _, strat_df_val = train_test_split(
        val_strat_df,
        test_size=val_size_relative,
        stratify=val_strat_df["domain"],
        random_state=seed,
    )

    val_ids = strat_df_val["id"].tolist()
    test_ids = strat_df_test["id"].tolist()

    print(f"Val: {len(val_ids)} | Test: {len(test_ids)}")

    return val_ids, test_ids

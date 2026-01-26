import json
import pandas as pd
from db.db import read_table, init_db
from db.models import TableName
from pathlib import Path
from email_prediction.feature_engineering.padding.firm_profiler import (
    build_firm_profile,
)
from email_prediction.feature_engineering.padding.generate_synthetic_investors import (
    generate_synthetic_investors_for_profiles,
)
from email_prediction.feature_engineering.features.split_and_stratify import (
    split_clean_ids,
)
from email_prediction.feature_engineering.features.feature_builder import (
    build_feature_matrix,
)
from typing import Dict, Tuple, List

# Padding constants, check model development notebook for reasoning
LOW_INVESTOR_THRESHOLD_STD = 40
LOW_INVESTOR_THRESHOLD_COMP = 25
STANDARD_N_PAD = 40
COMPLEX_N_PAD = 25

# Split constants as per the plan
TEST_RATIO = 0.2

# Paths for saving ids
BASE_PATH = Path(__file__).parent.resolve()
COMPLEX_CANDIDATES_PATH = (
    BASE_PATH / "../../cpp_inference_engine/cpp/data/complex_candidates.csv"
)
STD_CANDIDATES_PATH = (
    BASE_PATH / "../../cpp_inference_engine/cpp/data/std_candidates.csv"
)
TEST_IDS_DIRECTORY = BASE_PATH / "../../cpp_inference_engine/tests/test_data/"
TRAIN_AND_VAL_IDS_DIRECTORY = BASE_PATH / "../../cpp_inference_engine/cpp/data/"


def _split_dataset_by_complexity(
    df: pd.DataFrame, candidate_templates: pd.DataFrame
) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Splits the dataset and candidate templates into 'complex' and 'standard' sets
    based on the 'is_name_complex' flag.

    Returns:
        - "std_name_set": (standard_name_df, standard_templates)
        - "complex_name_set": (complex_name_df, complex_templates)
    """
    # Define complex flags
    complex_flags = [
        "has_multiple_first_names",
        "has_middle_name",
        "has_multiple_middle_names",
        "has_multiple_last_names",
        "has_nfkd_normalized",
        "has_german_char",
    ]

    # Create a single column flag
    df["is_name_complex"] = df[complex_flags].any(axis=1)

    # Split into two datasets
    complex_name_df = df[df["is_name_complex"]].copy()
    standard_name_df = df[~df["is_name_complex"]].copy()

    print(f"Complex names: {len(complex_name_df)}")
    print(f"Standard names: {len(standard_name_df)}")
    print(df["is_name_complex"].value_counts(normalize=True))

    # JSON safe string form of token_seq
    complex_name_df["token_seq_str"] = complex_name_df["token_seq"].apply(json.dumps)
    standard_name_df["token_seq_str"] = standard_name_df["token_seq"].apply(json.dumps)

    # Unique sequences seen in each subset
    complex_token_set = set(complex_name_df["token_seq_str"])
    standard_token_set = set(standard_name_df["token_seq_str"])

    # Filter candidate_templates
    complex_templates = candidate_templates[
        candidate_templates["template"].isin(complex_token_set)
    ].copy()
    standard_templates = candidate_templates[
        candidate_templates["template"].isin(standard_token_set)
    ].copy()

    print(f"Complex templates: {len(complex_templates)}")
    print(f"Standard templates: {len(standard_templates)}")

    # Save ids to csv
    complex_templates[["template_id"]].to_csv(COMPLEX_CANDIDATES_PATH, index=False)
    standard_templates[["template_id"]].to_csv(STD_CANDIDATES_PATH, index=False)

    return {
        "std_name_set": (standard_name_df, standard_templates),
        "complex_name_set": (complex_name_df, complex_templates),
    }


def _build_profile_and_pad(
    df: pd.DataFrame,
    firm_template_map: pd.DataFrame,
    candidates: pd.DataFrame,
    low_investor_firms: List[str],
    n_pad: int,
) -> pd.DataFrame:
    """
    Builds firm profiles for underrepresented firms and augments the dataset with synthetic
    investors.

    Args:
        df (pd.DataFrame): The original investor-level dataset.
        firm_template_map (pd.DataFrame): Precomputed firm-to-template mappings.
        candidates (pd.DataFrame): Candidate templates with structure and flag probabilities.
        low_investor_firms (List[str]): List of firm names with too few original entries.
        n_pad (int): Number of synthetic rows to generate per low-investor firm.

    Returns:
        pd.DataFrame: The augmented dataset including synthetic investors.
    """
    if not low_investor_firms or n_pad <= 0:
        return df.copy()

    # Build profiles
    firm_profiles = build_firm_profile(
        df, firm_template_map, candidates, low_investor_firms
    )

    # generate synthetic
    synthetic_map, _ = generate_synthetic_investors_for_profiles(
        profiles=firm_profiles,
        n_padding=n_pad,
    )

    # flatten into one DataFrame
    synthetic_df = pd.concat(
        [df for df in synthetic_map.values() if not df.empty], ignore_index=True
    )

    # append to original
    df_padded = pd.concat([df, synthetic_df], ignore_index=True)

    return df_padded


def _stratify_split_and_save(
    df_orig: pd.DataFrame,
    df_aug: pd.DataFrame,
    file_suffix: str,
    test_ratio: float = TEST_RATIO,
    seed: int = 42,
) -> None:
    """
    Stratifies and splits original data into val/test,
    then uses augmented data to extract training IDs,
    ensuring val/test contain no synthetic rows.

    Saves train/val/test ID lists to disk as CSVs using file_suffix.

    Args:
        df_orig (pd.DataFrame): Clean, original dataset.
        df_aug (pd.DataFrame): Augmented dataset containing synthetic rows.
        file_suffix (str): Used to label output files.
        test_ratio (float): Fraction of data used for testing.
        seed (int): Random seed for reproducibility.
    """
    # Get val and test sets from original clean data, stratified on domain
    val_ids, test_ids = split_clean_ids(
        df_orig, val_ratio=test_ratio, test_ratio=0.3, seed=seed
    )

    # Exclude val + test rows from augmented set to get training set
    used_ids = set(val_ids) | set(test_ids)
    train_ids = list(set(df_aug["id"]) - used_ids)

    # Save all three splits
    pd.DataFrame({"train_ids": train_ids}).to_csv(
        TRAIN_AND_VAL_IDS_DIRECTORY / f"train_{file_suffix}_ids.csv", index=False
    )
    pd.DataFrame({"val_ids": val_ids}).to_csv(
        TRAIN_AND_VAL_IDS_DIRECTORY / f"val_{file_suffix}_ids.csv", index=False
    )
    pd.DataFrame({"test_ids": test_ids}).to_csv(
        TEST_IDS_DIRECTORY / f"test_{file_suffix}_ids.csv", index=False
    )

    print(f"[{file_suffix.upper()}] train/val/test split saved:")
    print(f"Train: {len(train_ids)} | Val: {len(val_ids)} | Test: {len(test_ids)}")


def _prepare_training_data(
    low_investor_thresh_std: int = LOW_INVESTOR_THRESHOLD_STD,
    low_investor_thresh_comp: int = LOW_INVESTOR_THRESHOLD_COMP,
    std_n_pad: int = STANDARD_N_PAD,
    complex_n_pad: int = COMPLEX_N_PAD,
) -> None:
    """
    Executes the full preprocessing pipeline for a cleaned investor table (LP_CLEAN or GP_CLEAN),
    including splitting by name complexity, identifying low investor firms, generating synthetic
    investor rows, saving stratified splits, and building feature matrices.

    Args:
        table (TableName): The cleaned input table to process.
        low_investor_thresh (int): Firms with fewer than this number of investors are padded.
        std_n_pad (int): Number of synthetic rows to generate per low-investor firm (standard).
        complex_n_pad (int): Number of synthetic rows to generate per low-investor firm (complex).

    Raises:
        ValueError: If `table` is not LP_CLEAN or GP_CLEAN.
        ValueError: If augmented datasets are unexpectedly empty.
    """

    # Read and split data set
    data = read_table(TableName.COMBINED_CLEAN)
    cand_temps = read_table(TableName.CANDIDATE_TEMPLATES)
    datasets = _split_dataset_by_complexity(data, cand_temps)
    std_data, std_candidates = datasets["std_name_set"]
    complex_data, complex_candidates = datasets["complex_name_set"]

    # Get firm template map
    firm_template_map = read_table(TableName.FIRM_TEMPLATE_MAP)

    # Find low investor firms
    low_investor_firms_std = firm_template_map[
        firm_template_map["num_investors"] < low_investor_thresh_std
    ]["firm"].tolist()
    low_investor_firms_comp = firm_template_map[
        firm_template_map["num_investors"] < low_investor_thresh_comp
    ]["firm"].tolist()

    # Build firm profiles for each data set
    std_augmented = _build_profile_and_pad(
        std_data, firm_template_map, std_candidates, low_investor_firms_std, std_n_pad
    )
    print(f"Generated {len(std_augmented) - len(std_data)} new standard investors!")

    comp_augmented = _build_profile_and_pad(
        complex_data,
        firm_template_map,
        complex_candidates,
        low_investor_firms_comp,
        complex_n_pad,
    )
    print(f"Generated {len(comp_augmented) - len(complex_data)} new complex investors!")

    if std_augmented.empty or comp_augmented.empty:
        raise ValueError(
            "Augmented dataset is empty — check firm profiles or candidate templates."
        )

    # Save training and validation ids
    _stratify_split_and_save(std_data, std_augmented, "std")
    _stratify_split_and_save(
        complex_data, comp_augmented, "comp", test_ratio=TEST_RATIO + 0.1
    )

    print("Data split, writing to database!")

    # Save both to separate tables
    build_feature_matrix(
        std_augmented,
        std_candidates,
        firm_template_map,
        table=TableName.FEATURE_MATRIX,
    )
    build_feature_matrix(
        comp_augmented,
        complex_candidates,
        firm_template_map,
        table=TableName.FEATURE_MATRIX_COMPLEX,
    )


def run() -> bool:
    """
    Runs the full preprocessing and training data preparation pipeline.

    Returns:
        bool: True if the pipeline completed successfully, False if an error occurred.
    """
    try:
        # Setup DB and load clean data
        init_db()
        _prepare_training_data()

        return True

    except Exception as ex:
        print(f"[ERROR] Preprocessing failed: {ex}")
        return False


if __name__ == "__main__":
    run()

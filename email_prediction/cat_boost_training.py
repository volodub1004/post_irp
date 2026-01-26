import gc
import sqlite3
import pandas as pd
import numpy as np
from catboost import CatBoostRanker, Pool
from typing import Tuple

# Paths to files in Drive
_DB_PATH = "/content/drive/MyDrive/Colab Notebooks/database.db"
_STD_VAL_IDS = "/content/validation_std_ids.csv"
_COMP_VAL_IDS = "/content/validation_comp_ids.csv"

# Tuned hyperparameters
_BEST_PARAMS = {
    "loss_function": "YetiRank",
    "eval_metric": "NDCG:top=3",
    "random_seed": 42,
    "learning_rate": 0.13275757957731918,
    "depth": 6,
    "l2_leaf_reg": 7.142519331365267,
    "random_strength": 3.395785387976391,
    "min_data_in_leaf": 84,
    "subsample": 0.9048958560910838,
    "colsample_bylevel": 0.511123337191838,
    "grow_policy": "Lossguide",
}


def _compute_ranking_metrics(df: pd.DataFrame, k: int = 3):
    """
    Compute Accuracy@1, Recall@k, and MRR for a ranking prediction dataframe.

    Args:
        df (pd.DataFrame): Must contain columns ['clean_row_id', 'score', 'label']
        k (int): The cutoff rank for recall@k

    Returns:
        Tuple[float, float, float]: (Accuracy@1, Recall@k, MRR)
    """
    # Accuracy@1
    top1 = df.loc[df.groupby("clean_row_id")["score"].idxmax()]
    acc1 = (top1["label"] == 1).mean()

    # Recall@k
    topk = df.groupby("clean_row_id", group_keys=False).apply(
        lambda g: g.nlargest(k, "score")
    )
    recall_k = topk.groupby("clean_row_id")["label"].max().mean()

    # MRR
    def reciprocal_rank(g: pd.DataFrame) -> float:
        labels_sorted = g.sort_values("score", ascending=False)["label"].to_numpy()
        for rank, label in enumerate(labels_sorted, start=1):
            if label == 1:
                return 1.0 / rank
        return 0.0

    mrr = df.groupby("clean_row_id", group_keys=False).apply(reciprocal_rank).mean()

    return acc1, recall_k, mrr


def _train_catboost_model(
    parameters: dict,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    n_rounds: int = 500,
    model_output_path: str = "catboost_model.cbm",
) -> CatBoostRanker:
    """
    Trains a CatBoost ranking model using the provided training and validation data.

    Args:
        parameters (dict): Parameters for CatBoostRanker.
        train_df (pd.DataFrame): Training data with label, group info, and features.
        val_df (pd.DataFrame): Validation data with same structure.
        n_rounds (int): Maximum number of boosting rounds.
        model_output_path (str): File path to save the trained CatBoost model.

    Returns:
        CatBoostRanker: Trained CatBoost model.
    """
    drop_cols = ["label", "clean_row_id", "investor", "firm", "template_id"]

    # Train
    train_group_sizes = train_df.groupby("clean_row_id", sort=False).size().tolist()
    train_group_id = np.repeat(np.arange(len(train_group_sizes)), train_group_sizes)

    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df["label"]
    del train_df  # Free memory early

    train_pool = Pool(data=X_train, label=y_train, group_id=train_group_id)
    del X_train, y_train, train_group_id  # Free memory
    gc.collect()  # Call garbage collector to be extra sure

    # Validation
    val_group_sizes = val_df.groupby("clean_row_id", sort=False).size().tolist()
    val_group_id = np.repeat(np.arange(len(val_group_sizes)), val_group_sizes)

    X_val = val_df.drop(columns=drop_cols)
    y_val = val_df["label"]

    val_pool = Pool(data=X_val, label=y_val, group_id=val_group_id)
    del X_val, y_val, val_group_id  # Free memory
    gc.collect()  # Call garbage collector to be extra sure

    # Train model
    model = CatBoostRanker(iterations=n_rounds, **parameters)
    model.fit(
        train_pool,
        eval_set=val_pool,
        early_stopping_rounds=50,
        verbose=True,
    )

    # Save model
    model.save_model(model_output_path)
    print(f"\nModel saved to: {model_output_path}")

    # Score model
    val_df = val_df.copy()  # preserve original structure
    val_df["score"] = model.predict(val_pool)

    acc1, recall3, mrr = _compute_ranking_metrics(val_df, k=3)

    print("\nEvaluation Metrics (Validation Set):")
    print(f"Accuracy@1 : {acc1:.4f}")
    print(f"Recall@3   : {recall3:.4f}")
    print(f"MRR        : {mrr:.4f}")

    return model


def train_standard_and_complex_model(
    n_rounds: int = 1000,
) -> Tuple[CatBoostRanker, CatBoostRanker]:
    """
    Trains two CatBoost ranking models (standard and complex) on pre-split data and saves them to
    disk.

    The models are saved in `.cbm` format for compatibility with CatBoost's C++ inference engine.

    Args:
        n_rounds (int): Maximum number of boosting rounds for training (default: 1000).

    Returns:
        Tuple[CatBoostRanker, CatBoostRanker]: The trained standard and complex CatBoost models.
    """
    # Mount drive
    import sys

    if "google.colab" in sys.modules:
        from google.colab import drive

        drive.mount("/content/drive")

    def train_model(
        data_table: str, val_ids_path: str, model_path: str
    ) -> CatBoostRanker:
        print(f"Training model: {model_path}")
        # Get data
        with sqlite3.connect(_DB_PATH) as conn:
            full_df = pd.read_sql_query(f"SELECT * FROM {data_table}", conn)

        # Get ids
        val_ids = (
            pd.read_csv(val_ids_path)["validation_ids"].dropna().astype(int).tolist()
        )

        # Split the set
        val_ids_set = set(val_ids)
        val_df = full_df[full_df["clean_row_id"].isin(val_ids_set)]
        full_df = full_df[~full_df["clean_row_id"].isin(val_ids_set)]

        # Train model
        return _train_catboost_model(
            _BEST_PARAMS, full_df, val_df, n_rounds, model_path
        )

    # Start with standard
    std_model = train_model("feature_matrix", _STD_VAL_IDS, "std_catboost_model.cbm")
    # Then complex
    comp_model = train_model("feature_matrix", _COMP_VAL_IDS, "comp_catboost_model.cbm")

    return std_model, comp_model


if __name__ == "__main__":
    train_standard_and_complex_model()

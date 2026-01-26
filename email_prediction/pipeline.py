import etl
import pattern_mining
from email_prediction import feature_engineering


def run() -> bool:
    """
    Executes the full preprocessing pipeline for investor email prediction.

    This function orchestrates the sequential execution of the following components:
    - ETL: Loads and cleans raw investor contact data.
    - Pattern Mining: Identifies frequent email template structures using TRuleGrowth.
    - Feature Engineering: Constructs feature matrices for template prediction models.

    Each step is expected to return a boolean indicating success. The function prints
    the completion status of each step and halts execution if a step fails.

    Returns:
        bool: True for successful run of pipeline, False otherwise.
    """
    if etl.run():
        print("ETL pipeline complete.")
    else:
        print("ETL pipeline failed.")
        return False

    if pattern_mining.run():
        print("Pattern mining pipeline complete.")
    else:
        print("Pattern mining pipeline failed.")
        return False

    if feature_engineering.run():
        print("Feature engineering pipeline complete.")
        print("Data preprocessing complete.")
    else:
        print("Feature engineering pipeline failed.")
        return False

    # Success
    return True


if __name__ == "__main__":
    run()

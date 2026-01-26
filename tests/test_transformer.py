import pytest
import pandas as pd
from db.models import TableName
from db.db import write_table
from etl.transform.transformer import transform_table


@pytest.mark.integration
def test_transform_table_end_to_end():
    # Simulated raw LP data with a definite and ambiguous duplicate
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "investor": ["John Smith", "John Smith", "Jane Doe", "John Smith"],
            "firm": ["Blackstone", "Blackstone", "KKR", "KKR"],
            "role": ["VP", "VP", "Analyst", "Associate"],
            "email": ["js@bs.com", "js@bs.com", "jd@kkr.com", "js@kkr.com"],
            "linkedin": [
                "linkedin.com/in/js",
                "linkedin.com/in/js",
                "linkedin.com/in/jd",
                "linkedin.com/in/js-diff",
            ],
        }
    )

    # Load into temp database using write_table (temp_db fixture is auto-used)
    write_table(TableName.LP, df)

    # Run full pipeline on that table
    result = transform_table(TableName.LP)

    # Check all expected keys are present
    assert set(result.keys()) == {"final_df", "validation"}

    final_df = result["final_df"]

    # Final deduplicated data should exclude IDs 1 and 2
    final_ids = set(final_df["id"])
    assert 3 in final_ids

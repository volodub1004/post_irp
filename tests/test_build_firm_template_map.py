import json
import pandas as pd
from pattern_mining.data_enrichment import build_f_t_map


def test_build_firm_template_map_basic():
    # Sample flagged input
    data = {
        "firm": ["firm_a", "firm_a", "firm_a", "firm_b", "firm_b", "firm_c"],
        "investor": ["x", "y", "z", "m", "n", "p"],
        "token_seq": [
            ["f_0", ".", "last_original_0"],
            ["f_0", ".", "last_original_0"],
            ["f_0", "last_original_0"],
            ["first_original_0", "last_original_0"],
            ["first_original_0", "last_original_0"],
            None,  # firm_c has no token_seq
        ],
        "is_shared_infra": True,
        "firm_is_multi_domain": True,
    }

    flagged = pd.DataFrame(data)

    # Define deterministic template IDs
    template_lookup = {
        tuple(["f_0", ".", "last_original_0"]): 1,
        tuple(["f_0", "last_original_0"]): 2,
        tuple(["first_original_0", "last_original_0"]): 3,
    }

    # Call function
    result = build_f_t_map(flagged, template_lookup)

    # Verify results
    firm_a = result[result["firm"] == "firm_a"].iloc[0]
    assert sorted(json.loads(firm_a["template_ids"])) == [1, 1, 2]
    assert firm_a["num_templates"] == 2
    assert firm_a["num_investors"] == 3
    assert not firm_a["is_single_template"]

    firm_b = result[result["firm"] == "firm_b"].iloc[0]
    assert json.loads(firm_b["template_ids"]) == [3, 3]
    assert firm_b["is_single_template"]
    assert firm_b["diversity_ratio"] == 1 / 2

    # Ensure firm_c is excluded (no template)
    assert "firm_c" not in result["firm"].values

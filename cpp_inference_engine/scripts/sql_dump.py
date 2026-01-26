"""
Dumps inference relevant data from SQL DB into lightweight binary for CPP inference
engine to load at run time.
"""

import sqlalchemy as sa
import pandas as pd
import msgpack
import json
from pathlib import Path

# Start SQL
engine = sa.create_engine("sqlite:///data/database.db")
conn = engine.connect()
meta = sa.MetaData()
meta.reflect(bind=engine)

# Get the split ids
script_dir = Path(__file__).resolve().parent
complex_ids = pd.read_csv(script_dir / "../cpp/data/complex_candidates.csv")[
    "template_id"
].to_list()
std_ids = pd.read_csv(script_dir / "../cpp/data/std_candidates.csv")[
    "template_id"
].to_list()

# Set save directory
SAVE_DIRECTORY = script_dir / "../cpp/data"

# Dump candidate templates
std_cand = []
complex_cand = []
all_ids = []
for row in conn.execute(sa.select(meta.tables["candidate_templates"])):
    all_ids.append(row.template_id)
    if row.template_id in complex_ids:
        complex_cand.append(
            {
                "template_id": row.template_id,
                "template": json.loads(row.template),
                "support_count": row.support_count,
                "coverage_pct": row.coverage_pct,
                "in_mined_rules": row.in_mined_rules,
                "max_rule_confidence": row.max_rule_confidence,
                "avg_rule_confidence": row.avg_rule_confidence,
                "uses_middle_name": row.uses_middle_name,
                "uses_multiple_firsts": row.uses_multiple_firsts,
                "uses_multiple_middles": row.uses_multiple_middles,
                "uses_multiple_lasts": row.uses_multiple_lasts,
            }
        )

    if row.template_id in std_ids:
        std_cand.append(
            {
                "template_id": row.template_id,
                "template": json.loads(row.template),
                "support_count": row.support_count,
                "coverage_pct": row.coverage_pct,
                "in_mined_rules": row.in_mined_rules,
                "max_rule_confidence": row.max_rule_confidence,
                "avg_rule_confidence": row.avg_rule_confidence,
                "uses_middle_name": row.uses_middle_name,
                "uses_multiple_firsts": row.uses_multiple_firsts,
                "uses_multiple_middles": row.uses_multiple_middles,
                "uses_multiple_lasts": row.uses_multiple_lasts,
            }
        )

print(f"{len(std_cand)} std candidate templates!")
print(f"{len(complex_cand)} complex candidate templates!")

with open(SAVE_DIRECTORY / "std_candidate_templates.msgpack", "wb") as f:
    # Write to binary msgpack for CPP engine
    f.write(msgpack.packb(std_cand, use_bin_type=True))  # type: ignore
with open(SAVE_DIRECTORY / "complex_candidate_templates.msgpack", "wb") as f:
    # Write to binary msgpack for CPP engine
    f.write(msgpack.packb(complex_cand, use_bin_type=True))  # type: ignore

# Dump firm_template_map
firm_map = {}
for row in conn.execute(sa.select(meta.tables["firm_template_map"])):
    template_ids_int = [int(x) for x in json.loads(row.template_ids)]
    firm_map[row.firm] = {
        "template_ids": template_ids_int,
        "num_templates": row.num_templates,
        "num_investors": row.num_investors,
        "diversity_ratio": row.diversity_ratio,
        "is_single_template": row.is_single_template,
        "is_shared_infra": row.is_shared_infra,
        "firm_is_multi_domain": row.firm_is_multi_domain,
    }

with open(SAVE_DIRECTORY / "firm_template_map.msgpack", "wb") as f:
    f.write(msgpack.packb(firm_map, use_bin_type=True))  # type: ignore
print(f"{len(firm_map)} firms in template map!")

# Dump canonical_firms
canonical_firms = {}
for row in conn.execute(sa.select(meta.tables["canonical_firms"])):
    canonical_firms[row.firm] = {
        "domain": row.domain,
    }

with open(SAVE_DIRECTORY / "canonical_firms.msgpack", "wb") as f:
    f.write(msgpack.packb(canonical_firms, use_bin_type=True))  # type: ignore
print(f"{len(firm_map)} firms in domain map!")


# Dump canonical_firms
firm_match_cache = {}
for row in conn.execute(sa.select(meta.tables["firm_match_cache"])):
    firm_match_cache[row.raw_firm] = {
        "canonical_firm": row.canonical_firm,
        "domain": row.domain,
        "match_score": row.match_score,
    }

with open(SAVE_DIRECTORY / "firm_match_cache.msgpack", "wb") as f:
    f.write(msgpack.packb(firm_match_cache, use_bin_type=True))  # type: ignore
print(f"{len(firm_match_cache)} firms in cache!")

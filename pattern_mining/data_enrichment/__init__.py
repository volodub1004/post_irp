"""
pattern_mining.data_enrichment

Package for data enriching functionality used in the pattern mining phase.
"""

from .add_name_characteristics import add_name_characteristics_flags
from .build_firm_template_map import build_f_t_map
from .enrich_candidates import enrich_candidate_templates

__all__ = [
    "add_name_characteristics_flags",
    "build_f_t_map",
    "enrich_candidate_templates",
]

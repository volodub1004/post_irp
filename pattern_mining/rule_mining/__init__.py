"""
pattern_mining.rule_mining

Contains the TRuleGrowth rule miner. Works with the SPMF library and calls java in the backend.
"""

from .template_rule_miner import TemplateRuleMiner

__all__ = [
    "TemplateRuleMiner",
]

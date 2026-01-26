"""
pattern_mining

Package for pattern mining using TRuleGrowth. Used to extract template structures of emails as
well as firm name to domain mappings.
"""

from . import data_enrichment
from .template_encoders import EmailTemplateEncoder
from .rule_mining import TemplateRuleMiner
from .pipeline import run

__all__ = [
    "EmailTemplateEncoder",
    "TemplateRuleMiner",
    "data_enrichment",
    "run",
]

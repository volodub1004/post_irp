"""
email_prediction.feature_engineering.padding

Module to pad with synthetic investors for low investor count firms.
"""

from .firm_profiler import build_firm_profile, summarize_drift
from .generate_synthetic_investors import generate_synthetic_investors_for_profiles

__all__ = [
    "build_firm_profile",
    "summarize_drift",
    "generate_synthetic_investors_for_profiles",
]

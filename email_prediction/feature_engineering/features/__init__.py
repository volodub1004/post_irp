"""
email_prediction.feature_engineering.features

Feature engineering and generation for LightGBM email prediction model.
"""

from .feature_builder import build_feature_matrix
from .split_and_stratify import split_clean_ids

__all__ = [
    "build_feature_matrix",
    "split_clean_ids",
]

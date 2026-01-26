"""
email_prediction.feature_engineering

Feature engineering module for email prediction training pipeline.
"""

from . import features
from . import padding
from .pipeline import run

__all__ = [
    "features",
    "padding",
    "run",
]

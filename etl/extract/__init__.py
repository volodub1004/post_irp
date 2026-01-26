"""
etl.extract

Extract package for raw data ETL.
"""

from .extractor import extract_excel_data

__all__ = ["extract_excel_data"]

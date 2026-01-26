"""
db.migrations

Migrations scripts for SQL database.
"""

from .migrator import run_all_migrations

__all__ = [
    "run_all_migrations",
]

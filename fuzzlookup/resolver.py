from rapidfuzz import process, fuzz
from db.db import read_table, write_table
from db.models import TableName
import pandas as pd


class FirmResolver:
    """
    Fuzzy resolver for firm names with caching and high-performance matching.

    This class resolves raw firm names to canonical firm-domain pairs using
    fuzzy matching against a preloaded list of canonical firms. Resolved
    matches are cached to avoid redundant computations in future lookups.

    Attributes:
        threshold (int): Minimum fuzzy match score to accept a match.
        canonical_df (pd.DataFrame): Cached DataFrame of canonical firm-domain pairs.
        cache (dict): In-memory cache of previous fuzzy matches.
        _canonical_names (list[str]): List of canonical firm names for matching.
        _firm_to_domain (dict): Mapping from canonical firm to domain.
    """

    def __init__(self, threshold: int = 85):
        self.threshold = threshold
        self.canonical_df = read_table(TableName.CANONICAL_FIRMS)
        self.cache = self._load_cache()

        # Precompile search space
        self._canonical_names = self.canonical_df["firm"].tolist()
        self._firm_to_domain = dict(
            zip(self.canonical_df["firm"], self.canonical_df["domain"])
        )

    def _load_cache(self) -> dict:
        """
        Loads the firm match cache from the database into memory.

        Returns:
            dict: Mapping of raw_firm to (canonical_firm, domain, match_score).
        """
        try:
            df = read_table(TableName.FIRM_CACHE)
            return dict(
                zip(
                    df["raw_firm"],
                    df[["canonical_firm", "domain", "match_score"]].to_records(
                        index=False
                    ),
                )
            )
        except Exception:
            return {}

    def resolve(self, raw_firm: str) -> tuple[str, str, str, int]:
        """
        Resolves a raw firm name to a canonical firm and domain.

        First checks the cache for a match. If not found, performs an
        exact or fuzzy match against the canonical list. If matched, the
        result is stored in the cache and written to the database.

        Args:
            raw_firm (str): The firm name to resolve.

        Returns:
            tuple[str, str, str, int]: A tuple containing:
                - raw_firm (str): The input name
                - canonical_firm (str or None): Matched canonical name
                - domain (str or None): Associated domain
                - match_score (int): Fuzzy match score
        """
        # Exact match cache
        if raw_firm in self.cache:
            canonical_firm, domain, score = self.cache[raw_firm]
            return raw_firm, canonical_firm, domain, score

        # Exact canonical hit (no fuzzy needed)
        if raw_firm in self._firm_to_domain:
            canonical_firm = raw_firm
            domain = self._firm_to_domain[raw_firm]
            score = 100
        else:
            # Fuzzy match
            match, score, _ = process.extractOne(
                raw_firm,
                self._canonical_names,
                scorer=fuzz.token_sort_ratio,
                processor=None,  # skip preprocessing
            )
            if score < self.threshold:
                return raw_firm, None, None, score
            canonical_firm = match
            domain = self._firm_to_domain[match]

        # Cache it
        result_df = pd.DataFrame(
            [
                {
                    "raw_firm": raw_firm,
                    "canonical_firm": canonical_firm,
                    "domain": domain,
                    "match_score": score,
                }
            ]
        )
        write_table(TableName.FIRM_CACHE, result_df)
        self.cache[raw_firm] = (canonical_firm, domain, score)

        return raw_firm, canonical_firm, domain, score

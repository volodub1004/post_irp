import random
from db.db import read_table
from db.models import TableName
from fuzzlookup.resolver import FirmResolver
from typing import List


def _add_typo(word) -> str:
    """Introduce a single character-level typo into a word.

    This simulates a common data entry error such as a swapped, deleted,
    or inserted character.

    Args:
        word (str): The input word to corrupt.

    Returns:
        str: A modified version of the input word with a simulated typo.
    """
    if len(word) < 3:
        return word
    # Randomly select manipulations
    idx = random.randint(0, len(word) - 2)
    typo_type = random.choice(["swap", "delete", "insert"])
    if typo_type == "swap":
        return word[:idx] + word[idx + 1] + word[idx] + word[idx + 2 :]
    elif typo_type == "delete":
        return word[:idx] + word[idx + 1 :]
    elif typo_type == "insert":
        char = random.choice("abcdefghijklmnopqrstuvwxyz")
        return word[:idx] + char + word[idx:]
    return word


def _generate_noisy_variants(name: str) -> List[str]:
    """Generate a variety of noisy variants of a firm name.

    Variants include changes in case, removal of spaces, insertion of 'Inc',
    and character-level typos.

    Args:
        name (str): The canonical firm name.

    Returns:
        list[str]: A list of perturbed versions of the input name.
    """
    variants = set(
        [
            name.lower(),
            name.upper(),
            name.title(),
            name.replace(" ", ""),
            name + " Inc",
            _add_typo(name),  # Multiple typo types, since process is random
            _add_typo(name),
            _add_typo(name),
            _add_typo(name.title()),
            _add_typo(name.title()),
            _add_typo(name.title()),
        ]
    )
    variants.discard(name)
    return list(variants)


def populate_cache_with_noise() -> None:
    """Populate the firm match cache with noisy variants of canonical firm names.

    This function loads trusted firm-domain pairs from the canonical table,
    generates noisy variants of each firm name, resolves them using the fuzzy
    matching resolver, and stores the results into the firm match cache.

    The resulting cache entries simulate real-world lookup noise for performance
    tuning, evaluation, and fallback behavior testing.

    Returns:
        None
    """
    # Get resolver for match scores
    resolver = FirmResolver()

    # Get canonical firm-domain pairs
    canon_df = read_table(TableName.CANONICAL_FIRMS)
    noisy_rows = []

    # Save noisy inputs with matching score
    seen = set()
    for firm, domain in canon_df[["firm", "domain"]].drop_duplicates().values:
        for noisy in _generate_noisy_variants(firm):
            if noisy in seen:
                continue
            seen.add(noisy)
            # Score noisy input (saves to DB in resolver)
            raw_firm, canonical_firm, matched_domain, match_score = resolver.resolve(
                noisy
            )
            noisy_rows.append(
                {
                    "raw_firm": raw_firm,
                    "canonical_firm": canonical_firm,
                    "domain": matched_domain,
                    "match_score": match_score,
                }
            )


if __name__ == "__main__":
    populate_cache_with_noise()

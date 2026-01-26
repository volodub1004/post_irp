import json
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional


def generate_synthetic_investors_for_profiles(
    profiles: Dict[str, dict],
    n_padding: int,
    starting_id: int = 1_000_000,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[Dict[str, pd.DataFrame], int]:
    """
    Public API. Generate synthetic investors for all firms in `profiles`.

    Args:
        profiles: {firm: { 'firm', 'is_shared_infra', 'firm_is_multi_domain',
                           'templates': [{'template', 'sampling_weight', 'flag_probs'}...],
                           'num_investors' }}
        n_padding: target investors per firm (int) or per-firm map {firm: target}.
        starting_id: starting unique ID.
        rng: optional np.random.Generator for reproducibility.

    Returns:
        ({firm: synthetic_df}, final_id)

    Note:
        CoPilot was used to help optimize this function.
    """
    if rng is None:
        rng = np.random.default_rng()

    def _loads_template(t):
        if isinstance(t, (list, tuple)):
            return list(t)
        if isinstance(t, str):
            return json.loads(t)
        return []

    def _largest_remainder_counts(weights: np.ndarray, total: int) -> np.ndarray:
        if total <= 0 or weights.size == 0:
            return np.zeros_like(weights, dtype=int)
        w = weights.astype(float)
        s = w.sum()
        w = (np.ones_like(w) / len(w)) if s <= 0 else (w / s)
        raw = w * total
        base = np.floor(raw).astype(int)
        give = total - base.sum()
        if give > 0:
            idx = np.argpartition(-(raw - base), give - 1)[:give]
            base[idx] += 1
        return base

    out: Dict[str, pd.DataFrame] = {}
    curr_id = starting_id

    for firm, prof in profiles.items():
        if not prof or not prof.get("templates"):
            out[firm] = pd.DataFrame()
            continue

        new_inv = int(n_padding) - int(prof.get("num_investors", 0))
        if new_inv <= 0:
            out[firm] = pd.DataFrame()
            continue

        tmpls = prof["templates"]
        weights = np.array([t["sampling_weight"] for t in tmpls], dtype=float)
        counts = _largest_remainder_counts(weights, new_inv)
        if counts.sum() == 0:
            out[firm] = pd.DataFrame()
            continue

        pos = counts > 0
        tmpls = [t for t, k in zip(tmpls, pos) if k]
        counts = counts[pos]
        N = int(counts.sum())

        ids = np.arange(curr_id + 1, curr_id + N + 1, dtype=np.int64)
        curr_id = int(ids[-1])

        firm_col = np.full(N, firm, dtype=object)
        infra_col = np.full(N, bool(prof["is_shared_infra"]))
        multi_col = np.full(N, bool(prof["firm_is_multi_domain"]))
        investor = np.array(
            [f"synthetic_investor_{firm}_{x}" for x in ids], dtype=object
        )

        # Token sequences
        token_seq = []
        extend = token_seq.extend
        tmpl_lists = [_loads_template(t["template"]) for t in tmpls]
        for seq, c in zip(tmpl_lists, counts):
            extend([seq] * int(c))

        # Flags
        flag_names = list(tmpls[0]["flag_probs"].keys())
        F = len(flag_names)
        prob_rows = np.empty((N, F), dtype=float)
        p = 0
        for t, c in zip(tmpls, counts):
            vec = np.fromiter(
                (t["flag_probs"][fn] for fn in flag_names), dtype=float, count=F
            )
            prob_rows[p : p + c, :] = vec
            p += int(c)
        rnd = rng.random((N, F)) < prob_rows
        flag_cols = {fn: rnd[:, i] for i, fn in enumerate(flag_names)}

        out[firm] = pd.DataFrame(
            {
                "id": ids,
                "firm": firm_col,
                "investor": investor,
                "is_shared_infra": infra_col,
                "firm_is_multi_domain": multi_col,
                "token_seq": token_seq,
                **flag_cols,
            }
        )

    return out, curr_id

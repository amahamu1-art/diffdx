"""Evaluation metrics and normalization utilities for the DiffDx benchmark."""

import difflib


def normalize_pathology(s: str, allowed: list[str]) -> str | None:
    """Map a free-text pathology string to its canonical DDXPlus name.

    Tries increasingly fuzzy strategies in order:
      1. Exact match (case-insensitive)
      2. Substring match in either direction (case-insensitive)
      3. Fuzzy match via difflib with cutoff=0.7

    Args:
        s: Raw pathology string to normalize (e.g. from model output or dataset).
        allowed: List of canonical pathology names from load_pathology_list().

    Returns:
        The matched canonical name, or None if no match is found.
    """
    s_lower = s.strip().lower()

    # 1. Exact match (case-insensitive)
    for candidate in allowed:
        if candidate.lower() == s_lower:
            return candidate

    # 2. Substring match in either direction
    for candidate in allowed:
        c_lower = candidate.lower()
        if s_lower in c_lower or c_lower in s_lower:
            return candidate

    # 3. Fuzzy match
    lowered = [c.lower() for c in allowed]
    close = difflib.get_close_matches(s_lower, lowered, n=1, cutoff=0.7)
    if close:
        return allowed[lowered.index(close[0])]

    return None

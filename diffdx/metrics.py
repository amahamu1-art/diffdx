"""Evaluation metrics and normalization utilities for the DiffDx benchmark."""

import ast
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


def _extract_pathology_names(gt_differential) -> list[str]:
    """Extract pathology name strings from a DDXPlus DIFFERENTIAL_DIAGNOSIS field.

    Handles: list of strings, list of [name, prob] pairs, list of dicts,
    and string-repr of any of the above.
    """
    if isinstance(gt_differential, str):
        try:
            gt_differential = ast.literal_eval(gt_differential)
        except (ValueError, SyntaxError):
            return []

    names: list[str] = []
    for entry in gt_differential:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict):
            names.append(entry.get("pathology", ""))
        elif isinstance(entry, (list, tuple)) and len(entry) >= 1:
            names.append(str(entry[0]))
    return [n for n in names if n]


def top1_correct(predicted_top: str, ground_truth: str, allowed: list[str]) -> bool:
    """Return True if the top predicted pathology matches the ground truth."""
    norm_pred = normalize_pathology(predicted_top, allowed)
    norm_gt = normalize_pathology(ground_truth, allowed)
    if norm_pred is None or norm_gt is None:
        return False
    return norm_pred == norm_gt


def topk_correct(
    differential: list[dict], ground_truth: str, allowed: list[str], k: int = 5
) -> bool:
    """Return True if the ground truth appears in the top-k predicted pathologies."""
    norm_gt = normalize_pathology(ground_truth, allowed)
    if norm_gt is None:
        return False
    for item in differential[:k]:
        if normalize_pathology(item.get("pathology", ""), allowed) == norm_gt:
            return True
    return False


def mean_reciprocal_rank(
    differential: list[dict], ground_truth: str, allowed: list[str]
) -> float:
    """Return 1/rank of the ground truth in the differential, 0.0 if absent."""
    norm_gt = normalize_pathology(ground_truth, allowed)
    if norm_gt is None:
        return 0.0
    for rank, item in enumerate(differential, start=1):
        if normalize_pathology(item.get("pathology", ""), allowed) == norm_gt:
            return 1.0 / rank
    return 0.0


def differential_precision(
    predicted: list[dict], gt_differential: list, allowed: list[str]
) -> float:
    """Fraction of predicted pathologies that appear in the GT differential set."""
    if not predicted:
        return 0.0
    gt_names = _extract_pathology_names(gt_differential)
    gt_norm = {normalize_pathology(n, allowed) for n in gt_names} - {None}
    correct = sum(
        1 for item in predicted
        if normalize_pathology(item.get("pathology", ""), allowed) in gt_norm
    )
    return correct / len(predicted)


def differential_recall(
    predicted: list[dict], gt_differential: list, allowed: list[str]
) -> float:
    """Fraction of GT pathologies that appear in the predicted set."""
    gt_names = _extract_pathology_names(gt_differential)
    gt_norm = {normalize_pathology(n, allowed) for n in gt_names} - {None}
    if not gt_norm:
        return 0.0
    pred_norm = {
        normalize_pathology(item.get("pathology", ""), allowed) for item in predicted
    } - {None}
    return len(gt_norm & pred_norm) / len(gt_norm)

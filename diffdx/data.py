"""Data loading and formatting utilities for the DDXPlus benchmark."""

import ast
import json
import urllib.request
from pathlib import Path

from datasets import load_dataset

_EVIDENCES_URL = (
    "https://huggingface.co/datasets/aai530-group6/ddxplus/raw/main/release_evidences.json"
)
_CONDITIONS_URL = (
    "https://huggingface.co/datasets/aai530-group6/ddxplus/raw/main/release_conditions.json"
)
_CACHE_DIR = Path(__file__).parent.parent / ".cache"
_CACHE_PATH = _CACHE_DIR / "release_evidences.json"
_CONDITIONS_CACHE_PATH = _CACHE_DIR / "release_conditions.json"


def _download_if_missing(url: str, path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)


def load_evidence_lookup() -> dict:
    """Load the DDXPlus evidence code → metadata mapping.

    Downloads release_evidences.json from HuggingFace on first call and
    caches it at .cache/release_evidences.json for subsequent runs.

    Returns:
        Dict keyed by evidence code (e.g. "E_54") with fields including
        question_en and value_meaning.
    """
    _download_if_missing(_EVIDENCES_URL, _CACHE_PATH)
    with _CACHE_PATH.open() as f:
        return json.load(f)


def decode_evidences(codes: list[str], lookup: dict) -> list[str]:
    """Convert DDXPlus evidence codes to human-readable strings.

    Handles two code formats:
      - "E_70"          → question text only (boolean/presence evidence)
      - "E_54_@_V_112"  → "question text: value label"

    Args:
        codes: List of raw evidence codes from the dataset.
        lookup: Evidence lookup dict returned by load_evidence_lookup().

    Returns:
        List of readable symptom/history strings.
    """
    decoded: list[str] = []
    for code in codes:
        if "_@_" in code:
            ev_code, val_code = code.split("_@_", 1)
        else:
            ev_code, val_code = code, None

        entry = lookup.get(ev_code)
        if entry is None:
            decoded.append(code)  # unknown code — keep raw
            continue

        question = entry.get("question_en", ev_code)

        if val_code is not None:
            value_meaning = entry.get("value_meaning", {})
            label = value_meaning.get(val_code, {}).get("en", val_code)
            decoded.append(f"{question}: {label}")
        else:
            decoded.append(question)

    return decoded


def load_pathology_list() -> list[str]:
    """Return the canonical list of 49 DDXPlus pathology names.

    Downloads release_conditions.json from HuggingFace on first call and
    caches it at .cache/release_conditions.json for subsequent runs.

    Returns:
        Sorted list of English condition names (cond-name-eng).
    """
    _download_if_missing(_CONDITIONS_URL, _CONDITIONS_CACHE_PATH)
    with _CONDITIONS_CACHE_PATH.open() as f:
        conditions = json.load(f)
    return [v["cond-name-eng"] for v in conditions.values()]


def load_cases(split: str = "test", limit: int = 10) -> list[dict]:
    """Load N cases from the DDXPlus HuggingFace dataset.

    Args:
        split: Dataset split to use ("train", "validation", or "test").
        limit: Maximum number of cases to load.

    Returns:
        List of raw dataset rows as dicts.
    """
    ds = load_dataset("aai530-group6/ddxplus", split=f"{split}[:{limit}]")
    return [dict(row) for row in ds]


def format_case_for_prompt(case: dict, lookup: dict | None = None) -> str:
    """Convert a DDXPlus row into a readable clinical vignette string.

    Args:
        case: A single dataset row with AGE, SEX, INITIAL_EVIDENCE, and EVIDENCES fields.
        lookup: Optional evidence lookup from load_evidence_lookup(). When provided,
                evidence codes are decoded to human-readable text.

    Returns:
        Formatted clinical vignette suitable for use in a model prompt.
    """
    age: int = case["AGE"]
    sex: str = case["SEX"]
    initial: str = case["INITIAL_EVIDENCE"]
    raw_evidences = case["EVIDENCES"]

    # EVIDENCES is stored as a string repr of a list in this dataset
    if isinstance(raw_evidences, str):
        raw_evidences = ast.literal_eval(raw_evidences)
    evidences: list[str] = raw_evidences

    if lookup is not None:
        [initial_decoded] = decode_evidences([initial], lookup)
        evidences = decode_evidences(evidences, lookup)
    else:
        initial_decoded = initial

    gender = "male" if sex == "M" else "female"
    symptoms = ", ".join(evidences)

    return (
        f"Patient: {age}-year-old {gender}.\n"
        f"Initial complaint: {initial_decoded}\n"
        f"Reported symptoms and history: {symptoms}"
    )


if __name__ == "__main__":
    lookup = load_evidence_lookup()
    cases = load_cases(split="test", limit=3)
    for case in cases:
        print(format_case_for_prompt(case, lookup=lookup))
        print(f"Ground truth: {case['PATHOLOGY']}")
        print("---")

"""Smoke test: run 10 DDXPlus cases through the diagnosis agent and report top-1 accuracy."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tqdm import tqdm

from diffdx import data
from diffdx.agent import diagnose
from diffdx.metrics import normalize_pathology

_pathologies = data.load_pathology_list()


def _normalize(label: str, tag: str) -> str | None:
    """Normalize a label and print a warning if it was changed."""
    canonical = normalize_pathology(label, _pathologies)
    if canonical is None:
        tqdm.write(f"  [WARN] {tag}: could not normalize {label!r}")
    elif canonical != label:
        tqdm.write(f"  [NORM] {tag}: {label!r} → {canonical!r}")
    return canonical


async def main() -> None:
    cases = data.load_cases(split="test", limit=10)

    correct = 0
    attempted = 0

    for i, case in enumerate(tqdm(cases, desc="Diagnosing", unit="case"), start=1):
        ground_truth: str = case["PATHOLOGY"]
        result = await diagnose(case)

        if "error" in result:
            tqdm.write(f"Case {i}: SKIPPED — {result['error']}")
            continue

        top_raw: str = result.get("top_diagnosis", "")

        gt_norm = _normalize(ground_truth, f"Case {i} GT")
        top_norm = _normalize(top_raw, f"Case {i} Model")

        match = (gt_norm is not None and top_norm is not None and gt_norm == top_norm)
        mark = "✓" if match else "✗"

        tqdm.write(f"Case {i}: GT={gt_norm or ground_truth} | Model={top_norm or top_raw} | {mark}")

        attempted += 1
        if match:
            correct += 1

    print(f"\nFinal: {correct}/{attempted} top-1 correct")


if __name__ == "__main__":
    asyncio.run(main())

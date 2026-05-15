"""Batch evaluation runner for the DiffDx benchmark."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(Path(__file__).parent.parent / ".env")

from diffdx import agent, data
from diffdx.metrics import (
    differential_precision,
    differential_recall,
    mean_reciprocal_rank,
    normalize_pathology,
    top1_correct,
    topk_correct,
)

_RESULTS_DIR = Path(__file__).parent.parent / "results"


async def run_eval(cases: list[dict], model: str = "claude-sonnet-4-6") -> dict:
    """Evaluate the diagnosis agent on a list of DDXPlus cases.

    Args:
        cases: List of raw DDXPlus row dicts (from data.load_cases()).
        model: Claude model ID to benchmark.

    Returns:
        Summary dict with mean metrics, error count, and file paths.
    """
    _RESULTS_DIR.mkdir(exist_ok=True)

    allowed = data.load_pathology_list()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = model.replace("-", "_")
    jsonl_path = _RESULTS_DIR / f"eval_{model_slug}_{timestamp}.jsonl"
    summary_path = _RESULTS_DIR / f"summary_{model_slug}_{timestamp}.json"

    per_case: list[dict] = []
    errors = 0
    total_start = time.time()

    with tqdm(total=len(cases), desc=f"Evaluating {model}") as pbar:
        for idx, case in enumerate(cases):
            t0 = time.time()
            result = await agent.diagnose(case, model=model)
            latency = time.time() - t0

            if "error" in result:
                errors += 1
                print(f"\n[case {idx}] error: {result['error']}")
                pbar.update(1)
                continue

            gt_pathology: str = case.get("PATHOLOGY", "")
            gt_differential = case.get("DIFFERENTIAL_DIAGNOSIS", [])
            differential: list[dict] = result.get("differential", [])
            top_diag: str = result.get("top_diagnosis", "")

            row = {
                "case_index": idx,
                "gt_pathology": gt_pathology,
                "top_diagnosis": top_diag,
                "normalized_gt": normalize_pathology(gt_pathology, allowed),
                "normalized_top": normalize_pathology(top_diag, allowed) if top_diag else None,
                "latency_s": round(latency, 3),
                "top1": top1_correct(top_diag, gt_pathology, allowed),
                "top5": topk_correct(differential, gt_pathology, allowed, k=5),
                "mrr": mean_reciprocal_rank(differential, gt_pathology, allowed),
                "precision": differential_precision(differential, gt_differential, allowed),
                "recall": differential_recall(differential, gt_differential, allowed),
            }
            per_case.append(row)

            with jsonl_path.open("a") as f:
                f.write(json.dumps(row) + "\n")

            pbar.update(1)

    total_time = time.time() - total_start
    n = len(per_case)

    def _mean(key: str) -> float:
        return round(sum(r[key] for r in per_case) / n, 4) if n else 0.0

    summary = {
        "model": model,
        "timestamp": timestamp,
        "n_evaluated": n,
        "n_errors": errors,
        "total_time_s": round(total_time, 2),
        "top1_accuracy": _mean("top1"),
        "top5_accuracy": _mean("top5"),
        "mean_reciprocal_rank": _mean("mrr"),
        "mean_precision": _mean("precision"),
        "mean_recall": _mean("recall"),
        "jsonl_path": str(jsonl_path),
        "summary_path": str(summary_path),
    }

    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    width = 50
    print(f"\n{'='*width}")
    print(f"Evaluation Summary — {model}")
    print(f"{'='*width}")
    print(f"{'Cases evaluated':<22}: {n}")
    print(f"{'Errors skipped':<22}: {errors}")
    print(f"{'Top-1 Accuracy':<22}: {summary['top1_accuracy']:.1%}")
    print(f"{'Top-5 Accuracy':<22}: {summary['top5_accuracy']:.1%}")
    print(f"{'MRR':<22}: {summary['mean_reciprocal_rank']:.4f}")
    print(f"{'Diff Precision':<22}: {summary['mean_precision']:.4f}")
    print(f"{'Diff Recall':<22}: {summary['mean_recall']:.4f}")
    print(f"{'Total time':<22}: {summary['total_time_s']:.1f}s")
    print(f"{'JSONL':<22}: {jsonl_path.name}")
    print(f"{'='*width}")

    return summary

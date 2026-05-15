"""CLI entry point for DiffDx evaluation runs."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from diffdx import data
from diffdx.eval import run_eval

MODEL_MAP = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
    "haiku": "claude-haiku-4-5-20251001",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DiffDx evaluation benchmark")
    parser.add_argument("--n", type=int, default=25, help="Number of cases to evaluate")
    parser.add_argument(
        "--model",
        choices=list(MODEL_MAP),
        default="sonnet",
        help="Model shortname (sonnet/opus/haiku)",
    )
    parser.add_argument(
        "--split",
        choices=["test", "validation"],
        default="test",
        help="DDXPlus dataset split to use",
    )
    args = parser.parse_args()

    model_id = MODEL_MAP[args.model]
    print(f"Loading {args.n} cases from '{args.split}' split...")
    cases = data.load_cases(split=args.split, limit=args.n)
    print(f"Loaded {len(cases)} cases. Running eval with {model_id}...\n")

    asyncio.run(run_eval(cases, model=model_id))


if __name__ == "__main__":
    main()

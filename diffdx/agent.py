"""Diagnosis agent: wraps claude_agent_sdk to produce differential diagnoses."""

import asyncio
import json
import sys
from pathlib import Path

# Make `import diffdx` work whether this file is run directly or imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, TextBlock

from diffdx import data
from diffdx.prompts import DIAGNOSIS_SYSTEM_PROMPT

load_dotenv(Path(__file__).parent.parent / ".env")

# Load once at import time — shared across all diagnose() calls.
_lookup = data.load_evidence_lookup()


async def diagnose(case: dict, model: str = "claude-sonnet-4-6") -> dict:
    """Run differential diagnosis on a single DDXPlus case.

    Formats the case into a clinical vignette, sends it to Claude via the
    agent SDK, and returns the parsed JSON differential diagnosis.

    Args:
        case: A raw DDXPlus row dict (from data.load_cases()).
        model: Claude model ID to use.

    Returns:
        Parsed dict with keys "differential" and "top_diagnosis" on success,
        or {"error": ..., "raw": ...} on JSON parse failure,
        or {"error": ...} on any other exception.
    """
    vignette = data.format_case_for_prompt(case, lookup=_lookup)

    options = ClaudeAgentOptions(
        system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
        model=model,
        allowed_tools=[],
    )

    raw_text = ""
    try:
        async for message in query(prompt=vignette, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        raw_text += block.text

        # Strip markdown fences if the model ignores the strict-JSON instruction.
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]

        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "JSON parse failed", "raw": raw_text}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import pprint

    cases = data.load_cases(split="test", limit=1)
    case = cases[0]

    print("=== Vignette ===")
    print(data.format_case_for_prompt(case, lookup=_lookup))
    print(f"\nGround truth: {case['PATHOLOGY']}")
    print("\n=== Diagnosis ===")

    result = asyncio.run(diagnose(case))
    pprint.pprint(result, sort_dicts=False)

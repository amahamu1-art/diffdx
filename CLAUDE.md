# DiffDx — Differential Diagnosis Benchmark

## Project goal
Benchmark Claude models on the DDXPlus synthetic differential diagnosis dataset. Measure top-1 accuracy, top-5 accuracy, differential overlap, and mean reciprocal rank across hundreds of cases. Compare prompt strategies and models. This is a RESEARCH project, NOT a clinical tool.

## Tech stack
- Python 3.14, virtual env in `.venv/`
- `claude-agent-sdk` — uses CLAUDE_CODE_OAUTH_TOKEN from `.env`. DO NOT switch to the raw `anthropic` SDK, that would use paid API credits instead of the Pro subscription.
- HuggingFace `datasets` library for DDXPlus (`aai530-group6/ddxplus`)
- pandas + matplotlib for analysis and charts

## Project structure

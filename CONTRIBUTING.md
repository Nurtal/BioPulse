# Contributing to BioPulse

BioPulse is in early development. Before opening an issue or PR, please read
`README.md` (vision and core principles) and `ROADMAP.md` (phase ordering).

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

CI runs the same four commands on Python 3.11 and 3.12.

## Scope of changes

- Stay within the **current phase** of `ROADMAP.md`. Cross-phase PRs need
  prior discussion in an issue.
- Respect the three architectural invariants from `CLAUDE.md`:
  renderer-first, canonical-JSON only, event-driven (not snapshot-driven).
- The rendering backend is **not yet chosen**. Do not introduce a backend
  dependency without an issue tracking the decision.

## Commits

Conventional, imperative subject lines. Reference the roadmap phase when
relevant (e.g. `phase 1: add EventStream bisect seek`).

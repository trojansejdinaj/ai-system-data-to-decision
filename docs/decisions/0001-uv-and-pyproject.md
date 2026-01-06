# 0001 - Use uv + pyproject.toml

## Status
Accepted

## Context
We need fast, reproducible installs across multiple portfolio repos, with minimal tooling overhead.

## Decision
- Use `uv` for environment + dependency management.
- Use `pyproject.toml` as the single source of truth.
- Commit `uv.lock`.
- Pin Python via `.python-version` and run commands through `uv run` / Make targets.

## Consequences
- Faster installs and deterministic environments.
- Team/devs must use `uv` conventions (not bare `pip`).

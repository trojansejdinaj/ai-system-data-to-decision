# Week 03 — Cleaning + normalization module (2026-01-19)

## Goal
Ship a deterministic cleaning + normalization layer with documented rules and unit tests.

## What shipped
- `app.cleaning` module with:
  - Null normalization (common null literals -> `None`)
  - Date normalization -> `date` with `day_first` preference for ambiguous formats
  - Currency normalization -> `Decimal` (supports US + EU separators)
  - Category mapping to canonical labels
  - Outlier handling via simple min/max bounds (`OutlierRule`)
- Unit tests for rules + one end-to-end test case

## Cleaning rules (v1)
- **Nulls:** `None`, `""`, `"N/A"`, `"null"`, `"none"`, `"-"` → `None`
- **Text:** trim + collapse whitespace
- **Dates:** supports ISO + common slash formats; ambiguous uses `day_first=True` by default
- **Currency:** strips symbols, normalizes separators, returns `Decimal`
- **Categories:** lowercase/trim key → canonical mapping; unknown categories preserved (cleaned)
- **Outliers:** per-field min/max bounds; outside bounds → `None`

## Before/after sample rows

| field | before | after |
|---|---|---|
| title | `"  Hello   world "` | `"Hello world"` |
| category | `"Artificial Intelligence"` | `"AI"` |
| published_at | `"01/09/2026"` | `date(2026, 9, 1)` |
| price | `"€1.234,56"` | `Decimal("1234.56")` |
| views | `"-10"` | `None` |
| score | `"1.5"` | `None` |

## Commands
- Run tests: `pytest -q`
- Lint (if wired): `ruff check .`

## Notes
This is intentionally “boring” logic: deterministic transforms with strong tests.
Statistical outlier detection can come later once we have enough data volume.

# ADR 0003 — Cleaning + normalization module

## Status
Accepted — 2026-01-19

## Context
Week 02 established ingestion. Raw sources (CSV/Excel/APIs) contain messy, inconsistent values:
- Nulls expressed as "", "N/A", "null", "-"
- Dates in multiple formats (ISO, dd/mm/yyyy, mm/dd/yyyy)
- Currency formatted with symbols and locale separators
- Categories inconsistent ("AI", "Artificial Intelligence", "ai")
- Numeric outliers (negative counts, impossible scores)

We need deterministic normalization so downstream stages (database, features, models) are stable.

## Decision
Implement a dedicated `app.cleaning` module with:
- Explicit null rules
- Deterministic date parsing with a `day_first` preference for ambiguous formats
- Currency normalization to `Decimal`
- Category mapping to canonical values
- Simple per-field outlier bounds via `OutlierRule`
- A pure function pipeline: `clean_row` / `clean_rows`
- Unit tests covering each rule and an end-to-end example

## Consequences
Positive:
- Stable schema inputs and predictable downstream behavior
- Tests provide guardrails against regressions
- Configurable rules without adding heavy dependencies

Tradeoffs:
- Ambiguous dates require an explicit preference (`day_first`)
- Outlier detection is intentionally “simple bounds” (not statistical) at this stage

## Follow-ups
- Week 04: persist cleaned rows (DB schema + ingestion-to-DB flow)
- Add schema-aware field registry once real datasets settle

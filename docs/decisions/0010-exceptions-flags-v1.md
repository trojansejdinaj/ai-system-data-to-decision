# 0010 — Exceptions/flags v1 (needs-attention list)

## Status
Accepted

## Context
We need a deterministic, explainable way to identify ingested records that likely require human review.
This is the first version of an exceptions/flags layer, built directly from `public.raw_records`.

## Decision
Implement a flags engine that:
- Applies a small set of deterministic rules with fixed thresholds
- Produces a severity score as a sum of rule weights (capped at 100)
- Exports a CSV report including rule codes and human-readable explanations

## Rules (v1)
- VALUE_EMPTY_OR_NULLISH (40)
- VALUE_NOT_NUMERIC (40)
- FUTURE_EVENT_TIME (25)
- STALE_EVENT_TIME (15)
- VALUE_OUT_OF_RANGE (35)
- POSSIBLE_DUPLICATE_FINGERPRINT (30)

## Consequences
- Output is stable across runs (given the same input batch and time reference).
- Rules are easy to reason about and adjust.
- This provides a base for a future aggregated checks table (e.g., `summary.data_quality_checks`).


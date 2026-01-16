# Week 07 — Exceptions/flags v1 (needs-attention list)

## Goal
Create a deterministic, explainable “needs-attention” list from ingested records.

## Output artifacts
- Flag report CSV: `docs/assets/week-07/flags_report.csv`
- Screenshot proof: CLI output + first lines of the CSV

## Data source
- Table: `public.raw_records`

## Rules (v1)
Weights are fixed and severity is deterministic.

1. VALUE_EMPTY_OR_NULLISH (40)
   - `value` is empty/whitespace OR in {null, none, na, n/a, nil, -}

2. VALUE_NOT_NUMERIC (40)
   - `value` cannot be parsed as a float

3. FUTURE_EVENT_TIME (25)
   - `event_time` is more than 5 minutes in the future

4. STALE_EVENT_TIME (15)
   - `event_time` is older than 30 days

5. VALUE_OUT_OF_RANGE (35)
   - parsed numeric `value` is <= 0 or > 1,000,000

6. POSSIBLE_DUPLICATE_FINGERPRINT (30)
   - duplicate fingerprint appears within the current batch:
     (source, source_id, event_time, category, value)

## Severity scoring
severity = min(100, sum(weights of all triggered rules))

## How to run
- `uv run pytest -q`
- `uv run python -m app.flags`
- `head -n 25 docs/assets/week-07/flags_report.csv`

## Evidence
Store 1 screenshot containing:
- the CLI output
- the `head -n 25` output showing the report columns + flagged rows


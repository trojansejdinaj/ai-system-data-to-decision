# Decision Policy (v1)

## Overview

The decision step converts flagging results into one deterministic outcome:
`approve`, `review`, or `reject`.

It runs in `python -m app.decision`, writes a tracked `pipeline_runs` row
(`pipeline='decision'`), and persists one record in `public.decisions`.

## Inputs

- Raw records loaded from `public.raw_records` (latest batch window by limit)
- In-process flags output from `app.flags.engine.flag_records(...)`
- Per-record severity and flag codes from flagged records

## Features

The policy computes these signals from flagged records:

- `total_records`: number of records evaluated
- `flagged_count`: number of records that triggered at least one flag
- `flagged_ratio`: `flagged_count / total_records` (0 when total is 0)
- `max_severity`: max severity across flagged records
- `has_duplicate_fingerprint_flags`: true when a duplicate-like flag code exists

## Scoring

- Base score starts at `100`
- Penalties:
  - `max_severity >= 60` => `-40` and reason `high_severity_flags`
  - `flagged_ratio >= 0.30` => `-20` and reason `high_flag_density`
  - duplicate flag code present => `-10` and reason `duplicate_fingerprint_flags`
- If no flagged records: reason `no_flags_detected` (score remains high)
- If flagged records exist but no penalties hit: reason `low_risk_flags_only`
- Final score is clamped to `0..100`
- Reasons are sorted by a fixed priority list for deterministic `top_reason`

## Thresholds

- `score >= 80` => `approve`
- `50 <= score < 80` => `review`
- `score < 50` => `reject`

## Versioning

- Policy constant: `POLICY_VERSION = "v1"` (`src/app/decision_policy/policy.py`)
- Every persisted decision stores `policy_version` in `public.decisions`
- When policy logic changes, bump `POLICY_VERSION` and keep old rows intact so
  historical decisions remain reproducible under their original version label.

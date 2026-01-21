# Silver Layer: clean.clean_records

## Goal
Convert raw ingestion (`public.raw_records`) into a deterministic, normalized “silver” table used by transforms and dashboards.

## Input
- `public.raw_records`

## Output
- `clean.clean_records`

## How to run

```bash
make clean
```

**This:**

- fetches raw rows (default limit 5000)
- applies deterministic cleaning/normalization rules
- upserts into `clean.clean_records`
- writes a `pipeline_runs` entry with step timing + metadata

## ## Why silver?

- transforms should run on consistent types and normalized fields
- gold metrics shouldn't depend on raw, messy inputs
- isolates "business logic cleaning" from ingestion mechanics

## Notes

This layer is designed to be replayable: you can re-run `make clean` after any ingestion.

For the sample dataset, you should see:

- Total clean records: 10
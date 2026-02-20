# Decision Features v0

## Decision policy contract (v0)

Input: a feature dictionary (`dict[str, number]`) containing policy-relevant features.

Output:
- `decision` (`approve` | `review` | `reject`)
- `score` (integer, start at 100 and subtract penalties)
- `reasons` (ordered by largest penalty first; stable tie-break by rule code)
- `explanation_json` (JSON payload with `policy_version`, `policy_hash`, thresholds, feature snapshot, and ordered rule hits)

Policy metadata:
- `policy_version`: currently `v0`
- `policy_hash`: `sha256` of canonical policy JSON (`sort_keys=True`, `separators=(",", ":")`)

## Feature definitions

All features are computed from `clean.clean_records` with dataset scope `source = :dataset_key`.

For v0, `dataset_key == CleanRecord.source`.
In the demo flow, `dataset_key` is sourced from `DEMO_SOURCE` (default `samples`) and used directly as `clean.clean_records.source` for filtering.

| name | meaning | formula | type |
|---|---|---|---|
| `total_clean_records` | Total clean records in dataset scope. | `COUNT(*) where source = :dataset_key` | `num` |
| `distinct_sources` | Distinct source count in scope. | `COUNT(DISTINCT source) where source = :dataset_key` | `num` |
| `distinct_categories` | Distinct non-null categories in scope. | `COUNT(DISTINCT category) where source = :dataset_key and category is not null` | `num` |
| `sum_value_decimal` | Sum of non-null `value_decimal` values. | `SUM(value_decimal) where source = :dataset_key and value_decimal is not null` | `num` |
| `avg_value_decimal` | Average of non-null `value_decimal` values. | `AVG(value_decimal) where source = :dataset_key and value_decimal is not null` | `num` |
| `null_value_decimal_rate` | Null share for `value_decimal`. | `COUNT(value_decimal is null) / COUNT(*) where source = :dataset_key` | `num` |

Source of truth:
- `src/app/features/feature_definitions.py`

## Persistence schema

### `features.feature_values`
- Primary key: `id` (`bigserial`)
- Foreign key: `run_id -> pipeline_runs.id`
- Natural uniqueness: `UNIQUE (run_id, dataset_key, feature_name)`
- Indexes: `run_id`, `dataset_key`
- Value columns: `feature_value_num`, `feature_value_text`, `feature_value_json`

### `public.decisions`
- Primary key: `id` (`uuid`)
- Foreign key: `run_id -> pipeline_runs.id` (`ON DELETE CASCADE`)
- Natural uniqueness: `UNIQUE (run_id)` (one decision row per pipeline run)
- Indexes: `run_id`
- Decision payload columns: `policy_version`, `policy_hash`, `decision`, `score`, `reasons` (`jsonb`), `explanation_json` (`jsonb`), `created_at`

## Run

```bash
uv run python -m app.decisions
```

## Verify

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
"select run_id, decision, score, policy_version, policy_hash, reasons
from decisions
order by created_at desc
limit 10;"
```

Evidence artifact:
- `runs/_evidence/01.02.02.P02.T2-check-proof.txt`

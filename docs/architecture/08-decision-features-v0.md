# Decision Features v0

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

### `decisions.decisions`
- Primary key: `id` (`bigserial`)
- Foreign key: `run_id -> pipeline_runs.id`
- Natural uniqueness: `UNIQUE (run_id, policy_version)`
- Indexes: `run_id`
- Decision payload columns: `decision`, `score`, `reasons`, `created_at`

## Run

```bash
make demo
```

## Verify

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
"select run_id, dataset_key, feature_name, feature_value_num, computed_at
from features.feature_values
order by computed_at desc
limit 10;"
```

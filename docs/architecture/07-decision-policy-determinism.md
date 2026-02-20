# Decision Policy Determinism

## Purpose

`policy_version` identifies the exact scoring contract used to produce a decision.
It is persisted with every decision output so historical decisions remain reproducible,
auditable, and comparable across policy upgrades.

## Policy Contract

Current policy runtime lives in `src/app/decisions/policy_v0.py` and exposes:

- `DecisionInput`
- `DecisionPolicy`
- `DecisionResult`
- `evaluate(...)`

`DecisionResult` always includes:

- `decision`
- `score`
- `reasons`
- `policy_version`
- `policy_hash`

## Threshold Semantics

Threshold checks are inclusive:

- `approve` when `score >= approve_min`
- `review` when `score >= review_min` and `< approve_min`
- `reject` otherwise

This behavior is implemented centrally in `_decision_for_score(...)`.

## Determinism Guarantees

For the same input payload and same `policy_version`, results are deterministic:

- no randomness
- no time-dependent scoring inputs
- deterministic reason ordering: sort by penalty magnitude descending, then rule code ascending
- explicit numeric normalization in policy evaluation (`round(..., 6)`)
- canonical input hashing via JSON with sorted keys and compact separators

Canonical input hash implementation:

- `app.decisions.compute_input_hash(...)`

## Persistence

### `public.decision_outputs`

`decision_outputs` stores persisted decision artifacts:

- `policy_version` (`text`, not null)
- `input_hash` (`varchar(64)`, sha256 of canonical input JSON)
- `decision` (`varchar(20)`, not null)
- `score` (`integer`, not null)
- `reasons` (`jsonb`, not null)
- `input` (`jsonb`, canonical payload, not null)
- `meta` (`jsonb`, optional metadata)
- `created_at` (`timestamptz`)

Write helper:

- `app.decisions.save_decision_output(...)`

## Query Examples

Latest persisted outputs:

```bash
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
"select policy_version, input_hash, decision, score, reasons, created_at
 from decision_outputs
 order by created_at desc
 limit 20;"
```

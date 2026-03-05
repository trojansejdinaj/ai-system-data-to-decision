# Decision API

JSON endpoints for retrieving persisted decision outputs and run metadata.

## Endpoints

- `GET /decisions/latest`
- `GET /decisions?from=&to=&limit=&offset=`
- `GET /decisions/{run_id}`

## Query params (`GET /decisions`)

- `from` (optional, ISO datetime): inclusive lower bound on decision timestamp
- `to` (optional, ISO datetime): inclusive upper bound on decision timestamp
- `limit` (optional): default `50`, max `200`
- `offset` (optional): default `0`

Behavior notes:
- Results are newest-first.
- If both `from` and `to` are present and `from > to`, API returns `400`.
- `GET /decisions/latest` returns `404` with `{"detail":"No decisions yet"}` when no decision rows exist.
- `GET /decisions/{run_id}` returns `404` with `{"detail":"Decision not found"}` when the run has no decision.
- List response shape:
  - `items`: list of decision envelopes
  - `count`: total matching rows
  - `limit`: applied page size
  - `offset`: applied page offset

## Example response (compact)

```json
{
  "decision": {
    "run_id": "64b779c3-7576-4814-b246-a93d1a6a3655",
    "decision": "approve",
    "score": 100,
    "reasons": ["no_flags_detected"],
    "explanation_json": {},
    "policy_version": "v1",
    "policy_hash": null,
    "decided_at": "2026-02-24T10:23:03.815350Z"
  },
  "run_meta": {
    "run_started_at": "2026-02-24T10:23:03.789613Z",
    "run_finished_at": "2026-02-24T10:23:03.816446Z",
    "records_in": 0,
    "records_out": 1,
    "status": "succeeded"
  }
}
```

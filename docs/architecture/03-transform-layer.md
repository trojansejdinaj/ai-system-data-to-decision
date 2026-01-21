# Transform Layer (Gold)

This repo uses a simple 3-layer data flow:

## Layers

### Bronze (raw)
- **Table:** `public.raw_records`
- **Producer:** ingestion endpoints (`POST /ingest/samples`, `POST /ingest/files`)
- **Contract:** store the raw payload + stable dedupe hash (idempotency)

### Silver (clean)
- **Table:** `clean.clean_records`
- **Producer:** cleaning pipeline (`make clean`)
- **Goal:** deterministic normalization (types, null handling, cleaned text/category/value, preserved lineage keys)

### Gold (summary)
- **View:** `summary.monthly_metrics`
- **Producer:** metrics refresh (`make metrics`)
- **Goal:** stable monthly rollups used by the dashboard and downstream decisions

---

## Why a view for monthly metrics?
A view keeps the “gold” layer reproducible from silver without copy/duplication.

If you later need performance:
- materialize into a table
- schedule refreshes
- snapshot by month

---

## How to run the full flow

```bash
make demo      # bronze + flags
make clean     # silver
make metrics   # gold
make runs      # show run tracking
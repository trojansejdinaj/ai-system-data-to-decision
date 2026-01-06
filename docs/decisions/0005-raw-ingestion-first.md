# 0005 — Raw Ingestion Before Normalization

## Status
Accepted

## Context
The system needs to ingest external data sources that may evolve over time.
Early normalization introduces tight coupling and makes schema changes costly.

A decision was required on whether to:
- normalize data immediately on ingest, or
- persist raw data first and normalize later

## Decision
Persist all ingested records in a raw staging layer before normalization.

Each ingestion execution is tracked via an `ingest_runs` record.
Each ingested row is stored verbatim as JSON in `raw_records`.

Normalization will be introduced in a later phase.

## Rationale
- Preserves original source data for auditing and replay
- Enables schema evolution without data loss
- Simplifies ingestion logic
- Aligns with data-lake / medallion-style architectures
- Allows downstream processing to be retried independently

## Consequences
### Positive
- High flexibility
- Strong traceability
- Clear separation of concerns

### Negative
- Additional storage overhead
- Requires a later normalization step

These tradeoffs are acceptable and intentional.

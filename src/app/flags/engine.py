from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from .models import Flag, FlaggedRecord
from .rules import build_rules, fingerprint


def flag_records(
    records: Iterable[dict[str, Any]], now: datetime | None = None
) -> list[FlaggedRecord]:
    """
    Deterministic + explainable:
      - fixed rules with weights
      - severity = min(100, sum(weights))
      - stable sorting
    """
    now = now or datetime.now(UTC)
    rules = build_rules()

    recs = list(records)
    fp_counts = Counter(fingerprint(r) for r in recs)

    flagged: list[FlaggedRecord] = []
    for r in recs:
        flags: list[Flag] = []

        for rule in rules:
            f = rule(r, now)
            if f is not None:
                flags.append(f)

        fp = fingerprint(r)
        if fp_counts.get(fp, 0) > 1:
            flags.append(
                Flag(
                    code="POSSIBLE_DUPLICATE_FINGERPRINT",
                    weight=30,
                    message=f"Fingerprint appears {fp_counts[fp]} times in this batch",
                )
            )

        if flags:
            severity = min(100, sum(f.weight for f in flags))
            flagged.append(FlaggedRecord(record=r, severity=severity, flags=flags))

    flagged.sort(key=lambda fr: (-fr.severity, str(fr.record.get("id", ""))))
    return flagged

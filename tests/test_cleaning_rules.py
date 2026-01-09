from datetime import date
from decimal import Decimal

import pytest

from app.cleaning.pipeline import CleaningConfig, clean_row
from app.cleaning.rules import (
    OutlierRule,
    is_null,
    normalize_currency_to_decimal,
    normalize_date,
    normalize_text,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, True),
        ("", True),
        ("  ", True),
        ("N/A", True),
        ("null", True),
        ("None", True),
        ("something", False),
    ],
)
def test_is_null(value, expected):
    assert is_null(value) is expected


def test_normalize_text():
    assert normalize_text("  hello   world ") == "hello world"
    assert normalize_text("   ") is None


def test_normalize_date_iso():
    assert normalize_date("2026-01-09") == date(2026, 1, 9)


def test_normalize_date_ambiguous_day_first():
    assert normalize_date("01/09/2026", day_first=True) == date(2026, 9, 1)


def test_normalize_date_ambiguous_month_first():
    assert normalize_date("01/09/2026", day_first=False) == date(2026, 1, 9)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("$1,234.56", Decimal("1234.56")),
        ("€1.234,56", Decimal("1234.56")),
        ("  99 ", Decimal("99")),
        (None, None),
        ("N/A", None),
        ("abc", None),
    ],
)
def test_normalize_currency(value, expected):
    assert normalize_currency_to_decimal(value) == expected


def test_outlier_rule_sets_to_none():
    rule = OutlierRule(min_value=0, max_value=100)
    assert rule.apply(50) == 50
    assert rule.apply(-1) is None
    assert rule.apply(101) is None


def test_clean_row_end_to_end():
    cfg = CleaningConfig(
        allowed_keys={"title", "category", "published_at", "price", "views", "score"},
        day_first=True,
        category_mapping={
            "ai": "AI",
            "artificial intelligence": "AI",
            "ml": "ML",
        },
        outlier_rules={
            "views": OutlierRule(min_value=0, max_value=10_000_000),
            "score": OutlierRule(min_value=0, max_value=1),
        },
    )

    before = {
        "title": "  Hello   world ",
        "category": "Artificial Intelligence",
        "published_at": "01/09/2026",
        "price": "€1.234,56",
        "views": "-10",
        "score": "1.5",
        "ignore_me": "nope",
    }

    after = clean_row(before, cfg)

    assert after["title"] == "Hello world"
    assert after["category"] == "AI"
    assert after["published_at"] == date(2026, 9, 1)
    assert after["price"] == Decimal("1234.56")
    assert after["views"] is None  # outlier rule
    assert after["score"] is None  # outlier rule
    assert "ignore_me" not in after  # stripped by allowed_keys

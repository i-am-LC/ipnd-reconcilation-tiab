"""
Unit tests for IPND upload date aging enrichment logic.
"""

from datetime import datetime, timedelta

import pandas as pd

from main import categorize_upload_age, get_upload_age_category


def test_upload_age_categories_with_fixed_reference() -> None:
    """Test aging categorization across all predefined buckets."""
    ref = datetime(2026, 10, 8, 12, 0, 0)

    # Less than 6 months (< 182.5 days)
    assert get_upload_age_category(ref - timedelta(days=30), ref) == "< 6 Months"
    assert get_upload_age_category(ref - timedelta(days=180), ref) == "< 6 Months"

    # 6 to 12 months (182.5 to 365.25 days)
    assert get_upload_age_category(ref - timedelta(days=200), ref) == "6-12 Months"
    assert get_upload_age_category(ref - timedelta(days=360), ref) == "6-12 Months"

    # 1 to 2 years (365.25 to 730.5 days)
    assert get_upload_age_category(ref - timedelta(days=400), ref) == "1-2 Years"
    assert get_upload_age_category(ref - timedelta(days=700), ref) == "1-2 Years"

    # Greater than 2 years (>= 730.5 days)
    assert get_upload_age_category(ref - timedelta(days=750), ref) == "> 2 Years"
    assert get_upload_age_category(ref - timedelta(days=1500), ref) == "> 2 Years"


def test_upload_age_missing_and_invalid_dates() -> None:
    """Test that missing, empty, or unparseable dates result in 'No Upload Date'."""
    assert get_upload_age_category(None) == "No Upload Date"
    assert get_upload_age_category(pd.NA) == "No Upload Date"
    assert get_upload_age_category("") == "No Upload Date"
    assert get_upload_age_category("   ") == "No Upload Date"
    assert get_upload_age_category("invalid-date-string") == "No Upload Date"


def test_categorize_upload_age_series() -> None:
    """Test categorizing a pandas Series of upload dates."""
    ref = datetime(2026, 10, 8)
    series = pd.Series(
        [
            "08-Oct-2026 10:00:00",
            "08-Jan-2026 10:00:00",
            "08-Oct-2024 10:00:00",
            "08-Oct-2022 10:00:00",
            None,
        ]
    )

    result = categorize_upload_age(series, reference_date=ref)

    assert result.tolist() == [
        "< 6 Months",
        "6-12 Months",
        "1-2 Years",
        "> 2 Years",
        "No Upload Date",
    ]

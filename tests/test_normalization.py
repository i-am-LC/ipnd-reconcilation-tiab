"""
Unit tests for phone number normalization logic.
"""

import pandas as pd
import pytest

from main import clean_phone_number, normalize_number_column


def test_sip_uri_stripping() -> None:
    """Test that SIP URI domains are stripped and valid numbers preserved."""
    raw = "0263301452@tenant.ws184.connectyou.net.au"
    expected = "0263301452"
    assert clean_phone_number(raw) == expected


def test_internal_extensions_filtered_out() -> None:
    """Test that internal PBX extensions are rejected by the 10-digit regex."""
    extension_uri = "401@tenant.ws184.connectyou.net.au"
    assert clean_phone_number(extension_uri) is None

    short_ext = "401"
    assert clean_phone_number(short_ext) is None


def test_spreadsheet_float_suffix_stripping() -> None:
    """Test that spreadsheet .0 float representation is stripped."""
    assert clean_phone_number("0263301452.0") == "0263301452"
    assert clean_phone_number(263301452.0) == "0263301452"
    assert clean_phone_number("0412345678.0") == "0412345678"


def test_nine_digit_padding() -> None:
    """Test that 9-digit numbers are padded to 10 digits with a leading zero."""
    assert clean_phone_number("263301452") == "0263301452"
    assert clean_phone_number(263301452) == "0263301452"
    assert clean_phone_number(412345678) == "0412345678"


def test_whitespace_handling() -> None:
    """Test that leading and trailing whitespace is stripped."""
    assert clean_phone_number("   0358228011   ") == "0358228011"
    assert clean_phone_number(" 0412345678@domain.com ") == "0412345678"


def test_valid_australian_prefixes() -> None:
    """Test all valid Australian geographic and mobile prefixes."""
    assert clean_phone_number("0298765432") == "0298765432"  # NSW/ACT
    assert clean_phone_number("0398765432") == "0398765432"  # VIC/TAS
    assert clean_phone_number("0412345678") == "0412345678"  # Mobile
    assert clean_phone_number("0731234567") == "0731234567"  # QLD
    assert clean_phone_number("0881234567") == "0881234567"  # WA/SA/NT


def test_invalid_numbers_rejected() -> None:
    """Test that invalid numbers, special numbers, and non-numerics return None."""
    assert clean_phone_number(None) is None
    assert clean_phone_number("") is None
    assert clean_phone_number("   ") is None
    assert clean_phone_number("1300882961") is None  # 1300 special service
    assert clean_phone_number("1800123456") is None  # 1800 special service
    assert clean_phone_number("0512345678") is None  # Invalid prefix 05
    assert clean_phone_number("Rental Yealink T53") is None
    assert clean_phone_number("393209-TBA-5f9b6944-630e") is None


def test_normalize_number_column_dataframe() -> None:
    """Test DataFrame normalization filters invalid rows and cleans valid ones."""
    df = pd.DataFrame(
        {
            "Service Number": [
                "0263301452@tenant.ws184.connectyou.net.au",
                "401@tenant.ws184.connectyou.net.au",
                "263301452.0",
                "1300882961",
                " 0412345678 ",
            ],
            "Customer": ["Cust A", "Cust B", "Cust C", "Cust D", "Cust E"],
        }
    )

    result = normalize_number_column(df, "Service Number")

    assert len(result) == 3
    assert list(result["Service Number"]) == [
        "0263301452",
        "0263301452",
        "0412345678",
    ]
    assert list(result["Customer"]) == ["Cust A", "Cust C", "Cust E"]


def test_normalize_number_column_series() -> None:
    """Test Series normalization produces cleaned values or None for invalid."""
    series = pd.Series(
        [
            "0263301452@tenant.ws184.connectyou.net.au",
            "401@tenant.ws184.connectyou.net.au",
            "0412345678",
        ]
    )

    result = normalize_number_column(series)

    assert result.tolist() == ["0263301452", None, "0412345678"]


def test_normalize_number_column_missing_column_error() -> None:
    """Test ValueError is raised when DataFrame is passed without column name."""
    df = pd.DataFrame({"Number": ["0412345678"]})
    with pytest.raises(ValueError):
        normalize_number_column(df)

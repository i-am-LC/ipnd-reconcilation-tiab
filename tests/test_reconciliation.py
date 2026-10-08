"""
Unit tests for core reconciliation processing and category assignments.
"""

import pandas as pd

from main import process_reconciliation


def test_category_4_excludes_disconnected_services() -> None:
    """
    Test Category 4 excludes numbers in both active and disconnected reports.

    INC0043773 fix: Numbers appearing in the disconnected services report
    must not be reported as 'IPND Connected not in CSP'.
    """
    # Active services: contains 0263301410
    active_df = pd.DataFrame(
        {
            "Service ID": ["CP"],
            "Service Number": ["0263301410"],
            "Customer": ["Cust Active"],
        }
    )

    # Disconnected services: contains 0263301420
    discon_df = pd.DataFrame(
        {
            "Phone Number": ["0263301420"],
            "Customer Number": ["Cust Discon"],
        }
    )

    # IPND: contains active (0263301410), discon (0263301420), and missing (0263301430)
    ipnd_df = pd.DataFrame(
        {
            "Public Number": ["0263301410", "0263301420", "0263301430"],
            "Service Status Code": ["C", "C", "C"],
            "Terminated Date": [None, None, None],
            "IPND Last Upload Date": [
                "01-Jan-2026 10:00:00",
                "01-Jan-2025 10:00:00",
                "01-Jan-2024 10:00:00",
            ],
        }
    )

    results = process_reconciliation(active_df, discon_df, ipnd_df)
    cat4_df = results["4. IPND Connected not in CSP"]

    # 0263301410 is active -> excluded
    # 0263301420 is disconnected -> MUST be excluded
    # 0263301430 is not in CSP -> MUST be present
    assert "0263301410" not in list(cat4_df["Public Number"])
    assert "0263301420" not in list(cat4_df["Public Number"])
    assert "0263301430" in list(cat4_df["Public Number"])
    assert len(cat4_df) == 1


def test_category_4_and_5_upload_age_enrichment() -> None:
    """Test that Tab 4 and Tab 5 output DataFrames contain Upload Age Category."""
    active_df = pd.DataFrame(columns=["Service ID", "Service Number"])
    discon_df = pd.DataFrame(columns=["Phone Number"])

    ipnd_df = pd.DataFrame(
        {
            "Public Number": ["0263301410", "0263301420"],
            # 0263301410 is connected (for Cat 4)
            # 0263301420 is a conflict (status C but has Terminated Date) (for Cat 5)
            "Service Status Code": ["C", "C"],
            "Terminated Date": [None, "01-Jan-2026 12:00:00"],
            "IPND Last Upload Date": ["01-Jan-2026 10:00:00", None],
        }
    )

    results = process_reconciliation(active_df, discon_df, ipnd_df)

    cat4_df = results["4. IPND Connected not in CSP"]
    cat5_df = results["5. IPND Conflicts"]

    assert "Upload Age Category" in cat4_df.columns
    assert "Upload Age Category" in cat5_df.columns
    assert list(cat4_df["Upload Age Category"]) != []
    assert cat5_df["Upload Age Category"].iloc[0] == "No Upload Date"


def test_category_1_deduplication() -> None:
    """
    Test Category 1 deduplicates duplicate active entries for the same number,
    preserving customer details.
    """
    active_df = pd.DataFrame(
        {
            "Service ID": ["T2", "T2"],
            "Service Number": ["0358228011", "0358228011"],
            "Customer Name": ["David Lannen", "David Lannen Secondary"],
        }
    )
    discon_df = pd.DataFrame(columns=["Phone Number"])
    ipnd_df = pd.DataFrame(
        columns=[
            "Public Number",
            "Service Status Code",
            "Terminated Date",
            "IPND Last Upload Date",
        ]
    )

    results = process_reconciliation(active_df, discon_df, ipnd_df)
    cat1_df = results["1. Active not in IPND"]

    # Must be deduplicated to 1 record, preserving first customer name
    assert len(cat1_df) == 1
    assert cat1_df["Service Number"].iloc[0] == "0358228011"
    assert cat1_df["Customer Name"].iloc[0] == "David Lannen"


def test_active_with_ipnd_disconnected_and_conflict_handling() -> None:
    """
    Test ACMA IGN 019 reconciliation rules:
    1. Active number with IPND Status == 'D' and null Terminated Date is placed
       in Category 2 ('Active but IPND Disconnected') and NOT in Category 1.
    2. Number in active services absent from IPND is placed in Category 1.
    3. Category 5 captures Status == 'C' with Terminated Date as diagnostic audit
       without corrupting Category 1/2 outputs.
    """
    active_df = pd.DataFrame(
        {
            "Service ID": ["CP", "CP"],
            "Service Number": ["0383610742", "0299990001"],
            "Customer": ["Jason Thomas", "New Active Cust"],
        }
    )
    discon_df = pd.DataFrame(columns=["Phone Number"])
    ipnd_df = pd.DataFrame(
        {
            "Public Number": ["0383610742", "0288880002"],
            "Service Status Code": ["D", "C"],
            "Terminated Date": [None, "01-Jan-2026 10:00:00"],
            "IPND Last Upload Date": [
                "23-Jun-2026 14:20:41",
                "01-Jan-2026 09:00:00",
            ],
        }
    )

    results = process_reconciliation(active_df, discon_df, ipnd_df)

    cat1_df = results["1. Active not in IPND"]
    cat2_df = results["2. Active but IPND Disconnected"]
    cat5_df = results["5. IPND Conflicts"]

    # 0383610742 is active and IPND disconnected -> in Cat 2, NOT in Cat 1 or Cat 5
    assert "0383610742" in list(cat2_df["Service Number"])
    assert "0383610742" not in list(cat1_df["Service Number"])
    assert "0383610742" not in list(cat5_df["Public Number"])

    # 0299990001 is not in IPND at all -> in Cat 1, NOT in Cat 2
    assert "0299990001" in list(cat1_df["Service Number"])
    assert "0299990001" not in list(cat2_df["Service Number"])

    # 0288880002 is Status C with Terminated Date -> in Cat 5 conflict audit sheet
    assert "0288880002" in list(cat5_df["Public Number"])
